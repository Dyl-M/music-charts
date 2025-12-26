"""Unit tests for pipeline observer pattern.

Tests EventType, PipelineEvent, PipelineObserver, and Observable.
"""

# Standard library
from abc import ABC
from datetime import datetime

# Third-party
import pytest

# Local
from msc.pipeline.observer import (
    EventType,
    Observable,
    PipelineEvent,
    PipelineObserver,
)


class TestEventType:
    """Tests for EventType enum."""

    @staticmethod
    def test_pipeline_started() -> None:
        """Should have PIPELINE_STARTED event."""
        assert EventType.PIPELINE_STARTED.value == "pipeline_started"

    @staticmethod
    def test_pipeline_completed() -> None:
        """Should have PIPELINE_COMPLETED event."""
        assert EventType.PIPELINE_COMPLETED.value == "pipeline_completed"

    @staticmethod
    def test_pipeline_failed() -> None:
        """Should have PIPELINE_FAILED event."""
        assert EventType.PIPELINE_FAILED.value == "pipeline_failed"

    @staticmethod
    def test_stage_started() -> None:
        """Should have STAGE_STARTED event."""
        assert EventType.STAGE_STARTED.value == "stage_started"

    @staticmethod
    def test_stage_completed() -> None:
        """Should have STAGE_COMPLETED event."""
        assert EventType.STAGE_COMPLETED.value == "stage_completed"

    @staticmethod
    def test_stage_failed() -> None:
        """Should have STAGE_FAILED event."""
        assert EventType.STAGE_FAILED.value == "stage_failed"

    @staticmethod
    def test_item_processing() -> None:
        """Should have ITEM_PROCESSING event."""
        assert EventType.ITEM_PROCESSING.value == "item_processing"

    @staticmethod
    def test_item_completed() -> None:
        """Should have ITEM_COMPLETED event."""
        assert EventType.ITEM_COMPLETED.value == "item_completed"

    @staticmethod
    def test_item_failed() -> None:
        """Should have ITEM_FAILED event."""
        assert EventType.ITEM_FAILED.value == "item_failed"

    @staticmethod
    def test_item_skipped() -> None:
        """Should have ITEM_SKIPPED event."""
        assert EventType.ITEM_SKIPPED.value == "item_skipped"

    @staticmethod
    def test_checkpoint_saved() -> None:
        """Should have CHECKPOINT_SAVED event."""
        assert EventType.CHECKPOINT_SAVED.value == "checkpoint_saved"

    @staticmethod
    def test_checkpoint_loaded() -> None:
        """Should have CHECKPOINT_LOADED event."""
        assert EventType.CHECKPOINT_LOADED.value == "checkpoint_loaded"

    @staticmethod
    def test_warning() -> None:
        """Should have WARNING event."""
        assert EventType.WARNING.value == "warning"

    @staticmethod
    def test_error() -> None:
        """Should have ERROR event."""
        assert EventType.ERROR.value == "error"


class TestPipelineEvent:
    """Tests for PipelineEvent dataclass."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create event with required fields."""
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        assert event.event_type == EventType.STAGE_STARTED
        assert event.timestamp == datetime(2024, 1, 1, 12, 0, 0)

    @staticmethod
    def test_optional_fields_default_to_none() -> None:
        """Should default optional fields to None."""
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        assert event.stage_name is None
        assert event.item_id is None
        assert event.message is None
        assert event.metadata is None
        assert event.error is None

    @staticmethod
    def test_creates_with_all_fields() -> None:
        """Should create event with all fields."""
        error = ValueError("Test error")
        event = PipelineEvent(
            event_type=EventType.ITEM_FAILED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            stage_name="Extraction",
            item_id="track123",
            message="Processing failed",
            metadata={"key": "value"},
            error=error,
        )

        assert event.stage_name == "Extraction"
        assert event.item_id == "track123"
        assert event.message == "Processing failed"
        assert event.metadata == {"key": "value"}
        assert event.error is error

    @staticmethod
    def test_is_frozen() -> None:
        """Should be immutable (frozen dataclass)."""
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        with pytest.raises(AttributeError):
            # noinspection PyDataclass
            event.stage_name = "Modified"

    @staticmethod
    def test_str_representation() -> None:
        """Should have string representation."""
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            stage_name="Extraction",
            message="Starting extraction",
        )

        result = str(event)

        assert "2024-01-01" in result
        assert "stage_started" in result
        assert "Extraction" in result
        assert "Starting extraction" in result

    @staticmethod
    def test_str_without_optional_fields() -> None:
        """Should handle missing optional fields in string."""
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
        )

        result = str(event)

        assert "pipeline_started" in result


class TestPipelineObserverInterface:
    """Tests for PipelineObserver abstract interface."""

    @staticmethod
    def test_cannot_instantiate_directly() -> None:
        """Should not allow direct instantiation."""
        with pytest.raises(TypeError, match="abstract"):
            # noinspection PyAbstractClass
            PipelineObserver()  # skipcq: PYL-E0110

    @staticmethod
    def test_requires_on_event() -> None:
        """Should require on_event method."""

        class IncompleteObserver(PipelineObserver, ABC):
            """Observer missing on_event."""

        with pytest.raises(TypeError, match="on_event"):
            # noinspection PyAbstractClass
            IncompleteObserver()  # skipcq: PYL-E0110


class ConcreteObserver(PipelineObserver):
    """Concrete observer for testing."""

    def __init__(self) -> None:
        """Initialize observer."""
        self.events: list[PipelineEvent] = []
        self.pipeline_started_called = False
        self.stage_completed_called = False

    def on_event(self, event: PipelineEvent) -> None:
        """Record event."""
        self.events.append(event)

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Handle pipeline started."""
        self.pipeline_started_called = True
        self.on_event(event)

    def on_stage_completed(self, event: PipelineEvent) -> None:
        """Handle stage completed."""
        self.stage_completed_called = True
        self.on_event(event)


class TestPipelineObserverDefaultMethods:
    """Tests for PipelineObserver default method implementations."""

    @staticmethod
    def test_on_pipeline_started_calls_on_event() -> None:
        """Should call on_event by default."""
        observer = ConcreteObserver()
        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
        )

        observer.on_pipeline_started(event)

        assert len(observer.events) == 1

    @staticmethod
    def test_on_pipeline_completed_calls_on_event() -> None:
        """Should call on_event by default."""

        class MinimalObserver(PipelineObserver):
            """Observer with only on_event."""

            def __init__(self):
                self.events = []

            def on_event(self, _event: PipelineEvent) -> None:
                self.events.append(_event)

        observer = MinimalObserver()
        event = PipelineEvent(
            event_type=EventType.PIPELINE_COMPLETED,
            timestamp=datetime.now(),
        )

        observer.on_pipeline_completed(event)

        assert len(observer.events) == 1

    @staticmethod
    def test_on_stage_started_calls_on_event() -> None:
        """Should call on_event by default."""

        class MinimalObserver(PipelineObserver):
            """Observer with only on_event."""

            def __init__(self):
                self.events = []

            def on_event(self, _event: PipelineEvent) -> None:
                self.events.append(_event)

        observer = MinimalObserver()
        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )

        observer.on_stage_started(event)

        assert len(observer.events) == 1


class TestObservable:
    """Tests for Observable mixin class."""

    @staticmethod
    def test_starts_with_no_observers() -> None:
        """Should start with empty observer list."""
        observable = Observable()

        assert observable._observers == []

    @staticmethod
    def test_attach_adds_observer() -> None:
        """Should add observer to list."""
        observable = Observable()
        observer = ConcreteObserver()

        observable.attach(observer)

        assert len(observable._observers) == 1
        assert observer in observable._observers

    @staticmethod
    def test_attach_prevents_duplicates() -> None:
        """Should not add same observer twice."""
        observable = Observable()
        observer = ConcreteObserver()

        observable.attach(observer)
        observable.attach(observer)

        assert len(observable._observers) == 1

    @staticmethod
    def test_detach_removes_observer() -> None:
        """Should remove observer from list."""
        observable = Observable()
        observer = ConcreteObserver()
        observable.attach(observer)

        observable.detach(observer)

        assert len(observable._observers) == 0

    @staticmethod
    def test_detach_handles_missing_observer() -> None:
        """Should not raise when detaching missing observer."""
        observable = Observable()
        observer = ConcreteObserver()

        # Should not raise
        observable.detach(observer)

    @staticmethod
    def test_notify_calls_all_observers() -> None:
        """Should notify all attached observers."""
        observable = Observable()
        observer1 = ConcreteObserver()
        observer2 = ConcreteObserver()
        observable.attach(observer1)
        observable.attach(observer2)

        event = PipelineEvent(
            event_type=EventType.STAGE_STARTED,
            timestamp=datetime.now(),
        )
        observable.notify(event)

        assert len(observer1.events) == 1
        assert len(observer2.events) == 1

    @staticmethod
    def test_notify_routes_to_specific_handler() -> None:
        """Should route events to specific handlers."""
        observable = Observable()
        observer = ConcreteObserver()
        observable.attach(observer)

        event = PipelineEvent(
            event_type=EventType.PIPELINE_STARTED,
            timestamp=datetime.now(),
        )
        observable.notify(event)

        assert observer.pipeline_started_called

    @staticmethod
    def test_notify_falls_back_to_on_event() -> None:
        """Should fall back to on_event for unknown event types."""
        observable = Observable()
        observer = ConcreteObserver()
        observable.attach(observer)

        event = PipelineEvent(
            event_type=EventType.WARNING,
            timestamp=datetime.now(),
        )
        observable.notify(event)

        assert len(observer.events) == 1


class TestObservableCreateEvent:
    """Tests for Observable.create_event helper method."""

    @staticmethod
    def test_creates_event_with_type() -> None:
        """Should create event with specified type."""
        event = Observable.create_event(EventType.STAGE_STARTED)

        assert event.event_type == EventType.STAGE_STARTED

    @staticmethod
    def test_creates_event_with_timestamp() -> None:
        """Should create event with current timestamp."""
        before = datetime.now()
        event = Observable.create_event(EventType.STAGE_STARTED)
        after = datetime.now()

        assert before <= event.timestamp <= after

    @staticmethod
    def test_creates_event_with_all_fields() -> None:
        """Should create event with all optional fields."""
        error = ValueError("Test error")
        event = Observable.create_event(
            event_type=EventType.ITEM_FAILED,
            stage_name="Extraction",
            item_id="track123",
            message="Processing failed",
            metadata={"key": "value"},
            error=error,
        )

        assert event.stage_name == "Extraction"
        assert event.item_id == "track123"
        assert event.message == "Processing failed"
        assert event.metadata == {"key": "value"}
        assert event.error is error
