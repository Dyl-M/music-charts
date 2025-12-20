"""Observer pattern for pipeline progress tracking.

Implements the Observer pattern to decouple progress tracking
from pipeline logic. Allows multiple observers (console, file,
metrics) to monitor pipeline execution without modification.
"""

# Standard library
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """Types of pipeline events that can be observed."""

    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"

    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    STAGE_FAILED = "stage_failed"

    ITEM_PROCESSING = "item_processing"
    ITEM_COMPLETED = "item_completed"
    ITEM_FAILED = "item_failed"
    ITEM_SKIPPED = "item_skipped"

    CHECKPOINT_SAVED = "checkpoint_saved"
    CHECKPOINT_LOADED = "checkpoint_loaded"

    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True)
class PipelineEvent:
    """Immutable event object for pipeline notifications.

    Contains all information about what happened during
    pipeline execution, passed to observers.
    """

    event_type: EventType
    timestamp: datetime
    stage_name: str | None = None
    item_id: str | None = None
    message: str | None = None
    metadata: dict[str, Any] | None = None
    error: Exception | None = None

    def __str__(self) -> str:
        """Get string representation of event."""
        parts = [
            f"[{self.timestamp.isoformat()}]",
            self.event_type.value,
            f"stage={self.stage_name}" if self.stage_name else None,
            f"item={self.item_id}" if self.item_id else None,
            self.message
        ]

        return " ".join(filter(None, parts))


class PipelineObserver(ABC):
    """Abstract observer for pipeline events.

    Observers receive notifications about pipeline execution
    and can react to events (log, display progress, collect metrics, etc.).
    """

    @abstractmethod
    def on_event(self, event: PipelineEvent) -> None:
        """Handle a pipeline event.

        Args:
            event: The event that occurred
        """
        ...

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Handle pipeline start event (optional override).

        Args:
            event: Pipeline started event
        """
        self.on_event(event)

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """Handle pipeline completion event (optional override).

        Args:
            event: Pipeline completed event
        """
        self.on_event(event)

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """Handle pipeline failure event (optional override).

        Args:
            event: Pipeline failed event
        """
        self.on_event(event)

    def on_stage_started(self, event: PipelineEvent) -> None:
        """Handle stage start event (optional override).

        Args:
            event: Stage started event
        """
        self.on_event(event)

    def on_stage_completed(self, event: PipelineEvent) -> None:
        """Handle stage completion event (optional override).

        Args:
            event: Stage completed event
        """
        self.on_event(event)

    def on_stage_failed(self, event: PipelineEvent) -> None:
        """Handle stage failure event (optional override).

        Args:
            event: Stage failed event
        """
        self.on_event(event)

    def on_item_processing(self, event: PipelineEvent) -> None:
        """Handle item processing event (optional override).

        Args:
            event: Item processing event
        """
        self.on_event(event)

    def on_item_completed(self, event: PipelineEvent) -> None:
        """Handle item completion event (optional override).

        Args:
            event: Item completed event
        """
        self.on_event(event)

    def on_item_failed(self, event: PipelineEvent) -> None:
        """Handle item failure event (optional override).

        Args:
            event: Item failed event
        """
        self.on_event(event)

    def on_item_skipped(self, event: PipelineEvent) -> None:
        """Handle item skipped event (optional override).

        Args:
            event: Item skipped event
        """
        self.on_event(event)


class Observable:
    """Mixin class for objects that can be observed.

    Provides attach/detach/notify methods for managing observers.
    Pipeline stages and orchestrators should inherit from this.
    """

    def __init__(self) -> None:
        """Initialize the observable with empty observer list."""
        self._observers: list[PipelineObserver] = []

    def attach(self, observer: PipelineObserver) -> None:
        """Attach an observer to receive event notifications.

        Args:
            observer: Observer to attach
        """
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer: PipelineObserver) -> None:
        """Detach an observer from receiving notifications.

        Args:
            observer: Observer to detach
        """
        if observer in self._observers:
            self._observers.remove(observer)

    # Event type to handler method mapping
    _EVENT_HANDLERS = {
        EventType.PIPELINE_STARTED: "on_pipeline_started",
        EventType.PIPELINE_COMPLETED: "on_pipeline_completed",
        EventType.PIPELINE_FAILED: "on_pipeline_failed",
        EventType.STAGE_STARTED: "on_stage_started",
        EventType.STAGE_COMPLETED: "on_stage_completed",
        EventType.STAGE_FAILED: "on_stage_failed",
        EventType.ITEM_PROCESSING: "on_item_processing",
        EventType.ITEM_COMPLETED: "on_item_completed",
        EventType.ITEM_FAILED: "on_item_failed",
        EventType.ITEM_SKIPPED: "on_item_skipped"
    }

    def notify(self, event: PipelineEvent) -> None:
        """Notify all observers of an event.

        Args:
            event: Event to broadcast to observers
        """
        # Get handler method name for this event type
        handler_name = self._EVENT_HANDLERS.get(event.event_type)

        for observer in self._observers:
            if handler_name:
                # Route to specific handler
                handler = getattr(observer, handler_name)
                handler(event)

            else:
                # Fallback for events without specific handlers
                observer.on_event(event)

    @staticmethod
    def create_event(
            event_type: EventType,
            stage_name: str | None = None,
            item_id: str | None = None,
            message: str | None = None,
            metadata: dict[str, Any] | None = None,
            error: Exception | None = None,
    ) -> PipelineEvent:
        """Create and return a pipeline event (helper method).

        Args:
            event_type: Type of event
            stage_name: Name of pipeline stage (optional)
            item_id: Identifier of item being processed (optional)
            message: Human-readable message (optional)
            metadata: Additional event data (optional)
            error: Exception if event is error-related (optional)

        Returns:
            Created PipelineEvent
        """
        return PipelineEvent(
            event_type=event_type,
            timestamp=datetime.now(),
            stage_name=stage_name,
            item_id=item_id,
            message=message,
            metadata=metadata,
            error=error
        )
