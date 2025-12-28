"""Ranking stage: Compute power rankings from enriched tracks.

Computes power rankings using the PowerRankingScorer and exports
results to multiple formats (JSON, CSV, merged files).
"""

# Standard library
from pathlib import Path

# Local
from msc.analysis.scorer import PowerRankingScorer
from msc.config.settings import get_settings
from msc.models.ranking import PowerRankingResults
from msc.models.stats import TrackWithStats
from msc.pipeline.base import PipelineStage
from msc.pipeline.observer import EventType, Observable
from msc.storage.json_repository import JSONStatsRepository
from msc.utils.logging import get_logger
from msc.utils.path_utils import secure_write


class RankingStage(PipelineStage[list[TrackWithStats], PowerRankingResults], Observable):
    """Ranking pipeline stage.

    Responsibilities:
    1. Compute power rankings using PowerRankingScorer
    2. Export results to JSON (nested and flat formats)
    3. Export results to CSV
    4. Create merged output file with all track data
    """

    def __init__(
            self,
            scorer: PowerRankingScorer,
            output_dir: Path | None = None,
            stats_repository: JSONStatsRepository | None = None,
    ) -> None:
        """Initialize ranking stage.

        Args:
            scorer: PowerRankingScorer instance
            output_dir: Directory for output files (default: from settings)
            stats_repository: Optional repository for loading input tracks (enables standalone execution)
        """
        Observable.__init__(self)
        self.scorer = scorer
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.stats_repository = stats_repository

        # Determine output directory
        if output_dir is None:
            output_dir = self.settings.output_dir

        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @property
    def stage_name(self) -> str:
        """Human-readable name for this pipeline stage."""
        return "Ranking"

    def extract(self) -> list[TrackWithStats]:
        """Extract enriched tracks from repository for standalone execution.

        Returns:
            List of enriched tracks from repository, or empty list if no repository provided
        """
        if self.stats_repository:
            tracks = self.stats_repository.get_all()
            self.logger.info("Loaded %d enriched tracks from repository", len(tracks))
            return tracks

        self.logger.debug("No stats repository provided, returning empty list")
        return []

    def transform(self, data: list[TrackWithStats]) -> PowerRankingResults:
        """Transform enriched tracks into power rankings.

        Args:
            data: Tracks with platform statistics

        Returns:
            PowerRankingResults with ranked tracks
        """
        if not data:
            self.logger.warning("No tracks to rank")
            return PowerRankingResults(rankings=[], year=self.settings.year)

        # Notify stage started
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Ranking",
            message=f"Computing power rankings for {len(data)} tracks",
        )
        self.notify(event)

        try:
            # Compute rankings using scorer
            results = self.scorer.compute_rankings(data)

            # Notify stage completed
            event = self.create_event(
                EventType.STAGE_COMPLETED,
                stage_name="Ranking",
                message=f"Computed {len(results.rankings)} rankings",
                metadata={
                    "total_tracks": results.total_tracks,
                    "top_track": (
                        f"{results.rankings[0].artist_display} - {results.rankings[0].track.title}"
                        if results.rankings
                        else "N/A"
                    ),
                    "top_score": (
                        results.rankings[0].total_score if results.rankings else 0.0
                    ),
                },
            )
            self.notify(event)

            self.logger.info(
                "Computed %d rankings, top: %s - %s (%.2f)",
                len(results.rankings),
                results.rankings[0].artist_display if results.rankings else "N/A",
                results.rankings[0].track.title if results.rankings else "N/A",
                results.rankings[0].total_score if results.rankings else 0.0,
            )

            return results

        except Exception as error:
            self.logger.exception("Failed to compute rankings")

            event = self.create_event(
                EventType.STAGE_FAILED,
                stage_name="Ranking",
                message=f"Ranking failed: {error!s}",
                error=error,
            )
            self.notify(event)
            raise

    def load(self, data: PowerRankingResults) -> None:
        """Export power rankings to multiple file formats.

        Args:
            data: PowerRankingResults to export
        """
        # Notify stage started
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Ranking",
            message="Exporting rankings to files",
        )
        self.notify(event)

        try:
            year = self.settings.year

            # 1. Export rankings to JSON (nested format)
            rankings_json_path = self.output_dir / f"power_rankings_{year}.json"
            self._export_rankings_json(data, rankings_json_path)

            # 2. Export rankings to CSV
            rankings_csv_path = self.output_dir / f"power_rankings_{year}.csv"
            self._export_rankings_csv(data, rankings_csv_path)

            # 3. Export flat rankings (legacy format)
            rankings_flat_path = self.output_dir / f"power_rankings_{year}_flat.json"
            self._export_rankings_flat(data, rankings_flat_path)

            self.logger.info("Exported rankings to %s", self.output_dir)

            # Notify checkpoint saved
            event = self.create_event(
                EventType.CHECKPOINT_SAVED,
                stage_name="Ranking",
                message=f"Rankings exported to {self.output_dir}",
                metadata={
                    "files": [
                        rankings_json_path.name,
                        rankings_csv_path.name,
                        rankings_flat_path.name,
                    ]
                },
            )
            self.notify(event)

        except Exception as error:
            self.logger.exception("Failed to export rankings")

            event = self.create_event(
                EventType.ERROR,
                stage_name="Ranking",
                message=f"Export failed: {error!s}",
                error=error,
            )
            self.notify(event)
            raise

    def _export_rankings_json(
            self, results: PowerRankingResults, file_path: Path
    ) -> None:
        """Export rankings to JSON file (nested format).

        Args:
            results: PowerRankingResults to export
            file_path: Path to output file
        """
        import json

        try:
            data = results.model_dump(mode="json", by_alias=True)

            with secure_write(
                    file_path,
                    base_dir=self.output_dir,
                    purpose="rankings JSON export",
                    encoding="utf-8",
            ) as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info("Exported rankings to JSON: %s", file_path)

        except (OSError, TypeError, ValueError) as error:
            self.logger.exception("Failed to export rankings to JSON: %s", error)

    def _export_rankings_csv(
            self, results: PowerRankingResults, file_path: Path
    ) -> None:
        """Export rankings to CSV file.

        Args:
            results: PowerRankingResults to export
            file_path: Path to output file
        """
        import csv

        try:
            with secure_write(
                    file_path,
                    base_dir=self.output_dir,
                    purpose="rankings CSV export",
                    newline="",
                    encoding="utf-8",
            ) as f:
                if not results.rankings:
                    return

                # Flatten ranking data for CSV
                fieldnames = [
                    "rank",
                    "artist",
                    "title",
                    "track_id",
                    "total_score",
                ]

                # Add category score columns
                first_ranking = results.rankings[0]
                for score in first_ranking.category_scores:
                    fieldnames.extend(
                        [
                            f"{score.category}_raw_score",
                            f"{score.category}_weighted_score",
                            f"{score.category}_weight",
                        ]
                    )

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for ranking in results.rankings:
                    row = {
                        "rank": ranking.rank,
                        "artist": ranking.artist_display,
                        "title": ranking.track.title,
                        "track_id": ranking.track.identifier,
                        "total_score": ranking.total_score,
                    }

                    # Add category scores
                    for score in ranking.category_scores:
                        row[f"{score.category}_raw_score"] = score.raw_score
                        row[f"{score.category}_weighted_score"] = score.weighted_score
                        row[f"{score.category}_weight"] = score.weight

                    writer.writerow(row)

            self.logger.info("Exported rankings to CSV: %s", file_path)

        except (OSError, csv.Error, AttributeError, KeyError, ValueError) as error:
            self.logger.exception("Failed to export rankings to CSV: %s", error)

    def _export_rankings_flat(
            self, results: PowerRankingResults, file_path: Path
    ) -> None:
        """Export rankings to JSON file (flat/legacy format).

        Args:
            results: PowerRankingResults to export
            file_path: Path to output file
        """
        import json

        try:
            # Convert to flat format for backward compatibility
            flat_data = []

            for ranking in results.rankings:
                flat_row = {
                    "rank": ranking.rank,
                    "track_id": ranking.track.identifier,
                    "artist": ranking.artist_display,
                    "title": ranking.track.title,
                    "total_score": ranking.total_score,
                }

                # Flatten category scores
                for score in ranking.category_scores:
                    flat_row[f"{score.category}_raw_score"] = score.raw_score
                    flat_row[f"{score.category}_weighted_score"] = score.weighted_score
                    flat_row[f"{score.category}_weight"] = score.weight

                flat_data.append(flat_row)

            with secure_write(
                    file_path,
                    base_dir=self.output_dir,
                    purpose="flat rankings export",
                    encoding="utf-8",
            ) as f:
                json.dump(flat_data, f, indent=2, ensure_ascii=False)

            self.logger.info("Exported flat rankings to JSON: %s", file_path)

        except (OSError, TypeError, AttributeError, KeyError, ValueError) as error:
            self.logger.exception("Failed to export flat rankings: %s", error)
