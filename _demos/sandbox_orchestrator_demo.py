"""Interactive demo for PipelineOrchestrator.

This script demonstrates the PipelineOrchestrator which coordinates all pipeline
stages (Extraction, Enrichment, Ranking) and provides a unified interface for
running the complete music-charts pipeline.

IMPORTANT: This is a conceptual demo showing the orchestrator's capabilities.
Running the actual pipeline requires:
  - Valid Songstats API key
  - MusicBee library XML file
  - Proper environment configuration

Requirements:
    - For demo: No requirements (conceptual overview)
    - For real execution: See requirements above

Usage:
    python _demos/sandbox_orchestrator_demo.py
"""


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


def demo_orchestrator_overview() -> None:
    """Demonstrate PipelineOrchestrator overview."""
    print_separator("PipelineOrchestrator Overview")

    print("The PipelineOrchestrator coordinates all pipeline stages:")
    print()

    print("Responsibilities:")
    print("  1. Initialize all clients (MusicBee, Songstats)")
    print("  2. Create repositories (Track, Stats)")
    print("  3. Create checkpoint managers")
    print("  4. Attach observers (Console, File, Progress, Metrics)")
    print("  5. Coordinate stage execution")
    print("  6. Provide metrics and review queue access")
    print()

    print("Benefits:")
    print("  ✓ Single entry point for pipeline execution")
    print("  ✓ Automatic dependency injection")
    print("  ✓ Consistent observer attachment")
    print("  ✓ Centralized configuration")
    print("  ✓ Simplified error handling")


def demo_initialization() -> None:
    """Demonstrate orchestrator initialization."""
    print_separator("Orchestrator Initialization")

    print("Creating PipelineOrchestrator:")
    print()

    print("from msc.pipeline.orchestrator import PipelineOrchestrator")
    print()
    print("# Create orchestrator")
    print("orchestrator = PipelineOrchestrator(")
    print("    year=2025,")
    print("    playlist_name='✅ 2025 Selection',")
    print("    include_youtube=True,")
    print(")")
    print()

    print("What happens during initialization:")
    print("  1. Load settings (from environment or defaults)")
    print("  2. Create clients:")
    print("     • MusicBeeClient(library_path)")
    print("     • SongstatsClient(api_key)")
    print("  3. Create repositories:")
    print("     • JSONTrackRepository(_data/tracks.json)")
    print("     • JSONStatsRepository(_data/stats.json)")
    print("  4. Create checkpoint managers:")
    print("     • CheckpointManager(_data/checkpoints/)")
    print("     • ManualReviewQueue(_data/manual_review.json)")
    print("  5. Create scorer:")
    print("     • PowerRankingScorer(categories.json)")
    print("  6. Attach observers:")
    print("     • ConsoleObserver (colored terminal output)")
    print("     • FileObserver (event log to pipeline_events.jsonl)")
    print("     • ProgressBarObserver (real-time progress bars)")
    print("     • MetricsObserver (execution statistics)")


def demo_running_full_pipeline() -> None:
    """Demonstrate running the full pipeline."""
    print_separator("Running the Full Pipeline")

    print("Execute all three stages:")
    print()

    print("orchestrator.run()")
    print()

    print("This runs:")
    print("  1. ExtractionStage:")
    print("     • Extract tracks from MusicBee")
    print("     • Search Songstats for IDs")
    print("     • Save to track repository")
    print()
    print("  2. EnrichmentStage:")
    print("     • Fetch platform statistics")
    print("     • Fetch historical peaks")
    print("     • Fetch YouTube data (if enabled)")
    print("     • Save to stats repository")
    print()
    print("  3. RankingStage:")
    print("     • Compute power rankings")
    print("     • Export to JSON (nested/flat)")
    print("     • Export to CSV")
    print()

    print("Output:")
    print("  • _data/tracks.json")
    print("  • _data/stats.json")
    print("  • _data/output/power_rankings_2025.json")
    print("  • _data/output/power_rankings_2025_flat.json")
    print("  • _data/output/power_rankings_2025.csv")
    print("  • _data/checkpoints/extraction.json")
    print("  • _data/checkpoints/enrichment.json")
    print("  • _data/checkpoints/ranking.json")
    print("  • _data/pipeline_events.jsonl")
    print("  • _data/manual_review.json (if any failures)")


def demo_running_individual_stages() -> None:
    """Demonstrate running individual stages."""
    print_separator("Running Individual Stages")

    print("Run specific stages only:")
    print()

    print("# Run extraction only")
    print("orchestrator.run(stages=['extract'])")
    print()

    print("# Run enrichment only (requires extracted tracks)")
    print("orchestrator.run(stages=['enrich'])")
    print()

    print("# Run ranking only (requires enriched tracks)")
    print("orchestrator.run(stages=['rank'])")
    print()

    print("# Run extraction + enrichment (skip ranking)")
    print("orchestrator.run(stages=['extract', 'enrich'])")
    print()

    print("Use cases:")
    print("  • Re-run ranking with different category configuration")
    print("  • Re-enrich tracks after fixing manual review items")
    print("  • Test individual stages in development")


def demo_checkpoint_resumability() -> None:
    """Demonstrate checkpoint resumability."""
    print_separator("Checkpoint Resumability")

    print("Scenario: Pipeline crashes during enrichment (track 50/100)")
    print()

    print("1. Initial run:")
    print("   orchestrator.run()")
    print("   → Extraction completes (100 tracks)")
    print("   → Enrichment crashes at track 50")
    print("   → Checkpoint saved with 49 processed tracks")
    print()

    print("2. Restart:")
    print("   orchestrator.run()")
    print("   → Extraction skipped (checkpoint exists, all processed)")
    print("   → Enrichment resumes from track 51")
    print("   → Continues to track 100")
    print("   → Ranking proceeds normally")
    print()

    print("Benefits:")
    print("  ✓ No wasted API calls (expensive Songstats quota)")
    print("  ✓ Can pause/resume multi-hour pipelines")
    print("  ✓ Resilient to network failures")
    print("  ✓ Resilient to API rate limits")


def demo_manual_review_queue() -> None:
    """Demonstrate manual review queue access."""
    print_separator("Manual Review Queue")

    print("After pipeline runs:")
    print()

    print("# Get items needing review")
    print("review_items = orchestrator.get_review_queue()")
    print()
    print("for item in review_items:")
    print("    print(f'{item.title} - {item.artist}')")
    print("    print(f'Reason: {item.reason}')")
    print("    print(f'Metadata: {item.metadata}')")
    print()

    print("Typical reasons for manual review:")
    print("  • No Songstats ID found (track not in database)")
    print("  • Multiple matches (ambiguous search results)")
    print("  • API errors (timeout, rate limit)")
    print()

    print("Resolution workflow:")
    print("  1. User reviews `_data/manual_review.json`")
    print("  2. User manually searches Songstats website")
    print("  3. User adds Songstats ID to track in repository")
    print("  4. User removes item from review queue")
    print("  5. User re-runs enrichment stage")


def demo_execution_metrics() -> None:
    """Demonstrate execution metrics access."""
    print_separator("Execution Metrics")

    print("After pipeline runs:")
    print()

    print("# Get execution metrics")
    print("metrics = orchestrator.get_metrics()")
    print()
    print("print(f'Total events: {metrics[\"total_events\"]}')")
    print("print(f'Items completed: {metrics[\"events_by_type\"][\"ITEM_COMPLETED\"]}')")
    print("print(f'Items failed: {metrics[\"events_by_type\"][\"ITEM_FAILED\"]}')")
    print()

    print("Available metrics:")
    print("  • total_events: Total number of pipeline events")
    print("  • events_by_type: Breakdown by event type")
    print("    - PIPELINE_STARTED, PIPELINE_COMPLETED")
    print("    - STAGE_STARTED, STAGE_COMPLETED, STAGE_FAILED")
    print("    - ITEM_PROCESSING, ITEM_COMPLETED, ITEM_FAILED, ITEM_SKIPPED")
    print("    - CHECKPOINT_SAVED, CHECKPOINT_LOADED")
    print("  • Duration: Time taken for each stage")
    print("  • Success rate: Percentage of successful items")


def demo_observer_output() -> None:
    """Demonstrate observer output."""
    print_separator("Observer Output")

    print("During pipeline execution, observers provide real-time feedback:")
    print()

    print("1. ConsoleObserver (colored terminal output):")
    print("   [INFO] Starting pipeline...")
    print("   [INFO] Stage: Extraction")
    print("   [PROGRESS] Processing track 1/100")
    print("   [SUCCESS] Completed track 1: Levels - Avicii")
    print("   [ERROR] Failed track 2: No Songstats ID found")
    print("   ...")
    print()

    print("2. ProgressBarObserver (real-time progress bars):")
    print("   Extraction  ████████████████░░░░ 80% (80/100)")
    print("   Enrichment  ░░░░░░░░░░░░░░░░░░░░ 0% (0/80)")
    print("   Ranking     ░░░░░░░░░░░░░░░░░░░░ 0% (0/0)")
    print()

    print("3. FileObserver (JSONL event log):")
    print("   _data/pipeline_events.jsonl")
    print("   → Append-only log for auditing")
    print("   → One JSON object per line")
    print("   → Can be analyzed with jq, pandas, etc.")
    print()

    print("4. MetricsObserver (statistics collection):")
    print("   → Counts events by type")
    print("   → Calculates success rates")
    print("   → Measures stage durations")


def demo_pipeline_reset() -> None:
    """Demonstrate pipeline reset functionality."""
    print_separator("Pipeline Reset")

    print("Clear all checkpoints and start fresh:")
    print()

    print("# Clear checkpoints only")
    print("orchestrator.clear_checkpoints()")
    print("→ Removes all checkpoint files")
    print("→ Next run processes all items from scratch")
    print()

    print("# Full reset (dangerous!)")
    print("orchestrator.reset_pipeline()")
    print("→ Clears checkpoints")
    print("→ Clears repositories")
    print("→ Clears manual review queue")
    print("→ Completely fresh state")
    print()

    print("When to use:")
    print("  • Category configuration changed (re-ranking needed)")
    print("  • Data quality issues (want to re-fetch all)")
    print("  • Testing with fresh state")
    print()

    print("⚠️  Warning: reset_pipeline() deletes ALL data!")


def demo_cli_integration() -> None:
    """Demonstrate CLI integration."""
    print_separator("CLI Integration")

    print("The orchestrator powers the `msc run` CLI command:")
    print()

    print("# Run full pipeline")
    print("$ msc run --year 2025")
    print()

    print("# Run specific stages")
    print("$ msc run --year 2025 --stage extract")
    print("$ msc run --year 2025 --stage enrich")
    print("$ msc run --year 2025 --stage rank")
    print()

    print("# Skip YouTube data (faster)")
    print("$ msc run --year 2025 --no-youtube")
    print()

    print("# Reset and start fresh")
    print("$ msc run --year 2025 --reset")
    print()

    print("# Custom playlist")
    print("$ msc run --year 2025 --playlist 'My Custom Playlist'")
    print()

    print("Implementation:")
    print("  1. CLI parses arguments")
    print("  2. Creates PipelineOrchestrator with config")
    print("  3. Calls orchestrator.run(stages=...)")
    print("  4. Displays metrics and review queue")
    print("  5. Handles KeyboardInterrupt gracefully")


def main() -> None:
    """Run all pipeline orchestrator demos."""
    print("=" * 80)
    print(" PipelineOrchestrator - Conceptual Demo")
    print("=" * 80)
    print()
    print("NOTE: This is a conceptual demo showing how to use the orchestrator.")
    print("To run the actual pipeline, you need:")
    print("  • Songstats API key (_tokens/songstats_key.txt)")
    print("  • MusicBee library XML (configured in settings)")
    print("  • Proper environment configuration (.env)")
    print()

    demo_orchestrator_overview()
    demo_initialization()
    demo_running_full_pipeline()
    demo_running_individual_stages()
    demo_checkpoint_resumability()
    demo_manual_review_queue()
    demo_execution_metrics()
    demo_observer_output()
    demo_pipeline_reset()
    demo_cli_integration()

    print_separator()
    print("✓ All demos completed successfully!")
    print()
    print("Key Takeaways:")
    print("1. PipelineOrchestrator coordinates all pipeline stages")
    print("2. Automatic dependency injection (clients, repositories, observers)")
    print("3. Run full pipeline or individual stages")
    print("4. Checkpoint resumability for long-running pipelines")
    print("5. Manual review queue for failed items")
    print("6. Execution metrics and progress tracking")
    print("7. Integrated with `msc run` CLI command")
    print()
    print("To run the actual pipeline:")
    print("  1. Configure environment (.env)")
    print("  2. Add Songstats API key (_tokens/songstats_key.txt)")
    print("  3. Run: msc run --year 2025")
    print()


if __name__ == "__main__":
    main()
