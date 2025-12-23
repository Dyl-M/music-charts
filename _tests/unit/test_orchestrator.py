"""Tests for pipeline orchestrator.

Tests the PipelineOrchestrator class which coordinates execution of all
pipeline stages with observer pattern for progress tracking.
"""

# Standard library
from pathlib import Path
from unittest.mock import Mock, patch

# Third-party
import pytest

# Local
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track
from msc.pipeline.observer import PipelineObserver
from msc.pipeline.orchestrator import PipelineOrchestrator


class TestPipelineOrchestratorInit:
    """Tests for PipelineOrchestrator initialization."""

    @staticmethod
    def test_init_with_defaults(tmp_path: Path) -> None:
        """Test orchestrator initializes with default settings."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient") as mock_mb,
            patch("msc.pipeline.orchestrator.SongstatsClient") as mock_ss,
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            assert orchestrator.data_dir == tmp_path
            # Checkpoints are now per-run (in run directory)
            assert orchestrator.checkpoint_dir == orchestrator.run_dir / "checkpoints"
            assert orchestrator.checkpoint_dir.exists()
            assert orchestrator.include_youtube is True
            assert orchestrator.verbose is False
            assert orchestrator.run_id is not None
            assert orchestrator.run_dir.exists()

            # Check clients were initialized
            mock_mb.assert_called_once()
            mock_ss.assert_called_once()

    @staticmethod
    def test_init_with_custom_checkpoint_dir(tmp_path: Path) -> None:
        """Test orchestrator with custom checkpoint directory."""
        checkpoint_dir = tmp_path / "custom_checkpoints"

        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path, checkpoint_dir=checkpoint_dir
            )

            assert orchestrator.checkpoint_dir == checkpoint_dir

    @staticmethod
    def test_init_creates_directories(tmp_path: Path) -> None:
        """Test orchestrator creates required directories."""
        data_dir = tmp_path / "data"
        checkpoint_dir = tmp_path / "checkpoints"

        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            PipelineOrchestrator(data_dir=data_dir, checkpoint_dir=checkpoint_dir)

            assert data_dir.exists()
            assert checkpoint_dir.exists()

    @staticmethod
    def test_init_with_no_data_dir_uses_settings_default() -> None:
        """Test orchestrator uses settings default when data_dir is None."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator()  # No data_dir provided

            # Should use data_dir from settings
            assert orchestrator.data_dir is not None
            assert orchestrator.data_dir == orchestrator.settings.data_dir

    @staticmethod
    def test_init_attaches_default_observers(tmp_path: Path) -> None:
        """Test orchestrator attaches default observers."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Should have 4 default observers
            assert len(orchestrator._observers) == 4

    @staticmethod
    def test_find_latest_run_returns_none_when_no_runs_exist(tmp_path: Path) -> None:
        """Test _find_latest_run returns None when no runs exist."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path, new_run=True)

            # Clear the run directory that was just created
            import shutil
            runs_dir = tmp_path / "runs"
            if runs_dir.exists():
                shutil.rmtree(runs_dir)

            result = orchestrator._find_latest_run(2025)
            assert result is None

    @staticmethod
    def test_find_latest_run_finds_most_recent(tmp_path: Path) -> None:
        """Test _find_latest_run finds the most recent run for a year."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            # Create test run directories manually FIRST
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)

            (runs_dir / "2025_20251201_120000").mkdir()
            (runs_dir / "2025_20251215_140000").mkdir()
            (runs_dir / "2025_20251220_160000").mkdir()  # Latest
            (runs_dir / "2024_20241231_235959").mkdir()  # Different year

            # Create orchestrator with new_run=False (should find latest)
            # This will automatically resume from the latest run
            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=False,
            )

            # The orchestrator should have resumed from the latest run
            assert orchestrator.run_id == "20251220_160000"

    @staticmethod
    def test_init_resumes_latest_run_by_default(tmp_path: Path) -> None:
        """Test orchestrator resumes from latest run by default."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            # Create existing run directory
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            existing_run = "20251220_120000"
            (runs_dir / f"2025_{existing_run}").mkdir()

            # Initialize without new_run flag (default: resume)
            orchestrator = PipelineOrchestrator(data_dir=tmp_path, new_run=False)

            # Should resume from existing run
            assert orchestrator.run_id == existing_run
            assert orchestrator.run_dir == runs_dir / f"2025_{existing_run}"

    @staticmethod
    def test_init_creates_new_run_with_new_run_flag(tmp_path: Path) -> None:
        """Test orchestrator creates new run when new_run=True."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            # Create existing run directory
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            existing_run = "20251220_120000"
            (runs_dir / f"2025_{existing_run}").mkdir()

            # Initialize with new_run flag
            orchestrator = PipelineOrchestrator(data_dir=tmp_path, new_run=True)

            # Should create new run (different from existing)
            assert orchestrator.run_id != existing_run
            assert orchestrator.run_dir != runs_dir / f"2025_{existing_run}"

    @staticmethod
    def test_init_creates_new_run_when_none_exist(tmp_path: Path) -> None:
        """Test orchestrator creates new run when no runs exist."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            # No existing runs
            orchestrator = PipelineOrchestrator(data_dir=tmp_path, new_run=False)

            # Should create new run
            assert orchestrator.run_id is not None
            assert orchestrator.run_dir.exists()
            assert orchestrator.run_dir.name.startswith("2025_")


class TestPipelineOrchestratorRun:
    """Tests for PipelineOrchestrator run method."""

    @staticmethod
    def test_run_all_stages(tmp_path: Path) -> None:
        """Test running all pipeline stages."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract,
            patch("msc.pipeline.orchestrator.EnrichmentStage") as mock_enrich,
            patch("msc.pipeline.orchestrator.RankingStage") as mock_rank,
        ):
            # Setup mock tracks and results
            mock_tracks = [
                Track(title="Track 1", artist_list=["Artist 1"], year=2024)
            ]
            mock_stats = [
                TrackWithStats(
                    track=mock_tracks[0],
                    songstats_identifiers=SongstatsIdentifiers(
                        songstats_id="123", songstats_title="Track 1"
                    ),
                    platform_stats=PlatformStats(),
                )
            ]
            mock_ranking_results = PowerRankingResults(
                year=2024,
                rankings=[
                    PowerRanking(
                        rank=1,
                        track=mock_tracks[0],
                        category_scores=[
                            CategoryScore(
                                category="popularity",
                                raw_score=0.8,
                                weight=4,
                                weighted_score=3.2,
                                raw_metrics={"spotify_popularity_peak": 80},
                            )
                        ],
                        total_score=3.2,
                    )
                ],
                total_tracks=1,
            )

            # Setup stage mocks
            mock_extract_instance = mock_extract.return_value
            mock_extract_instance.run.return_value = mock_tracks

            mock_enrich_instance = mock_enrich.return_value
            mock_enrich_instance.transform.return_value = mock_stats
            mock_enrich_instance.load.return_value = None

            mock_rank_instance = mock_rank.return_value
            mock_rank_instance.transform.return_value = mock_ranking_results
            mock_rank_instance.load.return_value = None

            # Run pipeline
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)
            result = orchestrator.run()

            # Verify stages were called
            assert mock_extract_instance.run.called
            assert mock_enrich_instance.transform.called
            assert mock_rank_instance.transform.called

            # Verify result
            assert result is not None
            assert len(result.rankings) == 1

    @staticmethod
    def test_run_extraction_only(tmp_path: Path) -> None:
        """Test running extraction stage only."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract,
        ):
            mock_tracks = [
                Track(title="Track 1", artist_list=["Artist 1"], year=2024)
            ]
            mock_extract.return_value.run.return_value = mock_tracks

            orchestrator = PipelineOrchestrator(data_dir=tmp_path)
            result = orchestrator.run(
                run_extraction=True, run_enrichment=False, run_ranking=False
            )

            assert result is None  # No ranking results
            assert mock_extract.return_value.run.called

    @staticmethod
    def test_run_skips_extraction_loads_from_repository(tmp_path: Path) -> None:
        """Test skipping extraction loads tracks from repository."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.EnrichmentStage") as mock_enrich,
        ):
            mock_stats = [
                TrackWithStats(
                    track=Track(title="Track 1", artist_list=["Artist 1"], year=2024),
                    songstats_identifiers=SongstatsIdentifiers(
                        songstats_id="123", songstats_title="Track 1"
                    ),
                    platform_stats=PlatformStats(),
                )
            ]
            mock_enrich_instance = mock_enrich.return_value
            mock_enrich_instance.transform.return_value = mock_stats

            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Add tracks to repository
            track = Track(title="Track 1", artist_list=["Artist 1"], year=2024)
            orchestrator.track_repository.add(track)

            # Run without extraction
            orchestrator.run(
                run_extraction=False, run_enrichment=True, run_ranking=False
            )

            # Verify enrichment was called with tracks from repository
            assert mock_enrich_instance.transform.called
            call_args = mock_enrich_instance.transform.call_args[0][0]
            assert len(call_args) == 1

    @staticmethod
    def test_run_ranking_only_loads_from_repository(tmp_path: Path) -> None:
        """Test running ranking only loads enriched tracks from repository."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.RankingStage") as mock_rank,
        ):
            mock_ranking_results = PowerRankingResults(
                year=2024,
                rankings=[
                    PowerRanking(
                        rank=1,
                        track=Track(title="Track 1", artist_list=["Artist 1"], year=2024),
                        category_scores=[
                            CategoryScore(
                                category="streams",
                                raw_score=0.9,
                                weight=4,
                                weighted_score=3.6,
                            )
                        ],
                        total_score=10.0,
                    )
                ],
                total_tracks=1,
            )
            mock_rank_instance = mock_rank.return_value
            mock_rank_instance.transform.return_value = mock_ranking_results

            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Add enriched tracks to stats repository
            stats = TrackWithStats(
                track=Track(title="Track 1", artist_list=["Artist 1"], year=2024),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id="123", songstats_title="Track 1"
                ),
                platform_stats=PlatformStats(),
            )
            orchestrator.stats_repository.add(stats)

            # Run ranking only (skip extraction and enrichment) - should load from repository
            result = orchestrator.run(
                run_extraction=False, run_enrichment=False, run_ranking=True
            )

            # Verify ranking was called with tracks from repository
            assert mock_rank_instance.transform.called
            call_args = mock_rank_instance.transform.call_args[0][0]
            assert len(call_args) == 1
            assert result is not None

    @staticmethod
    def test_run_pipeline_failure(tmp_path: Path) -> None:
        """Test pipeline handles failures correctly."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract,
        ):
            # Setup extraction to raise error
            mock_extract.return_value.run.side_effect = RuntimeError("Test error")

            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Should raise and notify observers
            with pytest.raises(RuntimeError, match="Test error"):
                orchestrator.run()

    @staticmethod
    def test_run_attaches_observers_to_stages(tmp_path: Path) -> None:
        """Test pipeline attaches observers to all stages."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
            patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract,
            patch("msc.pipeline.orchestrator.EnrichmentStage") as mock_enrich,
            patch("msc.pipeline.orchestrator.RankingStage") as mock_rank,
        ):
            # Setup basic mocks
            mock_extract.return_value.run.return_value = []
            mock_enrich.return_value.transform.return_value = []
            mock_rank.return_value.transform.return_value = PowerRankingResults(
                year=2024, rankings=[], total_tracks=0
            )

            orchestrator = PipelineOrchestrator(data_dir=tmp_path)
            orchestrator.run()

            # Verify observers were attached
            assert mock_extract.return_value.attach.call_count == 4
            assert mock_enrich.return_value.attach.call_count == 4
            assert mock_rank.return_value.attach.call_count == 4


class TestPipelineOrchestratorObservers:
    """Tests for observer management."""

    @staticmethod
    def test_add_custom_observer(tmp_path: Path) -> None:
        """Test adding custom observer."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Create mock observer
            mock_observer = Mock(spec=PipelineObserver)

            # Add observer
            orchestrator.add_observer(mock_observer)

            # Should have 5 observers now (4 default + 1 custom)
            assert len(orchestrator._observers) == 5


class TestPipelineOrchestratorHelpers:
    """Tests for helper methods."""

    @staticmethod
    def test_get_metrics(tmp_path: Path) -> None:
        """Test getting pipeline metrics."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)
            metrics = orchestrator.get_metrics()

            assert isinstance(metrics, dict)

    @staticmethod
    def test_get_review_queue(tmp_path: Path) -> None:
        """Test getting review queue."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Add item to review queue
            track = Track(title="Test", artist_list=["Artist"], year=2024)
            orchestrator.review_queue.add(
                track.identifier, "Test", "Artist", "Test reason"
            )

            # Get review queue
            items = orchestrator.get_review_queue()
            assert len(items) == 1

    @staticmethod
    def test_clear_checkpoints(tmp_path: Path) -> None:
        """Test clearing checkpoints."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Create checkpoint files
            from datetime import datetime

            from msc.storage.checkpoint import CheckpointState

            now = datetime.now()
            extract_state = CheckpointState(
                stage_name="extraction",
                created_at=now,
                last_updated=now,
                processed_ids={"test"},
            )
            enrich_state = CheckpointState(
                stage_name="enrichment",
                created_at=now,
                last_updated=now,
                processed_ids={"test"},
            )

            orchestrator.checkpoint_mgr.save_checkpoint(extract_state)
            orchestrator.checkpoint_mgr.save_checkpoint(enrich_state)

            # Clear checkpoints
            orchestrator.clear_checkpoints()

            # Verify checkpoint files are deleted
            checkpoint_dir = orchestrator.checkpoint_dir
            assert not (checkpoint_dir / "extraction.json").exists()
            assert not (checkpoint_dir / "enrichment.json").exists()

    @staticmethod
    def test_reset_pipeline(tmp_path: Path) -> None:
        """Test resetting entire pipeline."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Add data to repositories and review queue
            track = Track(title="Test", artist_list=["Artist"], year=2024)
            orchestrator.track_repository.add(track)

            stats = TrackWithStats(
                track=track,
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id="123", songstats_title="Test"
                ),
                platform_stats=PlatformStats(),
            )
            orchestrator.stats_repository.add(stats)
            orchestrator.review_queue.add(track.identifier, "Test", "Artist", "Test")

            # Reset pipeline
            orchestrator.reset_pipeline()

            # Verify everything is cleared
            assert orchestrator.track_repository.count() == 0
            assert orchestrator.stats_repository.count() == 0
            assert len(orchestrator.review_queue.get_all()) == 0
