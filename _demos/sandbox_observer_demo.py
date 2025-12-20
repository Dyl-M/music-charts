"""Interactive demo for Observer Pattern implementation.

This script demonstrates the Observer Pattern with PipelineObserver, Observable,
and concrete observer implementations (ConsoleObserver, FileObserver, etc.).

Requirements:
    - Creates temporary files in _data/demo/
    - Cleans up after execution

Usage:
    python _demos/sandbox_observer_demo.py
"""

# Standard library
from pathlib import Path

# Local
from msc.pipeline.observer import EventType, Observable, PipelineEvent, PipelineObserver
from msc.pipeline.observers import ConsoleObserver, FileObserver, MetricsObserver


def print_separator(title: str = "") -> None:
    """Print a formatted separator line.

    Args:
        title: Optional title to display in separator.
    """
    if title:
        print(f"\n{'=' * 80}")
        print(f" {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def cleanup_demo_files() -> None:
    """Clean up demo files and directories."""
    demo_dir = Path("_data/demo")
    if demo_dir.exists():
        for file in demo_dir.glob("observer_*.jsonl"):
            file.unlink()
        if not any(demo_dir.iterdir()):
            demo_dir.rmdir()


class SimulatedPipeline(Observable):
    """Simulated pipeline for demonstration purposes."""

    def __init__(self) -> None:
        """Initialize simulated pipeline."""
        super().__init__()

    def run(self, num_items: int = 5) -> None:
        """Simulate pipeline execution.

        Args:
            num_items: Number of items to process
        """
        # Pipeline started
        event = self.create_event(
            EventType.PIPELINE_STARTED,
            message="Starting simulated pipeline",
            metadata={"total_items": num_items},
        )
        self.notify(event)

        # Stage started
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Extraction",
            message=f"Extracting {num_items} items",
            metadata={"total": num_items},
        )
        self.notify(event)

        # Process items
        for i in range(num_items):
            # Item processing
            event = self.create_event(
                EventType.ITEM_PROCESSING,
                stage_name="Extraction",
                item_id=f"item_{i + 1:03d}",
                message=f"Processing item {i + 1}/{num_items}",
            )
            self.notify(event)

            # Item completed (most items)
            if i < num_items - 1:
                event = self.create_event(
                    EventType.ITEM_COMPLETED,
                    stage_name="Extraction",
                    item_id=f"item_{i + 1:03d}",
                    message=f"Completed item {i + 1}",
                )
                self.notify(event)
            else:
                # Simulate one failure
                event = self.create_event(
                    EventType.ITEM_FAILED,
                    stage_name="Extraction",
                    item_id=f"item_{i + 1:03d}",
                    message=f"Failed item {i + 1}",
                    error=ValueError("Simulated error"),
                )
                self.notify(event)

        # Stage completed
        event = self.create_event(
            EventType.STAGE_COMPLETED,
            stage_name="Extraction",
            message="Extraction stage completed",
        )
        self.notify(event)

        # Pipeline completed
        event = self.create_event(
            EventType.PIPELINE_COMPLETED,
            message="Pipeline completed successfully",
        )
        self.notify(event)


class CustomObserver(PipelineObserver):
    """Custom observer for demonstration."""

    def __init__(self) -> None:
        """Initialize custom observer."""
        self.events_seen: list[str] = []

    def on_event(self, event: PipelineEvent) -> None:
        """Handle pipeline event by dispatching to specific handlers."""
        handler_map = {
            EventType.PIPELINE_STARTED: self.on_pipeline_started,
            EventType.PIPELINE_COMPLETED: self.on_pipeline_completed,
            EventType.PIPELINE_FAILED: self.on_pipeline_failed,
            EventType.STAGE_STARTED: self.on_stage_started,
            EventType.STAGE_COMPLETED: self.on_stage_completed,
            EventType.STAGE_FAILED: self.on_stage_failed,
            EventType.ITEM_PROCESSING: self.on_item_processing,
            EventType.ITEM_COMPLETED: self.on_item_completed,
            EventType.ITEM_FAILED: self.on_item_failed,
            EventType.ITEM_SKIPPED: self.on_item_skipped,
        }
        handler = handler_map.get(event.event_type)
        if handler:
            handler(event)

    def on_pipeline_started(self, event: PipelineEvent) -> None:
        """Handle pipeline started event."""
        self.events_seen.append(f"PIPELINE_STARTED: {event.message}")

    def on_pipeline_completed(self, event: PipelineEvent) -> None:
        """Handle pipeline completed event."""
        self.events_seen.append(f"PIPELINE_COMPLETED: {event.message}")

    def on_pipeline_failed(self, event: PipelineEvent) -> None:
        """Handle pipeline failed event."""
        self.events_seen.append(f"PIPELINE_FAILED: {event.message}")

    def on_stage_started(self, event: PipelineEvent) -> None:
        """Handle stage started event."""
        self.events_seen.append(f"STAGE_STARTED: {event.stage_name}")

    def on_stage_completed(self, event: PipelineEvent) -> None:
        """Handle stage completed event."""
        self.events_seen.append(f"STAGE_COMPLETED: {event.stage_name}")

    def on_stage_failed(self, event: PipelineEvent) -> None:
        """Handle stage failed event."""
        self.events_seen.append(f"STAGE_FAILED: {event.stage_name}")

    def on_item_processing(self, event: PipelineEvent) -> None:
        """Handle item processing event."""
        self.events_seen.append(f"ITEM_PROCESSING: {event.item_id}")

    def on_item_completed(self, event: PipelineEvent) -> None:
        """Handle item completed event."""
        self.events_seen.append(f"ITEM_COMPLETED: {event.item_id}")

    def on_item_failed(self, event: PipelineEvent) -> None:
        """Handle item failed event."""
        self.events_seen.append(f"ITEM_FAILED: {event.item_id}")

    def on_item_skipped(self, event: PipelineEvent) -> None:
        """Handle item skipped event."""
        self.events_seen.append(f"ITEM_SKIPPED: {event.item_id}")


def demo_basic_observer() -> None:
    """Demonstrate basic observer functionality."""
    print_separator("Basic Observer Pattern")

    # Create observable and observer
    pipeline = SimulatedPipeline()
    observer = CustomObserver()

    # Attach observer
    pipeline.attach(observer)

    print("Running pipeline with custom observer...")
    print()

    # Run pipeline (silently - observer just collects events)
    pipeline.run(num_items=3)

    # Show collected events
    print("Events received by observer:")
    for event in observer.events_seen:
        print(f"  • {event}")

    print()
    print("✓ Observer received all pipeline events")


def demo_multiple_observers() -> None:
    """Demonstrate multiple observers on same observable."""
    print_separator("Multiple Observers")

    # Create observable
    pipeline = SimulatedPipeline()

    # Create multiple observers
    observer1 = CustomObserver()
    observer2 = CustomObserver()

    # Attach both
    pipeline.attach(observer1)
    pipeline.attach(observer2)

    print("Running pipeline with TWO observers attached...")
    print()

    # Run pipeline
    pipeline.run(num_items=2)

    print(f"Observer 1 received {len(observer1.events_seen)} events")
    print(f"Observer 2 received {len(observer2.events_seen)} events")
    print()

    print("✓ Both observers received the same events")
    print("✓ Observers are independent (decoupled)")


def demo_console_observer() -> None:
    """Demonstrate ConsoleObserver with colored output."""
    print_separator("ConsoleObserver (Colored Output)")

    pipeline = SimulatedPipeline()
    console_observer = ConsoleObserver()

    pipeline.attach(console_observer)

    print("Running pipeline with ConsoleObserver...")
    print("(Note: You should see colored output)")
    print()

    pipeline.run(num_items=3)

    print()
    print("✓ ConsoleObserver provides colored, formatted console output")


def demo_file_observer() -> None:
    """Demonstrate FileObserver with JSONL logging."""
    print_separator("FileObserver (JSONL Event Log)")

    log_path = Path("_data/demo/observer_events.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    pipeline = SimulatedPipeline()
    file_observer = FileObserver(log_path)

    pipeline.attach(file_observer)

    print(f"Running pipeline with FileObserver (logging to {log_path})...")
    print()

    pipeline.run(num_items=3)

    # Read and display log file
    if log_path.exists():
        print(f"\nLog file created: {log_path}")
        print(f"File size: {log_path.stat().st_size} bytes")
        print()

        print("First 5 log entries:")
        with open(log_path, encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if idx <= 5:
                    print(f"  {idx}: {line.strip()[:70]}...")
                else:
                    break

        print()
        print("✓ FileObserver logs all events to JSONL file")
        print("✓ Useful for debugging, auditing, and post-mortem analysis")


def demo_metrics_observer() -> None:
    """Demonstrate MetricsObserver for statistics collection."""
    print_separator("MetricsObserver (Statistics Collection)")

    pipeline = SimulatedPipeline()
    metrics_observer = MetricsObserver()

    pipeline.attach(metrics_observer)

    print("Running pipeline with MetricsObserver...")
    print()

    pipeline.run(num_items=5)

    # Get metrics
    metrics = metrics_observer.get_metrics()

    print("\nCollected Metrics:")
    print(f"  Total events: {metrics.get('total_events', 0)}")
    print()

    print("  Events by type:")
    for event_type, count in sorted(metrics.get("events_by_type", {}).items()):
        print(f"    {event_type}: {count}")

    print()
    print("  Success rate:")
    completed = metrics.get("events_by_type", {}).get("ITEM_COMPLETED", 0)
    failed = metrics.get("events_by_type", {}).get("ITEM_FAILED", 0)
    total = completed + failed
    if total > 0:
        success_rate = (completed / total) * 100
        print(f"    {success_rate:.1f}% ({completed}/{total} items successful)")

    print()
    print("✓ MetricsObserver provides pipeline execution statistics")


def demo_observer_detachment() -> None:
    """Demonstrate observer attachment and detachment."""
    print_separator("Observer Detachment")

    pipeline = SimulatedPipeline()
    observer = CustomObserver()

    # Attach observer
    pipeline.attach(observer)
    print("Observer attached")

    # Run pipeline
    pipeline.run(num_items=2)
    events_before = len(observer.events_seen)
    print(f"Events received: {events_before}")
    print()

    # Detach observer
    pipeline.detach(observer)
    print("Observer detached")

    # Run pipeline again
    pipeline.run(num_items=2)
    events_after = len(observer.events_seen)
    print(f"Events received: {events_after}")
    print()

    print(f"Events before detach: {events_before}")
    print(f"Events after detach: {events_after}")
    print("✓ Observer stopped receiving events after detachment")


def demo_error_handling() -> None:
    """Demonstrate error handling in observers."""
    print_separator("Observer Error Handling")

    class BuggyObserver(PipelineObserver):
        """Observer that raises errors (for testing)."""

        def on_event(self, event: PipelineEvent) -> None:
            """Handle event by calling specific handler."""
            if event.event_type == EventType.PIPELINE_STARTED:
                self.on_pipeline_started(event)

        def on_pipeline_started(self, event: PipelineEvent) -> None:
            """Intentionally raise an error."""
            raise ValueError("Simulated observer error!")

    pipeline = SimulatedPipeline()

    # Attach buggy observer
    buggy_observer = BuggyObserver()
    pipeline.attach(buggy_observer)

    # Also attach working observer
    working_observer = CustomObserver()
    pipeline.attach(working_observer)

    print("Running pipeline with one buggy observer and one working observer...")
    print("(Buggy observer will raise error on first event)")
    print()

    try:
        pipeline.run(num_items=2)
    except Exception as e:
        print(f"Error caught: {type(e).__name__}: {e}")

    print()
    print(f"Working observer still received {len(working_observer.events_seen)} events")
    print()
    print("Note: Current implementation doesn't isolate observer errors")
    print("In production, would wrap each observer call in try/except")


def demo_observer_pattern_benefits() -> None:
    """Demonstrate Observer Pattern benefits."""
    print_separator("Observer Pattern Benefits")

    print("Benefits of Observer Pattern:")
    print()

    print("1. Decoupling:")
    print("   - Pipeline doesn't know about observer implementations")
    print("   - Observers can be added/removed without changing pipeline code")
    print()

    print("2. Extensibility:")
    print("   - Easy to add new observer types (Webhook, Slack, Email)")
    print("   - No modification to existing code (Open/Closed Principle)")
    print()

    print("3. Multiple Listeners:")
    print("   - Multiple observers can react to same events")
    print("   - Console logging + File logging + Metrics collection")
    print()

    print("4. Reusability:")
    print("   - Observers can be reused across different pipelines")
    print("   - Same MetricsObserver for all stages")
    print()

    print("5. Testability:")
    print("   - Easy to test pipeline without observers")
    print("   - Easy to test observers with mock events")


def main() -> None:
    """Run all observer pattern demos."""
    print("=" * 80)
    print(" Observer Pattern - Interactive Demo")
    print("=" * 80)

    # Clean up any existing demo files first
    cleanup_demo_files()

    try:
        demo_basic_observer()
        demo_multiple_observers()
        demo_console_observer()
        demo_file_observer()
        demo_metrics_observer()
        demo_observer_detachment()
        demo_error_handling()
        demo_observer_pattern_benefits()

        print_separator()
        print("✓ All demos completed successfully!")
        print()
        print("Key Takeaways:")
        print("1. Observer Pattern decouples event producers from consumers")
        print("2. Multiple observers can listen to same observable")
        print("3. ConsoleObserver: Colored terminal output")
        print("4. FileObserver: JSONL event logging for auditing")
        print("5. MetricsObserver: Statistics collection")
        print("6. Observers can be attached/detached dynamically")
        print("7. Supports loose coupling and extensibility")
        print()

    finally:
        # Clean up demo files
        cleanup_demo_files()
        print("✓ Demo files cleaned up")


if __name__ == "__main__":
    main()
