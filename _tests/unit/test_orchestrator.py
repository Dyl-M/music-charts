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
            assert orchestrator.checkpoint_dir == tmp_path / "checkpoints"
            assert orchestrator.include_youtube is True
            assert orchestrator.verbose is False

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
    def test_init_attaches_default_observers(tmp_path: Path) -> None:
        """Test orchestrator attaches default observers."""
        with (
            patch("msc.pipeline.orchestrator.MusicBeeClient"),
            patch("msc.pipeline.orchestrator.SongstatsClient"),
        ):
            orchestrator = PipelineOrchestrator(data_dir=tmp_path)

            # Should have 4 default observers
            assert len(orchestrator._observers) == 4


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
