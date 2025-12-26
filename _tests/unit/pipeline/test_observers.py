"""Unit tests for concrete observer implementations.

Tests ConsoleObserver, FileObserver, ProgressBarObserver, and MetricsObserver.
"""

# Standard library
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Local
from msc.pipeline.observer import EventType, PipelineEvent
from msc.pipeline.observers import (
    ConsoleObserver,
    FileObserver,
    MetricsObserver,
    ProgressBarObserver,
    TRUNCATION_LIMIT,
)


class TestConsoleObserverInit:
    """Tests for ConsoleObserver initialization."""

    @staticmethod
    def test_default_verbose_false() -> None:
        """Should default verbose to False."""
        observer = ConsoleObserver()

        assert observer.verbose is False

    @staticmethod
    def test_accepts_verbose_true() -> None:
        """Should accept verbose parameter."""
        observer = ConsoleObserver(verbose=True)

        assert observer.verbose is True

    @staticmethod
    def test_creates_console() -> None:
        """Should create Rich console."""
        observer = ConsoleObserver()

        assert observer.console is not None


class TestConsoleObserverOnEvent:
    """Tests for ConsoleObserver.on_event method."""

    @staticmethod
    def test_verbose_mode_logs_all_events() -> None:
        """Should log all events in verbose mode."""
        observer = ConsoleObserver(verbose=True)
        event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            message="Processing item",
        )

        with patch.object(observer.console, "print") as mock_print:
            observer.on_event(event)

            mock_print.assert_called_once()

    @staticmethod
    def test_non_verbose_filters_item_events() -> None:
        """Should filter item-level events in non-verbose mode."""
        observer = ConsoleObserver(verbose=False)
        event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
        )

        with patch.object(observer.console, "print") as mock_print:
            observer.on_event(event)

            mock_print.assert_not_called()

    @staticmethod
    def test_non_verbose_shows_pipeline_events() -> None:
        """Should show pipeline-level events in non-verbose mode."""
        observer = ConsoleObserver(verbose=False)
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
        )

        with patch.object(observer.console, "print") as mock_print:
            observer.on_event(event)

            mock_print.assert_called_once()

    @staticmethod
    def test_non_verbose_shows_errors() -> None:
        """Should show error events in non-verbose mode."""
        observer = ConsoleObserver(verbose=False)
        event = PipelineEvent(
            event_type=EventType.ERROR,
            timestamp=datetime.now(),
        )

        with patch.object(observer.console, "print") as mock_print:
            observer.on_event(event)

            mock_print.assert_called_once()


class TestFileObserverInit:
    """Tests for FileObserver initialization."""

    @staticmethod
    def test_creates_parent_directory(tmp_path: Path) -> None:
        """Should create parent directory if needed."""
        log_path = tmp_path / "logs" / "subdir" / "events.jsonl"

        FileObserver(log_path)

        assert log_path.parent.exists()

    @staticmethod
    def test_resolves_path(tmp_path: Path) -> None:
        """Should resolve path to absolute."""
        log_path = tmp_path / "events.jsonl"

        observer = FileObserver(log_path)

        assert observer.file_path.is_absolute()

    @staticmethod
    def test_starts_with_empty_events(tmp_path: Path) -> None:
        """Should start with empty events list."""
        log_path = tmp_path / "events.jsonl"

        observer = FileObserver(log_path)

        assert observer.events == []


class TestFileObserverOnEvent:
    """Tests for FileObserver.on_event method."""

    @staticmethod
    def test_appends_to_events_list(tmp_path: Path) -> None:
        """Should append event to internal list."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        observer.on_event(event)

        assert len(observer.events) == 1

    @staticmethod
    def test_writes_to_file(tmp_path: Path) -> None:
        """Should write event to file."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            stage_name="Extraction",
        )

        observer.on_event(event)

        content = log_path.read_text(encoding="utf-8")
        assert "stage_started" in content
        assert "Extraction" in content

    @staticmethod
    def test_appends_multiple_events(tmp_path: Path) -> None:
        """Should append multiple events to file."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)

        for i in range(3):
            event = PipelineEvent(
                event_type=EventType.ITEM_COMPLETED,
                timestamp=datetime.now(),
                item_id=f"item{i}",
            )
            observer.on_event(event)

        lines = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 3

    @staticmethod
    def test_writes_valid_json(tmp_path: Path) -> None:
        """Should write valid JSON for each event."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)
        event = PipelineEvent(
            event_type=EventType.STAGE_COMPLETED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        observer.on_event(event)

        content = log_path.read_text(encoding="utf-8").strip()
        parsed = json.loads(content)
        assert parsed["event_type"] == "stage_completed"

    @staticmethod
    def test_includes_error_info(tmp_path: Path) -> None:
        """Should include error information."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)
        error = ValueError("Test error")
        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
            error=error,
        )

        observer.on_event(event)

        content = log_path.read_text(encoding="utf-8")
        parsed = json.loads(content)
        assert "error" in parsed
        assert parsed["error"]["type"] == "ValueError"
        assert "Test error" in parsed["error"]["message"]


class TestFileObserverGetEvents:
    """Tests for FileObserver.get_events method."""

    @staticmethod
    def test_returns_copy_of_events(tmp_path: Path) -> None:
        """Should return copy of events list."""
        log_path = tmp_path / "events.jsonl"
        observer = FileObserver(log_path)
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )
        observer.on_event(event)

        result = observer.get_events()
        result.clear()

        assert len(observer.events) == 1


class TestProgressBarObserverInit:
    """Tests for ProgressBarObserver initialization."""

    @staticmethod
    def test_creates_progress() -> None:
        """Should create Rich progress bar."""
        observer = ProgressBarObserver()

        assert observer.progress is not None

    @staticmethod
    def test_starts_not_started() -> None:
        """Should start in not-started state."""
        observer = ProgressBarObserver()

        assert observer.started is False

    @staticmethod
    def test_starts_with_empty_tasks() -> None:
        """Should start with no tasks."""
        observer = ProgressBarObserver()

        assert observer.tasks == {}


class TestProgressBarObserverPipelineEvents:
    """Tests for ProgressBarObserver pipeline event handlers."""

    @staticmethod
    def test_on_pipeline_started_starts_progress() -> None:
        """Should start progress display."""
        observer = ProgressBarObserver()
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
        )

        with patch.object(observer.progress, "start"):
            observer.on_pipeline_started(event)

            assert observer.started is True

    @staticmethod
    def test_on_pipeline_completed_stops_progress() -> None:
        """Should stop progress display."""
        observer = ProgressBarObserver()
        observer.started = True
        event = PipelineEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            timestamp=datetime.now(),
        )

        with patch.object(observer.progress, "stop"):
            observer.on_pipeline_completed(event)

            assert observer.started is False

    @staticmethod
    def test_on_pipeline_failed_stops_progress() -> None:
        """Should stop progress display on failure."""
        observer = ProgressBarObserver()
        observer.started = True
        event = PipelineEvent(
            event_type=EventType.PIPELINE_FAILED,
            timestamp=datetime.now(),
        )

        with patch.object(observer.progress, "stop"):
            observer.on_pipeline_failed(event)

            assert observer.started is False


class TestProgressBarObserverStageEvents:
    """Tests for ProgressBarObserver stage event handlers."""

    @staticmethod
    def test_on_stage_started_creates_task() -> None:
        """Should create progress task for stage."""
        observer = ProgressBarObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )

        with patch.object(observer.progress, "add_task", return_value=1) as mock_add:
            observer.on_stage_started(event)

            mock_add.assert_called_once()
            assert "Extraction" in observer.tasks

    @staticmethod
    def test_on_stage_started_requires_total() -> None:
        """Should not create task without total in metadata."""
        observer = ProgressBarObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
        )

        with patch.object(observer.progress, "add_task") as mock_add:
            observer.on_stage_started(event)

            mock_add.assert_not_called()


class TestProgressBarObserverItemEvents:
    """Tests for ProgressBarObserver item event handlers."""

    @staticmethod
    def test_on_item_completed_advances_progress() -> None:
        """Should advance progress bar."""
        observer = ProgressBarObserver()
        observer.tasks["Extraction"] = 1
        event = PipelineEvent(
            event_type=EventType.ITEM_COMPLETED,
            timestamp=datetime.now(),
            stage_name="Extraction",
        )

        with patch.object(observer.progress, "advance") as mock_advance:
            observer.on_item_completed(event)

            mock_advance.assert_called_once_with(1, 1)

    @staticmethod
    def test_on_item_skipped_advances_progress() -> None:
        """Should advance progress bar for skipped items."""
        observer = ProgressBarObserver()
        observer.tasks["Extraction"] = 1
        event = PipelineEvent(
            event_type=EventType.ITEM_SKIPPED,
            timestamp=datetime.now(),
            stage_name="Extraction",
        )

        with patch.object(observer.progress, "advance") as mock_advance:
            observer.on_item_skipped(event)

            mock_advance.assert_called_once_with(1, 1)

    @staticmethod
    def test_on_item_failed_advances_progress() -> None:
        """Should advance progress bar for failed items."""
        observer = ProgressBarObserver()
        observer.tasks["Extraction"] = 1
        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            error=ValueError("Test error"),
        )

        with patch.object(observer.progress, "advance") as mock_advance:
            with patch.object(observer.progress, "update"):
                observer.on_item_failed(event)

                mock_advance.assert_called_once()


class TestProgressBarObserverClose:
    """Tests for ProgressBarObserver.close method."""

    @staticmethod
    def test_close_stops_progress() -> None:
        """Should stop progress when closed."""
        observer = ProgressBarObserver()
        observer.started = True

        with patch.object(observer.progress, "stop"):
            observer.close()

            assert observer.started is False

    @staticmethod
    def test_close_is_idempotent() -> None:
        """Should handle multiple close calls."""
        observer = ProgressBarObserver()
        observer.started = False

        # Should not raise
        observer.close()


class TestProgressBarObserverContextManager:
    """Tests for ProgressBarObserver context manager support."""

    @staticmethod
    def test_enter_returns_self() -> None:
        """Should return self on enter."""
        observer = ProgressBarObserver()

        result = observer.__enter__()

        assert result is observer

    @staticmethod
    def test_exit_calls_close() -> None:
        """Should call close on exit."""
        observer = ProgressBarObserver()

        with patch.object(observer, "close") as mock_close:
            observer.__exit__(None, None, None)

            mock_close.assert_called_once()


class TestMetricsObserverInit:
    """Tests for MetricsObserver initialization."""

    @staticmethod
    def test_starts_with_zero_counts() -> None:
        """Should start with zero counts."""
        observer = MetricsObserver()

        assert observer.metrics["items_processed"] == 0
        assert observer.metrics["items_failed"] == 0
        assert observer.metrics["items_skipped"] == 0
        assert observer.metrics["stages_completed"] == 0
        assert observer.metrics["stages_failed"] == 0

    @staticmethod
    def test_starts_with_empty_events_by_type() -> None:
        """Should start with empty events_by_type."""
        observer = MetricsObserver()

        assert observer.metrics["events_by_type"] == {}


class TestMetricsObserverOnEvent:
    """Tests for MetricsObserver.on_event method."""

    @staticmethod
    def test_counts_events_by_type() -> None:
        """Should count events by type."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        observer.on_event(event)

        assert observer.metrics["events_by_type"]["stage_started"] == 1

    @staticmethod
    def test_increments_event_count() -> None:
        """Should increment count for same event type."""
        observer = MetricsObserver()

        for _ in range(3):
            event = PipelineEvent(
                event_type=EventType.ITEM_PROCESSING,
                timestamp=datetime.now(),
            )
            observer.on_event(event)

        assert observer.metrics["events_by_type"]["item_processing"] == 3


class TestMetricsObserverItemEvents:
    """Tests for MetricsObserver item event handlers."""

    @staticmethod
    def test_on_item_completed_increments_processed() -> None:
        """Should increment items_processed."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.ITEM_COMPLETED,
            timestamp=datetime.now(),
        )

        observer.on_item_completed(event)

        assert observer.metrics["items_processed"] == 1

    @staticmethod
    def test_on_item_failed_increments_failed() -> None:
        """Should increment items_failed."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
        )

        observer.on_item_failed(event)

        assert observer.metrics["items_failed"] == 1

    @staticmethod
    def test_on_item_skipped_increments_skipped() -> None:
        """Should increment items_skipped."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.ITEM_SKIPPED,
            timestamp=datetime.now(),
        )

        observer.on_item_skipped(event)

        assert observer.metrics["items_skipped"] == 1


class TestMetricsObserverStageEvents:
    """Tests for MetricsObserver stage event handlers."""

    @staticmethod
    def test_on_stage_completed_increments_completed() -> None:
        """Should increment stages_completed."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_COMPLETED,
            timestamp=datetime.now(),
        )

        observer.on_stage_completed(event)

        assert observer.metrics["stages_completed"] == 1

    @staticmethod
    def test_on_stage_failed_increments_failed() -> None:
        """Should increment stages_failed."""
        observer = MetricsObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_FAILED,
            timestamp=datetime.now(),
        )

        observer.on_stage_failed(event)

        assert observer.metrics["stages_failed"] == 1


class TestMetricsObserverGetMetrics:
    """Tests for MetricsObserver.get_metrics method."""

    @staticmethod
    def test_returns_copy_of_metrics() -> None:
        """Should return copy of metrics."""
        observer = MetricsObserver()
        observer.metrics["items_processed"] = 5

        result = observer.get_metrics()
        result["items_processed"] = 0

        assert observer.metrics["items_processed"] == 5


class TestMetricsObserverGetSuccessRate:
    """Tests for MetricsObserver.get_success_rate method."""

    @staticmethod
    def test_returns_zero_when_no_items() -> None:
        """Should return 0 when no items processed."""
        observer = MetricsObserver()

        result = observer.get_success_rate()

        assert result == 0.0

    @staticmethod
    def test_calculates_success_rate() -> None:
        """Should calculate success rate correctly."""
        observer = MetricsObserver()
        observer.metrics["items_processed"] = 8
        observer.metrics["items_failed"] = 2

        result = observer.get_success_rate()

        assert result == 80.0  # 8 / (8 + 2) = 80%

    @staticmethod
    def test_returns_100_when_all_succeed() -> None:
        """Should return 100 when all items succeed."""
        observer = MetricsObserver()
        observer.metrics["items_processed"] = 10
        observer.metrics["items_failed"] = 0

        result = observer.get_success_rate()

        assert result == 100.0

    @staticmethod
    def test_returns_0_when_all_fail() -> None:
        """Should return 0 when all items fail."""
        observer = MetricsObserver()
        observer.metrics["items_processed"] = 0
        observer.metrics["items_failed"] = 10

        result = observer.get_success_rate()

        assert result == 0.0


class TestTruncationLimit:
    """Tests for truncation limit constant."""

    @staticmethod
    def test_truncation_limit_is_positive() -> None:
        """Should have positive truncation limit."""
        assert TRUNCATION_LIMIT > 0

    @staticmethod
    def test_truncation_limit_is_reasonable() -> None:
        """Should have reasonable truncation limit."""
        assert 20 <= TRUNCATION_LIMIT <= 100


class TestProgressBarObserverOnStageCompleted:
    """Tests for ProgressBarObserver.on_stage_completed method."""

    @staticmethod
    def test_completes_progress_bar_for_stage() -> None:
        """Should complete the progress bar when stage finishes."""
        observer = ProgressBarObserver()

        # Start stage with total
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Complete stage
        complete_event = PipelineEvent(
            event_type=EventType.STAGE_COMPLETED,
            timestamp=datetime.now(),
            stage_name="Extraction",
        )
        observer.on_stage_completed(complete_event)

        assert "Extraction" in observer.tasks

    @staticmethod
    def test_handles_unknown_stage() -> None:
        """Should handle completion of unknown stage gracefully."""
        observer = ProgressBarObserver()

        complete_event = PipelineEvent(
            event_type=EventType.STAGE_COMPLETED,
            timestamp=datetime.now(),
            stage_name="Unknown",
        )
        # Should not raise exception
        observer.on_stage_completed(complete_event)


class TestProgressBarObserverOnItemProcessing:
    """Tests for ProgressBarObserver.on_item_processing method."""

    @staticmethod
    def test_updates_description_with_current_item() -> None:
        """Should update progress bar description with current item."""
        observer = ProgressBarObserver()

        # Start stage first
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Process item with current_item in metadata
        process_event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"current_item": "Track 1"},
        )
        observer.on_item_processing(process_event)

        assert observer.current_items.get("Extraction") == "Track 1"

    @staticmethod
    def test_uses_item_id_when_no_current_item() -> None:
        """Should use item_id when current_item not in metadata."""
        observer = ProgressBarObserver()

        # Start stage
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Process item with item_id but no current_item
        process_event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            stage_name="Extraction",
            item_id="track_123",
        )
        observer.on_item_processing(process_event)

        assert observer.current_items.get("Extraction") == "track_123"

    @staticmethod
    def test_uses_default_when_no_item_info() -> None:
        """Should use default text when no item info provided."""
        observer = ProgressBarObserver()

        # Start stage
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Process item with no item info
        process_event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            stage_name="Extraction",
        )
        observer.on_item_processing(process_event)

        assert observer.current_items.get("Extraction") == "Processing..."

    @staticmethod
    def test_truncates_long_item_names() -> None:
        """Should truncate item names that exceed limit."""
        observer = ProgressBarObserver()

        # Start stage
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Process item with very long name
        long_name = "A" * 100
        process_event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"current_item": long_name},
        )
        observer.on_item_processing(process_event)

        truncated_name = observer.current_items.get("Extraction")
        assert truncated_name is not None
        assert len(truncated_name) <= TRUNCATION_LIMIT
        assert truncated_name.endswith("...")


class TestProgressBarObserverOnItemFailed:
    """Tests for ProgressBarObserver.on_item_failed method."""

    @staticmethod
    def test_shows_error_in_description() -> None:
        """Should show error message in progress bar description."""
        observer = ProgressBarObserver()

        # Start stage
        start_event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            metadata={"total": 10},
        )
        observer.on_stage_started(start_event)

        # Fail item
        fail_event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
            stage_name="Extraction",
            error=RuntimeError("Connection failed"),
        )
        # Should not raise exception
        observer.on_item_failed(fail_event)

        # Verify task was advanced (progress.advance called)
        assert "Extraction" in observer.tasks
