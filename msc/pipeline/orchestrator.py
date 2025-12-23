"""Pipeline orchestrator for coordinating multi-stage execution.

Coordinates execution of multiple pipeline stages with observer pattern
for progress tracking and error handling.
"""

# Standard library
from datetime import datetime
from pathlib import Path
from typing import Any

# Local
from msc.analysis.scorer import PowerRankingScorer
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.config.settings import get_settings
from msc.models.ranking import PowerRankingResults
from msc.pipeline.enrich import EnrichmentStage
from msc.pipeline.extract import ExtractionStage
from msc.pipeline.observer import EventType, Observable, PipelineObserver
from msc.pipeline.observers import (
    ConsoleObserver,
    FileObserver,
    MetricsObserver,
    ProgressBarObserver,
)
from msc.pipeline.rank import RankingStage
from msc.storage.checkpoint import CheckpointManager, ManualReviewQueue
from msc.storage.json_repository import JSONStatsRepository, JSONTrackRepository
from msc.utils.logging import get_logger


class PipelineOrchestrator(Observable):
    """Orchestrates the full music-charts pipeline.

    Coordinates execution of all pipeline stages:
    1. Extraction: MusicBee → Songstats ID resolution
    2. Enrichment: Fetch platform statistics
    3. Ranking: Compute power rankings

    Uses Observer pattern for progress tracking and error handling.
    """

    def __init__(
            self,
            data_dir: Path | None = None,
            checkpoint_dir: Path | None = None,
            include_youtube: bool = True,
            verbose: bool = False,
            run_id: str | None = None,
            new_run: bool = False,
    ) -> None:
        """Initialize pipeline orchestrator.

        Args:
            data_dir: Directory for data files (default: from settings)
            checkpoint_dir: Directory for checkpoints (default: run_dir / "checkpoints")
            include_youtube: Whether to fetch YouTube data
            verbose: Enable verbose logging
            run_id: Unique identifier for this run (default: auto-detect latest or create new)
            new_run: If True, force creation of new run directory instead of resuming latest
        """
        super().__init__()
        self.settings = get_settings()
        self.logger = get_logger(__name__)

        # Setup directories
        if data_dir is None:
            data_dir = self.settings.data_dir

        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Determine run ID and run directory
        if run_id is None:
            if new_run:
                # Force new run
                run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                self.logger.info("Creating new run: %s", run_id)

            else:
                # Try to find latest run for this year
                latest_run = self._find_latest_run(self.settings.year)

                if latest_run:
                    run_id = latest_run
                    self.logger.info("Resuming latest run: %s", run_id)

                else:
                    # No existing runs, create new
                    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.logger.info("No existing runs found, creating new: %s", run_id)

        self.run_id = run_id
        self.run_dir = self.data_dir / "runs" / f"{self.settings.year}_{self.run_id}"
        self.run_dir.mkdir(parents=True, exist_ok=True)

        # Checkpoints are now per-run (stored in run directory)
        if checkpoint_dir is None:
            checkpoint_dir = self.run_dir / "checkpoints"

        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.include_youtube = include_youtube
        self.verbose = verbose

        # Initialize clients
        self.musicbee = MusicBeeClient(self.settings.musicbee_library)
        self.songstats = SongstatsClient(
            api_key=self.settings.songstats_api_key,
            rate_limit=self.settings.songstats_rate_limit,
        )

        # Initialize repositories
        # Tracks repository now in run directory
        self.track_repository = JSONTrackRepository(
            self.run_dir / "tracks.json"
        )
        self.stats_repository = JSONStatsRepository(
            self.data_dir / "output" / "enriched_tracks.json"
        )

        # Initialize checkpoint and review queue
        self.checkpoint_mgr = CheckpointManager(self.checkpoint_dir)
        # Manual review queue now in run directory
        self.review_queue = ManualReviewQueue(self.run_dir / "manual_review.json")

        # Initialize scorer
        self.scorer = PowerRankingScorer()

        # Initialize stages (will be set up in run())
        self.extraction_stage: ExtractionStage | None = None
        self.enrichment_stage: EnrichmentStage | None = None
        self.ranking_stage: RankingStage | None = None

        # Attach default observers
        self._setup_observers()

    def _find_latest_run(self, year: int) -> str | None:
        """Find the most recent run directory for the given year.

        Args:
            year: Year to search for

        Returns:
            Run ID (timestamp portion) of the latest run, or None if no runs exist
        """
        runs_dir = self.data_dir / "runs"
        if not runs_dir.exists():
            return None

        # Find all run directories matching the year pattern
        year_prefix = f"{year}_"
        matching_runs = []

        try:
            for run_dir in runs_dir.iterdir():
                if run_dir.is_dir() and run_dir.name.startswith(year_prefix):
                    # Extract run_id (timestamp portion after year_)
                    run_id = run_dir.name[len(year_prefix):]
                    matching_runs.append(run_id)

        except OSError as error:
            self.logger.warning("Failed to scan runs directory: %s", error)
            return None

        if not matching_runs:
            return None

        # Sort by timestamp (run_id format: YYYYMMDD_HHMMSS)
        # Most recent will be last
        matching_runs.sort()
        latest_run_id = matching_runs[-1]

        self.logger.debug("Found %d existing runs for year %d, latest: %s",
                          len(matching_runs), year, latest_run_id)

        return latest_run_id

    def _setup_observers(self) -> None:
        """Setup default observers for pipeline monitoring."""
        # Console observer
        console_observer = ConsoleObserver(verbose=self.verbose)
        self.attach(console_observer)

        # File observer for event log (in logs directory)
        log_dir = self.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"pipeline_events_{self.run_id}.jsonl"
        file_observer = FileObserver(log_file)
        self.attach(file_observer)

        # Progress bar observer
        progress_observer = ProgressBarObserver()
        self.attach(progress_observer)

        # Metrics observer
        self.metrics_observer = MetricsObserver()
        self.attach(self.metrics_observer)

    def add_observer(self, observer: PipelineObserver) -> None:
        """Add a custom observer to the pipeline.

        Args:
            observer: Observer to add
        """
        self.attach(observer)

    def run(
            self,
            run_extraction: bool = True,
            run_enrichment: bool = True,
            run_ranking: bool = True,
            playlist_name: str | None = None,
    ) -> PowerRankingResults | None:
        """Run the full pipeline or selected stages.

        Args:
            run_extraction: Whether to run extraction stage
            run_enrichment: Whether to run enrichment stage
            run_ranking: Whether to run ranking stage
            playlist_name: Name of playlist to extract (default: from settings)

        Returns:
            PowerRankingResults if ranking stage was run, None otherwise
        """
        # Notify pipeline started
        event = self.create_event(
            EventType.PIPELINE_STARTED,
            message=f"Starting music-charts pipeline (year: {self.settings.year})",
            metadata={
                "extraction": run_extraction,
                "enrichment": run_enrichment,
                "ranking": run_ranking,
                "include_youtube": self.include_youtube,
                "run_id": self.run_id,
                "run_dir": str(self.run_dir),
            },
        )
        self.notify(event)

        # Log run information
        self.logger.info("Run ID: %s", self.run_id)
        self.logger.info("Run directory: %s", self.run_dir)

        try:
            results: PowerRankingResults | None = None
            extracted_tracks = []
            enriched_tracks = []

            # Stage 1: Extraction
            if run_extraction:
                self.logger.info("Running extraction stage")
                self.extraction_stage = ExtractionStage(
                    musicbee_client=self.musicbee,
                    songstats_client=self.songstats,
                    track_repository=self.track_repository,
                    checkpoint_manager=self.checkpoint_mgr,
                    review_queue=self.review_queue,
                    playlist_name=playlist_name,
                )

                # Attach all pipeline observers to stage
                for observer in self._observers:
                    self.extraction_stage.attach(observer)

                # Run extraction stage
                extracted_tracks = self.extraction_stage.run()
                self.logger.info("Extraction stage completed: %d tracks", len(extracted_tracks))

            # Stage 2: Enrichment
            if run_enrichment:
                self.logger.info("Running enrichment stage")

                # Get tracks from repository if extraction was skipped
                if not run_extraction:
                    extracted_tracks = self.track_repository.get_all()
                    self.logger.info("Loaded %d tracks from repository", len(extracted_tracks))

                self.enrichment_stage = EnrichmentStage(
                    songstats_client=self.songstats,
                    stats_repository=self.stats_repository,
                    checkpoint_manager=self.checkpoint_mgr,
                    include_youtube=self.include_youtube,
                    track_repository=self.track_repository,
                )

                # Attach all pipeline observers to stage
                for observer in self._observers:
                    self.enrichment_stage.attach(observer)

                # Run enrichment stage
                enriched_tracks = self.enrichment_stage.transform(extracted_tracks)
                self.enrichment_stage.load(enriched_tracks)
                self.logger.info("Enrichment stage completed: %d tracks", len(enriched_tracks))

            # Stage 3: Ranking
            if run_ranking:
                self.logger.info("Running ranking stage")

                # Get enriched tracks from repository if enrichment was skipped
                if not run_enrichment:
                    enriched_tracks = self.stats_repository.get_all()
                    self.logger.info("Loaded %d enriched tracks from repository", len(enriched_tracks))

                self.ranking_stage = RankingStage(
                    scorer=self.scorer,
                    output_dir=self.settings.output_dir,
                    stats_repository=self.stats_repository,
                )

                # Attach all pipeline observers to stage
                for observer in self._observers:
                    self.ranking_stage.attach(observer)

                # Run ranking stage
                results = self.ranking_stage.transform(enriched_tracks)
                self.ranking_stage.load(results)
                self.logger.info("Ranking stage completed: %d rankings", len(results.rankings))

            # Notify pipeline completed
            metrics = self.metrics_observer.get_metrics()
            event = self.create_event(
                EventType.PIPELINE_COMPLETED,
                message="Pipeline completed successfully",
                metadata={
                    "stages_completed": metrics.get("stages_completed", 0),
                    "items_processed": metrics.get("items_processed", 0),
                    "items_failed": metrics.get("items_failed", 0),
                    "success_rate": self.metrics_observer.get_success_rate(),
                },
            )

            self.notify(event)
            self.logger.info("Pipeline completed successfully")

            return results

        except Exception as error:
            self.logger.exception("Pipeline failed")

            # Notify pipeline failed
            event = self.create_event(
                EventType.PIPELINE_FAILED,
                message=f"Pipeline failed: {error!s}",
                error=error,
            )

            self.notify(event)
            raise

    def get_metrics(self) -> dict[str, Any]:
        """Get pipeline execution metrics.

        Returns:
            Dictionary of metrics
        """
        return self.metrics_observer.get_metrics()

    def get_review_queue(self) -> list[Any]:
        """Get items in manual review queue.

        Returns:
            List of items needing manual review
        """
        return self.review_queue.get_all()

    def clear_checkpoints(self) -> None:
        """Clear all checkpoint files."""
        self.checkpoint_mgr.clear_checkpoint("extraction")
        self.checkpoint_mgr.clear_checkpoint("enrichment")
        self.logger.info("Cleared all checkpoints")

    def reset_pipeline(self) -> None:
        """Reset the entire pipeline (clear checkpoints, repositories, review queue).

        WARNING: This will delete all processed data and start from scratch.
        """
        # Clear checkpoints
        self.clear_checkpoints()

        # Clear repositories
        self.track_repository.clear()
        self.stats_repository.clear()

        # Clear review queue
        self.review_queue.clear()
        self.logger.warning("Pipeline reset: all data cleared")
