"""Tests for pipeline observer implementations.

Tests ConsoleObserver, FileObserver, ProgressBarObserver, MetricsObserver,
and the Observable mixin for event handling and notification.
"""

# Standard library
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Third-party
import pytest

# Local
from msc.pipeline.observer import EventType, Observable, PipelineEvent, PipelineObserver
from msc.pipeline.observers import (
    ConsoleObserver,
    FileObserver,
    MetricsObserver,
    ProgressBarObserver,
)


class TestPipelineEvent:
    """Tests for PipelineEvent dataclass."""

    @staticmethod
    def test_create_minimal_event() -> None:
        """Test creating event with minimal fields."""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
        )

        assert event.event_type == EventType.PIPELINE_STARTED
        assert event.stage_name is None
        assert event.item_id is None
        assert event.message is None
        assert event.metadata is None
        assert event.error is None

    @staticmethod
    def test_create_full_event() -> None:
        """Test creating event with all fields."""
        timestamp = datetime.now()
        error = ValueError("test error")
        metadata = {"count": 10}

        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=timestamp,
            stage_name="extraction",
            item_id="track_123",
            message="Processing failed",
            metadata=metadata,
            error=error,
        )

        assert event.event_type == EventType.ITEM_FAILED
        assert event.timestamp == timestamp
        assert event.stage_name == "extraction"
        assert event.item_id == "track_123"
        assert event.message == "Processing failed"
        assert event.metadata == metadata
        assert event.error == error

    @staticmethod
    def test_event_is_frozen() -> None:
        """Test that events are immutable."""
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            event.event_type = EventType.STAGE_COMPLETED  # type: ignore

    @staticmethod
    def test_event_str_representation() -> None:
        """Test string representation of event."""
        event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            stage_name="enrichment",
            item_id="track_456",
            message="Fetching stats",
        )

        str_repr = str(event)
        assert "[2024-01-01T12:00:00]" in str_repr
        assert "item_processing" in str_repr
        assert "stage=enrichment" in str_repr
        assert "item=track_456" in str_repr
        assert "Fetching stats" in str_repr


class TestObservable:
    """Tests for Observable mixin."""

    @staticmethod
    def test_attach_observer() -> None:
        """Test attaching an observer."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)

        observable.attach(observer)

        assert observer in observable._observers

    @staticmethod
    def test_attach_same_observer_twice() -> None:
        """Test that attaching same observer twice doesn't duplicate."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)

        observable.attach(observer)
        observable.attach(observer)

        assert observable._observers.count(observer) == 1

    @staticmethod
    def test_detach_observer() -> None:
        """Test detaching an observer."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)

        observable.attach(observer)
        observable.detach(observer)

        assert observer not in observable._observers

    @staticmethod
    def test_detach_nonexistent_observer() -> None:
        """Test detaching observer that wasn't attached."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)

        # Should not raise error
        observable.detach(observer)

    @staticmethod
    def test_notify_routes_to_specific_handler() -> None:
        """Test that notify routes events to specific handlers."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)
        observable.attach(observer)

        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
            stage_name="extraction",
        )

        observable.notify(event)

        # Should call specific handler
        observer.on_stage_started.assert_called_once_with(event)

    @staticmethod
    def test_notify_falls_back_for_unknown_events() -> None:
        """Test that notify falls back to on_event for unknown event types."""
        observable = Observable()
        observer = Mock(spec=PipelineObserver)
        observable.attach(observer)

        # WARNING and ERROR don't have specific handlers
        event = PipelineEvent(
            event_type=EventType.WARNING,
            timestamp=datetime.now(),
            message="Warning message",
        )

        observable.notify(event)

        # Should call generic handler
        observer.on_event.assert_called_once_with(event)

    @staticmethod
    def test_create_event_helper() -> None:
        """Test the create_event helper method."""
        event = Observable.create_event(
            event_type=EventType.ITEM_COMPLETED,
            stage_name="ranking",
            item_id="track_789",
            message="Ranking computed",
            metadata={"score": 85.5},
        )

        assert event.event_type == EventType.ITEM_COMPLETED
        assert event.stage_name == "ranking"
        assert event.item_id == "track_789"
        assert event.message == "Ranking computed"
        assert event.metadata == {"score": 85.5}
        assert isinstance(event.timestamp, datetime)


class TestConsoleObserver:
    """Tests for ConsoleObserver."""

    @staticmethod
    def test_init_default() -> None:
        """Test default initialization."""
        observer = ConsoleObserver()

        assert observer.verbose is False
        assert observer.console is not None

    @staticmethod
    def test_init_verbose() -> None:
        """Test initialization with verbose mode."""
        observer = ConsoleObserver(verbose=True)

        assert observer.verbose is True

    @staticmethod
    @patch("msc.pipeline.observers.Console")
    def test_on_event_verbose_mode(mock_console_class: Mock) -> None:
        """Test that verbose mode logs all events."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        observer = ConsoleObserver(verbose=True)
        event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            message="Processing item",
        )

        observer.on_event(event)

        # Should print in verbose mode
        mock_console.print.assert_called_once()

    @staticmethod
    @patch("msc.pipeline.observers.Console")
    def test_on_event_non_verbose_skips_verbose_events(mock_console_class: Mock) -> None:
        """Test that non-verbose mode skips verbose events."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        observer = ConsoleObserver(verbose=False)
        event = PipelineEvent(
            event_type=EventType.ITEM_PROCESSING,
            timestamp=datetime.now(),
            message="Processing item",
        )

        observer.on_event(event)

        # Should NOT print in non-verbose mode
        mock_console.print.assert_not_called()

    @staticmethod
    @patch("msc.pipeline.observers.Console")
    def test_on_event_uses_correct_style(mock_console_class: Mock) -> None:
        """Test that different event types use correct styling."""
        mock_console = MagicMock()
        mock_console_class.return_value = mock_console

        observer = ConsoleObserver(verbose=True)

        # Test error style
        error_event = PipelineEvent(
            event_type=EventType.PIPELINE_FAILED,
            timestamp=datetime.now(),
            message="Pipeline failed",
        )
        observer.on_event(error_event)
        mock_console.print.assert_called_with(str(error_event), style="bold red")

        mock_console.reset_mock()

        # Test success style
        success_event = PipelineEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            timestamp=datetime.now(),
            message="Pipeline completed",
        )
        observer.on_event(success_event)
        mock_console.print.assert_called_with(str(success_event), style="bold green")


class TestFileObserver:
    """Tests for FileObserver."""

    @staticmethod
    def test_init_creates_directory(tmp_path: Path) -> None:
        """Test that initialization creates parent directory."""
        log_file = tmp_path / "logs" / "events.jsonl"

        observer = FileObserver(log_file)

        assert log_file.parent.exists()
        assert observer.file_path == log_file

    @staticmethod
    def test_on_event_appends_to_file(tmp_path: Path) -> None:
        """Test that events are appended to log file."""
        log_file = tmp_path / "events.jsonl"
        observer = FileObserver(log_file)

        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            stage_name="extraction",
            message="Starting extraction",
        )

        observer.on_event(event)

        # Check file was created and contains event
        assert log_file.exists()
        with open(log_file, encoding="utf-8") as f:
            line = f.readline()
            logged_event = json.loads(line)

        assert logged_event["event_type"] == "stage_started"
        assert logged_event["stage_name"] == "extraction"
        assert logged_event["message"] == "Starting extraction"

    @staticmethod
    def test_on_event_logs_error(tmp_path: Path) -> None:
        """Test that error events include error information."""
        log_file = tmp_path / "events.jsonl"
        observer = FileObserver(log_file)

        error = ValueError("Something went wrong")
        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
            item_id="track_123",
            error=error,
        )

        observer.on_event(event)

        with open(log_file, encoding="utf-8") as f:
            logged_event = json.loads(f.readline())

        assert "error" in logged_event
        assert logged_event["error"]["type"] == "ValueError"
        assert logged_event["error"]["message"] == "Something went wrong"

    @staticmethod
    def test_get_events(tmp_path: Path) -> None:
        """Test getting all logged events."""
        log_file = tmp_path / "events.jsonl"
        observer = FileObserver(log_file)

        events = [
            PipelineEvent(
                event_type=EventType.PIPELINE_STARTED,
                timestamp=datetime.now(),
            ),
            PipelineEvent(
                event_type=EventType.STAGE_STARTED,
                timestamp=datetime.now(),
                stage_name="extraction",
            ),
        ]

        for event in events:
            observer.on_event(event)

        logged = observer.get_events()
        assert len(logged) == 2
        assert logged[0]["event_type"] == "pipeline_started"
        assert logged[1]["event_type"] == "stage_started"

    @staticmethod
    def test_on_event_handles_write_error(tmp_path: Path) -> None:
        """Test that write errors are handled gracefully."""
        log_file = tmp_path / "events.jsonl"
        observer = FileObserver(log_file)

        # Make file read-only to force write error
        log_file.touch()
        log_file.chmod(0o444)

        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        # Should not raise exception
        observer.on_event(event)

        # Event should still be in memory
        assert len(observer.events) == 1

        # Restore permissions for cleanup
        log_file.chmod(0o644)


class TestProgressBarObserver:
    """Tests for ProgressBarObserver."""

    @staticmethod
    def test_init() -> None:
        """Test initialization."""
        observer = ProgressBarObserver()

        assert observer.progress is not None
        assert observer.tasks == {}
        assert observer.started is False

    @staticmethod
    def test_on_pipeline_started() -> None:
        """Test that pipeline start begins progress display."""
        observer = ProgressBarObserver()

        with patch.object(observer.progress, "start") as mock_start:
            event = PipelineEvent(
                event_type=EventType.PIPELINE_STARTED,
                timestamp=datetime.now(),
            )

            observer.on_pipeline_started(event)

            mock_start.assert_called_once()
            assert observer.started is True

    @staticmethod
    def test_on_pipeline_completed_stops_progress() -> None:
        """Test that pipeline completion stops progress display."""
        observer = ProgressBarObserver()
        observer.started = True

        with patch.object(observer.progress, "stop") as mock_stop:
            event = PipelineEvent(
                event_type=EventType.PIPELINE_COMPLETED,
                timestamp=datetime.now(),
            )

            observer.on_pipeline_completed(event)

            mock_stop.assert_called_once()
            assert observer.started is False

    @staticmethod
    def test_on_stage_started_creates_task() -> None:
        """Test that stage start creates a progress task."""
        observer = ProgressBarObserver()

        with patch.object(observer.progress, "add_task") as mock_add_task:
            mock_add_task.return_value = 1  # Mock task ID

            event = PipelineEvent(
                event_type=EventType.STAGE_STARTED,
                timestamp=datetime.now(),
                stage_name="extraction",
                metadata={"total": 100},
            )

            observer.on_stage_started(event)

            mock_add_task.assert_called_once()
            assert observer.tasks["extraction"] == 1

    @staticmethod
    def test_on_item_completed_advances_progress() -> None:
        """Test that item completion advances progress bar."""
        observer = ProgressBarObserver()
        observer.tasks["extraction"] = 1  # Mock task ID

        with patch.object(observer.progress, "advance") as mock_advance:
            event = PipelineEvent(
                event_type=EventType.ITEM_COMPLETED,
                timestamp=datetime.now(),
                stage_name="extraction",
            )

            observer.on_item_completed(event)

            mock_advance.assert_called_once_with(1, 1)

    @staticmethod
    def test_on_item_failed_advances_progress() -> None:
        """Test that failed items also advance progress."""
        observer = ProgressBarObserver()
        observer.tasks["enrichment"] = 2

        with patch.object(observer.progress, "advance") as mock_advance:
            event = PipelineEvent(
                event_type=EventType.ITEM_FAILED,
                timestamp=datetime.now(),
                stage_name="enrichment",
            )

            observer.on_item_failed(event)

            mock_advance.assert_called_once_with(2, 1)

    @staticmethod
    def test_on_item_skipped_advances_progress() -> None:
        """Test that skipped items also advance progress."""
        observer = ProgressBarObserver()
        observer.tasks["ranking"] = 3

        with patch.object(observer.progress, "advance") as mock_advance:
            event = PipelineEvent(
                event_type=EventType.ITEM_SKIPPED,
                timestamp=datetime.now(),
                stage_name="ranking",
            )

            observer.on_item_skipped(event)

            mock_advance.assert_called_once_with(3, 1)

    @staticmethod
    def test_context_manager() -> None:
        """Test using observer as context manager."""
        with patch("msc.pipeline.observers.Progress") as mock_progress_class:
            mock_progress = MagicMock()
            mock_progress_class.return_value = mock_progress

            with ProgressBarObserver() as observer:
                assert observer is not None

            # Progress should be stopped on exit
            # (stop is called in close() if started)

    @staticmethod
    def test_close_when_started() -> None:
        """Test that close stops progress if started."""
        observer = ProgressBarObserver()
        observer.started = True

        with patch.object(observer.progress, "stop") as mock_stop:
            observer.close()

            mock_stop.assert_called_once()
            assert observer.started is False


class TestMetricsObserver:
    """Tests for MetricsObserver."""

    @staticmethod
    def test_init() -> None:
        """Test initialization."""
        observer = MetricsObserver()

        assert observer.metrics["items_processed"] == 0
        assert observer.metrics["items_failed"] == 0
        assert observer.metrics["items_skipped"] == 0
        assert observer.metrics["stages_completed"] == 0
        assert observer.metrics["stages_failed"] == 0
        assert observer.metrics["events_by_type"] == {}

    @staticmethod
    def test_on_item_completed() -> None:
        """Test item completion increments counter."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.ITEM_COMPLETED,
            timestamp=datetime.now(),
        )

        observer.on_item_completed(event)

        assert observer.metrics["items_processed"] == 1
        assert observer.metrics["events_by_type"]["item_completed"] == 1

    @staticmethod
    def test_on_item_failed() -> None:
        """Test item failure increments counter."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime.now(),
        )

        observer.on_item_failed(event)

        assert observer.metrics["items_failed"] == 1

    @staticmethod
    def test_on_item_skipped() -> None:
        """Test item skipped increments counter."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.ITEM_SKIPPED,
            timestamp=datetime.now(),
        )

        observer.on_item_skipped(event)

        assert observer.metrics["items_skipped"] == 1

    @staticmethod
    def test_on_stage_completed() -> None:
        """Test stage completion increments counter."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.STAGE_COMPLETED,
            timestamp=datetime.now(),
        )

        observer.on_stage_completed(event)

        assert observer.metrics["stages_completed"] == 1

    @staticmethod
    def test_on_stage_failed() -> None:
        """Test stage failure increments counter."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.STAGE_FAILED,
            timestamp=datetime.now(),
        )

        observer.on_stage_failed(event)

        assert observer.metrics["stages_failed"] == 1

    @staticmethod
    def test_get_metrics() -> None:
        """Test getting metrics returns a copy."""
        observer = MetricsObserver()

        event = PipelineEvent(
            event_type=EventType.ITEM_COMPLETED,
            timestamp=datetime.now(),
        )
        observer.on_item_completed(event)

        metrics = observer.get_metrics()

        # Modify the returned metrics
        metrics["items_processed"] = 999

        # Original should be unchanged
        assert observer.metrics["items_processed"] == 1

    @staticmethod
    def test_get_success_rate_with_no_items() -> None:
        """Test success rate calculation with no items."""
        observer = MetricsObserver()

        rate = observer.get_success_rate()

        assert rate == 0.0

    @staticmethod
    def test_get_success_rate_all_successful() -> None:
        """Test success rate with all successful items."""
        observer = MetricsObserver()

        for _ in range(10):
            event = PipelineEvent(
                event_type=EventType.ITEM_COMPLETED,
                timestamp=datetime.now(),
            )
            observer.on_item_completed(event)

        rate = observer.get_success_rate()

        assert rate == 100.0

    @staticmethod
    def test_get_success_rate_mixed() -> None:
        """Test success rate with mixed results."""
        observer = MetricsObserver()

        # 7 successful, 3 failed
        for _ in range(7):
            event = PipelineEvent(
                event_type=EventType.ITEM_COMPLETED,
                timestamp=datetime.now(),
            )
            observer.on_item_completed(event)

        for _ in range(3):
            event = PipelineEvent(
                event_type=EventType.ITEM_FAILED,
                timestamp=datetime.now(),
            )
            observer.on_item_failed(event)

        rate = observer.get_success_rate()

        assert rate == 70.0

    @staticmethod
    def test_events_by_type_counting() -> None:
        """Test that events are counted by type."""
        observer = MetricsObserver()

        # Create multiple events of different types
        events = [
            (EventType.PIPELINE_STARTED, observer.on_event),
            (EventType.STAGE_STARTED, observer.on_stage_started),
            (EventType.ITEM_COMPLETED, observer.on_item_completed),
            (EventType.ITEM_COMPLETED, observer.on_item_completed),
            (EventType.ITEM_FAILED, observer.on_item_failed),
        ]

        for event_type, handler in events:
            event = PipelineEvent(event_type=event_type, timestamp=datetime.now())
            handler(event)

        events_by_type = observer.metrics["events_by_type"]
        assert events_by_type["pipeline_started"] == 1
        assert events_by_type["stage_started"] == 1
        assert events_by_type["item_completed"] == 2
        assert events_by_type["item_failed"] == 1
