"""Unit tests for PipelineOrchestrator.

Tests pipeline coordination and observer management.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.pipeline.orchestrator import PipelineOrchestrator
from msc.pipeline.observer import EventType, PipelineObserver


class TestPipelineOrchestratorInit:
    """Tests for PipelineOrchestrator initialization."""

    @staticmethod
    def test_uses_settings_data_dir(tmp_path: Path) -> None:
        """Should use data dir from settings by default."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            # Create dummy library file
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    assert orchestrator.data_dir == tmp_path

    @staticmethod
    def test_accepts_custom_data_dir(tmp_path: Path) -> None:
        """Should accept custom data directory."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()

        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(
                        data_dir=custom_dir, new_run=True
                    )

                    assert orchestrator.data_dir == custom_dir

    @staticmethod
    def test_creates_run_directory(tmp_path: Path) -> None:
        """Should create run directory."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    assert orchestrator.run_dir.exists()

    @staticmethod
    def test_creates_checkpoint_directory(tmp_path: Path) -> None:
        """Should create checkpoint directory."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    assert orchestrator.checkpoint_dir.exists()

    @staticmethod
    def test_default_include_youtube_true(tmp_path: Path) -> None:
        """Should default include_youtube to True."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    assert orchestrator.include_youtube is True

    @staticmethod
    def test_default_verbose_false(tmp_path: Path) -> None:
        """Should default verbose to False."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    assert orchestrator.verbose is False

    @staticmethod
    def test_attaches_default_observers(tmp_path: Path) -> None:
        """Should attach default observers."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    # Should have console, file, progress, metrics observers
                    assert len(orchestrator._observers) >= 4


class TestPipelineOrchestratorFindLatestRun:
    """Tests for PipelineOrchestrator._find_latest_run method."""

    @staticmethod
    def test_returns_none_when_no_runs(tmp_path: Path) -> None:
        """Should return None when no runs exist for the year searched."""
        # Use separate directories: one for orchestrator, one for test data
        orchestrator_dir = tmp_path / "orchestrator"
        orchestrator_dir.mkdir()
        test_runs_dir = tmp_path / "test_runs"
        test_runs_dir.mkdir()

        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = orchestrator_dir
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    # Search for runs in a different year than what orchestrator uses
                    result = orchestrator._find_latest_run(2023)

                    assert result is None

    @staticmethod
    def test_finds_latest_run(tmp_path: Path) -> None:
        """Should find the latest run for year."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Create run directories BEFORE orchestrator so they get sorted correctly
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir()
            (runs_dir / "2024_20240101_120000").mkdir()
            (runs_dir / "2024_20240115_120000").mkdir()

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    # Create orchestrator with run_id to avoid creating new run
                    orchestrator = PipelineOrchestrator(run_id="20240115_120000")

                    # Find latest should return the one we specify
                    result = orchestrator._find_latest_run(2024)

                    # Will find "20240115_120000" as latest
                    assert result == "20240115_120000"

    @staticmethod
    def test_ignores_other_years(tmp_path: Path) -> None:
        """Should ignore runs from other years."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Create run directories
            runs_dir = tmp_path / "runs"
            runs_dir.mkdir()
            (runs_dir / "2023_20231201_120000").mkdir()
            (runs_dir / "2024_20240101_120000").mkdir()

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    # Use run_id to avoid creating new run
                    orchestrator = PipelineOrchestrator(run_id="20240101_120000")

                    result = orchestrator._find_latest_run(2024)

                    assert result == "20240101_120000"


class TestPipelineOrchestratorAddObserver:
    """Tests for PipelineOrchestrator.add_observer method."""

    @staticmethod
    def test_adds_observer(tmp_path: Path, mock_observer) -> None:
        """Should add observer to list."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)
                    initial_count = len(orchestrator._observers)

                    orchestrator.add_observer(mock_observer)

                    assert len(orchestrator._observers) == initial_count + 1


class TestPipelineOrchestratorGetMetrics:
    """Tests for PipelineOrchestrator.get_metrics method."""

    @staticmethod
    def test_returns_metrics(tmp_path: Path) -> None:
        """Should return metrics from observer."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    metrics = orchestrator.get_metrics()

                    assert isinstance(metrics, dict)
                    assert "items_processed" in metrics


class TestPipelineOrchestratorGetReviewQueue:
    """Tests for PipelineOrchestrator.get_review_queue method."""

    @staticmethod
    def test_returns_queue_items(tmp_path: Path) -> None:
        """Should return review queue items."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    result = orchestrator.get_review_queue()

                    assert isinstance(result, list)


class TestPipelineOrchestratorClearCheckpoints:
    """Tests for PipelineOrchestrator.clear_checkpoints method."""

    @staticmethod
    def test_clears_both_checkpoints(tmp_path: Path) -> None:
        """Should clear extraction and enrichment checkpoints."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    with patch.object(
                            orchestrator.checkpoint_mgr, "clear_checkpoint"
                    ) as mock_clear:
                        orchestrator.clear_checkpoints()

                        assert mock_clear.call_count == 2


class TestPipelineOrchestratorResetPipeline:
    """Tests for PipelineOrchestrator.reset_pipeline method."""

    @staticmethod
    def test_clears_all_data(tmp_path: Path) -> None:
        """Should clear all pipeline data."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                with patch("msc.pipeline.orchestrator.SongstatsClient"):
                    orchestrator = PipelineOrchestrator(new_run=True)

                    with patch.object(orchestrator, "clear_checkpoints"):
                        with patch.object(orchestrator.track_repository, "clear"):
                            with patch.object(orchestrator.stats_repository, "clear"):
                                with patch.object(orchestrator.review_queue, "clear"):
                                    orchestrator.reset_pipeline()

                                    orchestrator.track_repository.clear.assert_called_once()
                                    orchestrator.stats_repository.clear.assert_called_once()
                                    orchestrator.review_queue.clear.assert_called_once()


class TestPipelineOrchestratorRun:
    """Tests for PipelineOrchestrator.run method."""

    @staticmethod
    def test_run_extraction_only(tmp_path: Path) -> None:
        """Should run only extraction stage when specified."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            result = orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            mock_stage.run.assert_called_once()
            assert result is None

    @staticmethod
    def test_run_emits_pipeline_started_event(tmp_path: Path) -> None:
        """Should emit PIPELINE_STARTED event when run starts."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            # Track emitted events
            events = []

            class EventCapture(PipelineObserver):
                """Captures events for testing."""

                def on_event(self, event):
                    """Capture event."""
                    events.append(event)

            orchestrator.add_observer(EventCapture())

            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            event_types = [e.event_type for e in events]
            assert EventType.PIPELINE_STARTED in event_types

    @staticmethod
    def test_run_emits_pipeline_completed_event(tmp_path: Path) -> None:
        """Should emit PIPELINE_COMPLETED event on success."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            events = []

            class EventCapture(PipelineObserver):
                """Captures events for testing."""

                def on_event(self, event):
                    """Capture event."""
                    events.append(event)

            orchestrator.add_observer(EventCapture())

            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            event_types = [e.event_type for e in events]
            assert EventType.PIPELINE_COMPLETED in event_types

    @staticmethod
    def test_run_emits_pipeline_failed_on_exception(tmp_path: Path) -> None:
        """Should emit PIPELINE_FAILED event when stage raises exception."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            mock_stage = MagicMock()
            mock_stage.run.side_effect = RuntimeError("Test failure")
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            events = []

            class EventCapture(PipelineObserver):
                """Captures events for testing."""

                def on_event(self, event):
                    """Capture event."""
                    events.append(event)

            orchestrator.add_observer(EventCapture())

            with pytest.raises(RuntimeError):
                orchestrator.run(
                    run_extraction=True,
                    run_enrichment=False,
                    run_ranking=False,
                )

            event_types = [e.event_type for e in events]
            assert EventType.PIPELINE_FAILED in event_types


class TestPipelineOrchestratorTestMode:
    """Tests for PipelineOrchestrator test mode functionality."""

    @staticmethod
    def test_test_mode_uses_mock_client(tmp_path: Path) -> None:
        """Should use mock client when test_mode is True."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.clients.create_mock_songstats_client") as mock_factory:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.test_library_path = tmp_path / "test_library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "test_library.xml").write_text("<library/>", encoding="utf-8")

            mock_client = MagicMock()
            mock_factory.return_value = mock_client

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                test_mode=True,
                new_run=True,
            )

            assert orchestrator.test_mode is True

    @staticmethod
    def test_track_limit_stored(tmp_path: Path) -> None:
        """Should store track_limit parameter."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"):
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                track_limit=10,
                new_run=True,
            )

            assert orchestrator.track_limit == 10
