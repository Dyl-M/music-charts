"""Interactive demo for Checkpoint Pattern implementation.

This script demonstrates the CheckpointManager and ManualReviewQueue, showing
how to create resumable pipelines with checkpoint state management and manual
intervention workflows.

Requirements:
    - Creates temporary files in _data/demo/
    - Cleans up after execution

Usage:
    python _demos/sandbox_checkpoint_demo.py
"""

# Standard library
from datetime import datetime
from pathlib import Path

# Local
from msc.storage.checkpoint import CheckpointManager, ManualReviewQueue


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
        for file in demo_dir.glob("checkpoint_*.json"):
            file.unlink()
        for file in demo_dir.glob("manual_review*.json"):
            file.unlink()
        if not any(demo_dir.iterdir()):
            demo_dir.rmdir()


def demo_checkpoint_creation() -> None:
    """Demonstrate checkpoint creation and state."""
    print_separator("Checkpoint Creation")

    checkpoint_dir = Path("_data/demo")
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    manager = CheckpointManager(checkpoint_dir)

    # Create a new checkpoint
    checkpoint = manager.create_checkpoint(
        stage_name="extraction",
        metadata={
            "year": 2025,
            "playlist": "Electronic Music",
            "started_at": datetime.now().isoformat(),
        },
    )

    print("Created new checkpoint:")
    print(f"  Stage: {checkpoint.stage_name}")
    print(f"  Created: {checkpoint.created_at}")
    print(f"  Processed: {len(checkpoint.processed_ids)} items")
    print(f"  Failed: {len(checkpoint.failed_ids)} items")
    print(f"  Skipped: {len(checkpoint.skipped_ids)} items")
    print(f"  Metadata: {checkpoint.metadata}")
    print()

    print("✓ Checkpoint created successfully!")


def demo_checkpoint_operations() -> None:
    """Demonstrate checkpoint state operations."""
    print_separator("Checkpoint State Operations")

    checkpoint_dir = Path("_data/demo")
    manager = CheckpointManager(checkpoint_dir)

    # Create checkpoint
    checkpoint = manager.create_checkpoint("enrichment")

    print("Starting with empty checkpoint...")
    print(f"  Processed: {len(checkpoint.processed_ids)}")
    print()

    # Mark items as processed (modify set directly)
    checkpoint.processed_ids.add("track_001")
    checkpoint.processed_ids.add("track_002")
    checkpoint.processed_ids.add("track_003")

    print("Marked 3 items as processed")
    print(f"  Processed IDs: {sorted(checkpoint.processed_ids)}")
    print()

    # Mark item as failed (modify set directly)
    checkpoint.failed_ids.add("track_004")

    print("Marked 1 item as failed")
    print(f"  Failed IDs: {sorted(checkpoint.failed_ids)}")
    print()

    # Mark item as skipped (modify set directly)
    checkpoint.skipped_ids.add("track_005")

    print("Marked 1 item as skipped")
    print(f"  Skipped IDs: {sorted(checkpoint.skipped_ids)}")
    print()

    # Save checkpoint
    manager.save_checkpoint(checkpoint)

    print("✓ Checkpoint saved with current state")


def demo_checkpoint_resumability() -> None:
    """Demonstrate pipeline resumability with checkpoints."""
    print_separator("Pipeline Resumability")

    checkpoint_dir = Path("_data/demo")
    manager = CheckpointManager(checkpoint_dir)

    # Simulate pipeline interruption
    print("Scenario: Pipeline processing 10 tracks, interrupted at track 6")
    print()

    # Create checkpoint
    checkpoint = manager.create_checkpoint(
        "ranking",
        metadata={"total_tracks": 10},
    )

    # Process tracks 1-5
    for i in range(1, 6):
        track_id = f"track_{i:03d}"
        checkpoint.processed_ids.add(track_id)
        print(f"  Processed: {track_id}")

    manager.save_checkpoint(checkpoint)
    print()
    print("Pipeline interrupted! Checkpoint saved at track 5")
    print()

    # Simulate pipeline restart
    print("Restarting pipeline...")
    loaded_checkpoint = manager.load_checkpoint("ranking")

    if loaded_checkpoint:
        print(f"  Checkpoint loaded: {len(loaded_checkpoint.processed_ids)} already processed")
        print()

        # Continue from track 6
        remaining_tracks = [f"track_{i:03d}" for i in range(1, 11)]
        to_process = [
            tid for tid in remaining_tracks if tid not in loaded_checkpoint.processed_ids
        ]

        print(f"Resuming with {len(to_process)} remaining tracks:")
        for track_id in to_process:
            loaded_checkpoint.processed_ids.add(track_id)
            print(f"  Processed: {track_id}")

        manager.save_checkpoint(loaded_checkpoint)
        print()
        print("✓ Pipeline completed after resuming from checkpoint!")
        print(f"  Total processed: {len(loaded_checkpoint.processed_ids)}/10")


def demo_checkpoint_metadata() -> None:
    """Demonstrate checkpoint metadata usage."""
    print_separator("Checkpoint Metadata")

    checkpoint_dir = Path("_data/demo")
    manager = CheckpointManager(checkpoint_dir)

    # Create checkpoint with rich metadata
    checkpoint = manager.create_checkpoint(
        "extraction",
        metadata={
            "config": {
                "year": 2025,
                "playlist_name": "Electronic Hits",
                "api_version": "v1",
            },
            "stats": {
                "api_calls": 0,
                "rate_limit_hits": 0,
            },
            "started_at": datetime.now().isoformat(),
        },
    )

    print("Checkpoint with metadata:")
    print(f"  Stage: {checkpoint.stage_name}")
    print("  Metadata:")
    for key, value in checkpoint.metadata.items():
        print(f"    {key}: {value}")
    print()

    # Update metadata during processing
    checkpoint.metadata["stats"]["api_calls"] = 42
    checkpoint.metadata["stats"]["rate_limit_hits"] = 2
    checkpoint.metadata["last_updated"] = datetime.now().isoformat()

    manager.save_checkpoint(checkpoint)

    # Load and verify
    loaded = manager.load_checkpoint("extraction")
    if loaded:
        print("Loaded checkpoint metadata:")
        print(f"  API calls: {loaded.metadata.get('stats', {}).get('api_calls')}")
        print(f"  Rate limit hits: {loaded.metadata.get('stats', {}).get('rate_limit_hits')}")

    print()
    print("✓ Metadata can store arbitrary configuration and statistics")


def demo_manual_review_queue() -> None:
    """Demonstrate manual review queue functionality."""
    print_separator("Manual Review Queue")

    queue_path = Path("_data/demo/manual_review_demo.json")
    queue = ManualReviewQueue(queue_path)

    print("Manual Review Queue: Handle items that need human intervention")
    print()

    # Add items that need review (using queue.add() method)
    items_to_add = [
        {
            "track_id": "ambiguous_track_001",
            "title": "Levels",
            "artist": "Avicii",
            "reason": "Multiple matches in Songstats (3 results)",
            "metadata": {"query": "avicii levels", "match_count": 3},
        },
        {
            "track_id": "missing_track_002",
            "title": "Unreleased Demo",
            "artist": "Unknown Producer",
            "reason": "No Songstats ID found",
            "metadata": {"query": "unknown producer unreleased demo"},
        },
        {
            "track_id": "error_track_003",
            "title": "API Timeout",
            "artist": "Test Artist",
            "reason": "Songstats API timeout (3 retries failed)",
            "metadata": {"error": "RequestTimeout", "retries": 3},
        },
    ]

    for item_data in items_to_add:
        queue.add(**item_data)
        print(f"Added to queue: {item_data['track_id']}")
        print(f"  Title: {item_data['title']} - {item_data['artist']}")
        print(f"  Reason: {item_data['reason']}")
        print()

    # Get all items
    all_items = queue.get_all()
    print(f"✓ Manual review queue contains {len(all_items)} items")
    print()

    # Get specific item by finding in list
    all_items_check = queue.get_all()
    item = next((i for i in all_items_check if i.track_id == "ambiguous_track_001"), None)
    if item:
        print("Retrieved specific item:")
        print(f"  Track: {item.title} - {item.artist}")
        print(f"  Reason: {item.reason}")
        print(f"  Timestamp: {item.timestamp}")
    print()

    # Remove resolved item
    queue.remove("ambiguous_track_001")
    print("✓ Removed resolved item from queue")
    print(f"  Remaining: {len(queue.get_all())} items")


def demo_manual_review_workflow() -> None:
    """Demonstrate complete manual review workflow."""
    print_separator("Manual Review Workflow")

    queue_path = Path("_data/demo/manual_review_workflow.json")
    queue = ManualReviewQueue(queue_path)

    print("Complete workflow: Track fails → Manual review → Resolution")
    print()

    # Step 1: Track fails during pipeline
    print("1. Pipeline encounters problematic track:")
    track_id = "review_track_001"
    queue.add(
        track_id=track_id,
        title="Test Track",
        artist="Test Artist",
        reason="Ambiguous Songstats search results",
        metadata={"candidates": ["id_123", "id_456", "id_789"]},
    )
    print(f"   Added to manual review queue: {track_id}")
    print()

    # Step 2: User reviews queue
    print("2. User reviews queue (simulated):")
    all_items = queue.get_all()
    for idx, review_item in enumerate(all_items, 1):
        print(f"   [{idx}] {review_item.title} - {review_item.artist}")
        print(f"       Reason: {review_item.reason}")
        print(f"       Added: {review_item.timestamp}")
    print()

    # Step 3: User resolves issue manually
    print("3. User manually resolves issue:")
    print("   → Searches Songstats manually")
    print("   → Finds correct ID: id_456")
    print("   → Updates track in repository")
    print()

    # Step 4: Remove from queue
    print("4. Remove resolved item from queue:")
    queue.remove(track_id)
    print(f"   ✓ Removed {track_id}")
    print(f"   Remaining items: {len(queue.get_all())}")
    print()

    print("✓ Manual review workflow complete!")


def demo_checkpoint_race_condition() -> None:
    """Demonstrate checkpoint/repository race condition handling."""
    print_separator("Checkpoint/Repository Synchronization")

    checkpoint_dir = Path("_data/demo")
    manager = CheckpointManager(checkpoint_dir)

    print("Scenario: Track in checkpoint but missing from repository")
    print()

    # Create checkpoint with processed items
    checkpoint = manager.create_checkpoint("enrichment")
    checkpoint.processed_ids.add("track_001")
    checkpoint.processed_ids.add("track_002")  # This one will be "lost"
    checkpoint.processed_ids.add("track_003")

    manager.save_checkpoint(checkpoint)
    print("Checkpoint saved with 3 processed tracks")
    print()

    # Simulate: track_002 is in checkpoint but not in repository
    print("Loading checkpoint...")
    loaded = manager.load_checkpoint("enrichment")

    if loaded:
        # Check if track is in checkpoint
        track_id = "track_002"
        if track_id in loaded.processed_ids:
            print(f"  {track_id} found in checkpoint")

            # Simulate: not found in repository (would check repo.get(track_id))
            in_repository = False  # Simulated

            if not in_repository:
                print(f"  ✗ {track_id} NOT found in repository!")
                print("  → Removing from checkpoint, will reprocess")

                loaded.processed_ids.remove(track_id)
                manager.save_checkpoint(loaded)

                print(f"  ✓ Checkpoint updated, {track_id} will be reprocessed")

    print()
    print("✓ Race condition handled gracefully")
    print("  This prevents silent data loss when repository/checkpoint drift")


def demo_checkpoint_clear() -> None:
    """Demonstrate checkpoint clearing."""
    print_separator("Checkpoint Clearing")

    checkpoint_dir = Path("_data/demo")
    manager = CheckpointManager(checkpoint_dir)

    # Create multiple checkpoints
    stages = ["extraction", "enrichment", "ranking"]
    for stage in stages:
        checkpoint = manager.create_checkpoint(stage)
        checkpoint.processed_ids.add(f"{stage}_item_1")
        manager.save_checkpoint(checkpoint)

    print(f"Created checkpoints for {len(stages)} stages")
    print()

    # Clear specific checkpoint
    manager.clear_checkpoint("extraction")
    print("✓ Cleared 'extraction' checkpoint")

    loaded = manager.load_checkpoint("extraction")
    print(f"  Load result: {loaded}")
    print()

    # Clear all checkpoints (call clear_checkpoint for each stage)
    for stage in stages:
        manager.clear_checkpoint(stage)
    print("✓ Cleared ALL checkpoints")

    for stage in stages:
        loaded = manager.load_checkpoint(stage)
        print(f"  {stage}: {loaded}")

    print()
    print("Clearing is useful for:")
    print("  • Starting pipeline from scratch")
    print("  • Resetting after configuration changes")
    print("  • Testing pipeline with fresh state")


def main() -> None:
    """Run all checkpoint and manual review demos."""
    print("=" * 80)
    print(" Checkpoint Pattern & Manual Review - Interactive Demo")
    print("=" * 80)

    # Clean up any existing demo files first
    cleanup_demo_files()

    try:
        demo_checkpoint_creation()
        demo_checkpoint_operations()
        demo_checkpoint_resumability()
        demo_checkpoint_metadata()
        demo_manual_review_queue()
        demo_manual_review_workflow()
        demo_checkpoint_race_condition()
        demo_checkpoint_clear()

        print_separator()
        print("✓ All demos completed successfully!")
        print()
        print("Key Takeaways:")
        print("1. Checkpoints enable resumable pipelines (save/restore state)")
        print("2. Track processed/failed/skipped items separately")
        print("3. Metadata stores arbitrary pipeline configuration")
        print("4. Manual review queue handles items needing intervention")
        print("5. Checkpoint/repository synchronization prevents data loss")
        print("6. Clean architecture separates state management from business logic")
        print()

    finally:
        # Clean up demo files
        cleanup_demo_files()
        print("✓ Demo files cleaned up")


if __name__ == "__main__":
    main()
