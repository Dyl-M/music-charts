"""Concrete observer implementations for pipeline monitoring.

Provides ready-to-use observers for common use cases:
console logging, file logging, progress bars, and metrics collection.
"""

# Standard library
import json
from pathlib import Path
from typing import Any

# Third-party
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
)

# Local
from msc.pipeline.observer import EventType, PipelineEvent, PipelineObserver
from msc.utils.logging import get_logger


class ConsoleObserver(PipelineObserver):
    """Observer that logs events to console using rich.

    Provides colored, formatted console output for pipeline events
    with different styling for different event types.
    """

    # Event type to console style mapping
    _EVENT_STYLES = {
        EventType.PIPELINE_FAILED: "bold red",
        EventType.STAGE_FAILED: "bold red",
        EventType.ERROR: "bold red",
        EventType.ITEM_FAILED: "yellow",
        EventType.WARNING: "yellow",
        EventType.PIPELINE_COMPLETED: "bold green",
        EventType.STAGE_COMPLETED: "bold green",
        EventType.PIPELINE_STARTED: "bold blue",
        EventType.STAGE_STARTED: "bold blue",
    }

    def __init__(self, verbose: bool = False) -> None:
        """Initialize console observer.

        Args:
            verbose: If True, log all events; if False, only important events
        """
        self.verbose = verbose
        self.console = Console()
        self.logger = get_logger(__name__)

    def on_event(self, event: PipelineEvent) -> None:
        """Handle any pipeline event by logging to console."""
        # Skip verbose events if not in verbose mode
        if not self.verbose and event.event_type in {
            EventType.ITEM_PROCESSING,
            EventType.CHECKPOINT_SAVED,
        }:
            return

        # Get style from mapping (default: "dim")
        style = self._EVENT_STYLES.get(event.event_type, "dim")
        self.console.print(f"{event}", style=style)


class FileObserver(PipelineObserver):
    """Observer that logs events to a JSON file.

    Maintains a structured log of all pipeline events for
    debugging, auditing, and analysis.
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize file observer.

        Args:
            file_path: Path to event log file
        """
        self.file_path = file_path
        self.logger = get_logger(__name__)
        self.events: list[dict[str, Any]] = []

        # Create parent directory if needed
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def on_event(self, event: PipelineEvent) -> None:
        """Handle event by appending to log file."""
        event_dict = {
            "event_type": event.event_type.value,
            "timestamp": event.timestamp.isoformat(),
            "stage_name": event.stage_name,
            "item_id": event.item_id,
            "message": event.message,
            "metadata": event.metadata
        }

        if event.error:
            event_dict["error"] = {
                "type": type(event.error).__name__,
                "message": str(event.error)
            }

        self.events.append(event_dict)

        # Append to file immediately for real-time logging
        try:
            with open(self.file_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_dict, ensure_ascii=False) + "\n")

        except OSError as error:
            self.logger.exception("Failed to write event to log file: %s", error)

    def get_events(self) -> list[dict[str, Any]]:
        """Get all logged events.

        Returns:
            List of event dictionaries
        """
        return self.events.copy()


class ProgressBarObserver(PipelineObserver):
    """Observer that displays a rich progress bar.

    Shows real-time progress for pipeline execution with
    item counts, elapsed time, and current operation.
    """

    def __init__(self) -> None:
        """Initialize progress bar observer."""
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=Console(),
        )
        self.tasks: dict[str, TaskID] = {}
        self.started = False

    def on_event(self, event: PipelineEvent) -> None:
        """Handle events without specific handlers (no-op for progress bar).

        Args:
            event: Pipeline event to handle
        """
        # No action needed - all relevant events have specific handlers
        ...

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Start the progress display."""
        if not self.started:
            self.progress.start()
            self.started = True

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """Stop the progress display."""
        if self.started:
            self.progress.stop()
            self.started = False

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """Stop the progress display on failure."""
        if self.started:
            self.progress.stop()
            self.started = False

    def on_stage_started(self, event: PipelineEvent) -> None:
        """Create a progress bar for the stage."""
        if event.stage_name and event.metadata and "total" in event.metadata:
            task_id = self.progress.add_task(
                f"[cyan]{event.stage_name}", total=event.metadata["total"]
            )
            self.tasks[event.stage_name] = task_id

    def on_stage_completed(self, event: PipelineEvent) -> None:
        """Complete the progress bar for the stage."""
        if event.stage_name and event.stage_name in self.tasks:
            task_id = self.tasks[event.stage_name]

            # Find the task by ID in the tasks sequence
            task = next((t for t in self.progress.tasks if t.id == task_id), None)

            if task and task.total is not None:
                self.progress.update(task_id, completed=task.total)

    def on_item_completed(self, event: PipelineEvent) -> None:
        """Advance the progress bar."""
        if event.stage_name and event.stage_name in self.tasks:
            task_id = self.tasks[event.stage_name]
            self.progress.advance(task_id, 1)

    def on_item_failed(self, event: PipelineEvent) -> None:
        """Advance the progress bar (count failed items too)."""
        if event.stage_name and event.stage_name in self.tasks:
            task_id = self.tasks[event.stage_name]
            self.progress.advance(task_id, 1)

    def close(self) -> None:
        """Clean up progress bar resources.

        Should be called when the observer is no longer needed
        to ensure proper cleanup of terminal resources.
        """
        if self.started:
            self.progress.stop()
            self.started = False

    def __enter__(self) -> "ProgressBarObserver":
        """Enter context manager.

        Returns:
            Self for context manager protocol
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager and clean up resources.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        self.close()

    def __del__(self) -> None:
        """Cleanup when object is garbage collected."""
        self.close()

    def on_item_skipped(self, event: PipelineEvent) -> None:
        """Advance the progress bar (count skipped items too)."""
        if event.stage_name and event.stage_name in self.tasks:
            task_id = self.tasks[event.stage_name]
            self.progress.advance(task_id, 1)


class MetricsObserver(PipelineObserver):
    """Observer that collects pipeline execution metrics.

    Tracks counts, timing, success/failure rates for analysis
    and monitoring.
    """

    def __init__(self) -> None:
        """Initialize metrics observer."""
        self.metrics: dict[str, Any] = {
            "items_processed": 0,
            "items_failed": 0,
            "items_skipped": 0,
            "stages_completed": 0,
            "stages_failed": 0,
            "events_by_type": {}
        }

    def on_event(self, event: PipelineEvent) -> None:
        """Collect metrics for the event."""
        # Count events by type
        event_name = event.event_type.value
        self.metrics["events_by_type"][event_name] = (
                self.metrics["events_by_type"].get(event_name, 0) + 1
        )

    def on_item_completed(self, event: PipelineEvent) -> None:
        """Increment processed item count."""
        self.metrics["items_processed"] += 1
        self.on_event(event)

    def on_item_failed(self, event: PipelineEvent) -> None:
        """Increment failed item count."""
        self.metrics["items_failed"] += 1
        self.on_event(event)

    def on_item_skipped(self, event: PipelineEvent) -> None:
        """Increment skipped item count."""
        self.metrics["items_skipped"] += 1
        self.on_event(event)

    def on_stage_completed(self, event: PipelineEvent) -> None:
        """Increment completed stage count."""
        self.metrics["stages_completed"] += 1
        self.on_event(event)

    def on_stage_failed(self, event: PipelineEvent) -> None:
        """Increment failed stage count."""
        self.metrics["stages_failed"] += 1
        self.on_event(event)

    def get_metrics(self) -> dict[str, Any]:
        """Get collected metrics.

        Returns:
            Dictionary of metrics
        """
        return self.metrics.copy()

    def get_success_rate(self) -> float:
        """Calculate success rate for processed items.

        Returns:
            Success rate as a percentage (0-100)
        """
        total = self.metrics["items_processed"] + self.metrics["items_failed"]
        if total == 0:
            return 0.0
        return (self.metrics["items_processed"] / total) * 100
