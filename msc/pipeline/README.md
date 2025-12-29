# Pipeline Module

ETL pipeline stages with orchestration and observer-based progress tracking.

## Modules

| Module            | Purpose                                              |
|-------------------|------------------------------------------------------|
| `base.py`         | Abstract pipeline stage with ETL pattern             |
| `extract.py`      | Extraction stage: MusicBee → Songstats ID resolution |
| `enrich.py`       | Enrichment stage: Fetch platform statistics          |
| `rank.py`         | Ranking stage: Compute power rankings                |
| `orchestrator.py` | Pipeline coordinator with run management             |
| `observer.py`     | Observer pattern interface and event types           |
| `observers.py`    | Console, file, progress bar, and metrics observers   |

## Pipeline Stages

Each stage follows the ETL pattern: `extract() → transform() → load()`.

```python
from msc.pipeline.extract import ExtractionStage
from msc.pipeline.enrich import EnrichmentStage
from msc.pipeline.rank import RankingStage

# Extraction: MusicBee library → Tracks with Songstats IDs
extraction = ExtractionStage(
    musicbee_client=musicbee_client,
    songstats_client=songstats_client,
    track_repository=track_repo,
    checkpoint_manager=checkpoint_mgr,
)
tracks = extraction.run(playlist_name="DJ Selection 2025")

# Enrichment: Tracks → TrackWithStats (platform statistics)
enrichment = EnrichmentStage(
    songstats_client=songstats_client,
    stats_repository=stats_repo,
    checkpoint_manager=checkpoint_mgr,
    include_youtube=True,
)
enriched = enrichment.run(tracks)

# Ranking: TrackWithStats → PowerRankingResults
ranking = RankingStage(
    scorer=power_ranking_scorer,
    stats_repository=stats_repo,
)
results = ranking.run(enriched)
```

## Pipeline Orchestrator

Coordinates all stages with automatic run management.

```python
from msc.pipeline.orchestrator import PipelineOrchestrator

# Initialize orchestrator
orchestrator = PipelineOrchestrator(
    include_youtube=True,
    verbose=False,
    new_run=True,  # Create new run directory
)

# Run full pipeline
results = orchestrator.run(
    playlist_name="DJ Selection 2025",
    stages=["extract", "enrich", "rank"],  # Or subset
)

# Access results
print(f"Processed {results.total_tracks} tracks")
for ranking in results.rankings[:10]:
    print(f"#{ranking.rank}: {ranking.track.title} ({ranking.final_score:.1f})")

# Resume interrupted pipeline
orchestrator = PipelineOrchestrator(
    new_run=False,  # Resume latest run
)
results = orchestrator.run(playlist_name="DJ Selection 2025")
```

## Observer Pattern

Track progress and events across all stages.

```python
from msc.pipeline.observer import PipelineObserver, EventType, PipelineEvent
from msc.pipeline.observers import (
    ConsoleObserver,
    FileObserver,
    ProgressBarObserver,
    MetricsObserver,
)

# Console observer: prints events to stdout
console = ConsoleObserver(verbose=True)

# File observer: writes events to JSONL file
file_obs = FileObserver(log_path=Path("_data/logs/events.jsonl"))

# Progress bar: Rich progress display
progress = ProgressBarObserver()

# Metrics: collects timing and counts
metrics = MetricsObserver()

# Attach observers to orchestrator
orchestrator.attach(console)
orchestrator.attach(file_obs)
orchestrator.attach(progress)
orchestrator.attach(metrics)

# Run pipeline (observers receive events automatically)
results = orchestrator.run(playlist_name="DJ Selection 2025")

# Get metrics after run
stats = metrics.get_metrics()
print(f"Total duration: {stats['total_duration']:.1f}s")
print(f"Tracks processed: {stats['tracks_processed']}")
print(f"Errors: {stats['error_count']}")
```

## Event Types

```python
from msc.pipeline.observer import EventType

# Available event types
EventType.PIPELINE_START  # Pipeline execution started
EventType.PIPELINE_END  # Pipeline execution completed
EventType.STAGE_START  # Individual stage started
EventType.STAGE_END  # Individual stage completed
EventType.ITEM_PROCESSED  # Single item processed
EventType.ITEM_SKIPPED  # Item skipped (already processed)
EventType.ITEM_FAILED  # Item processing failed
EventType.PROGRESS_UPDATE  # Progress percentage update
EventType.ERROR  # Error occurred
EventType.WARNING  # Warning issued
```

## Custom Observer

```python
from msc.pipeline.observer import PipelineObserver, PipelineEvent


class SlackNotifier(PipelineObserver):
    """Send Slack notifications for pipeline events."""

    def update(self, event: PipelineEvent) -> None:
        if event.event_type == EventType.PIPELINE_END:
            self._send_slack(f"Pipeline completed: {event.data['total_tracks']} tracks")
        elif event.event_type == EventType.ERROR:
            self._send_slack(f"Pipeline error: {event.data['message']}")

    def _send_slack(self, message: str) -> None:
        # Slack API call...
        pass


# Attach custom observer
orchestrator.attach(SlackNotifier())
```

## Manual Songstats ID Addition

When tracks fail automatic matching, you can manually add Songstats IDs to `tracks.json`.
The enrichment stage will automatically repopulate missing metadata fields.

### Process

1. Check `manual_review.json` for unmatched tracks
2. Find the Songstats ID on [songstats.com](https://songstats.com) (from URL: `songstats.com/track/<ID>`)
3. Edit `tracks.json` and add the ID:

```json
{
  "songstats_identifiers": {
    "s_id": "qmr6e0bx",
    "s_title": ""
  }
}
```

4. Run enrichment: `msc run --year 2025 --stage enrich --stage rank`

The enrichment stage will detect the incomplete metadata and automatically fetch:
- `songstats_title` - Track title from Songstats
- `songstats_artists` - Artist names
- `songstats_labels` - Record labels
- `isrc` - International Standard Recording Code

The updated metadata is saved back to `tracks.json`.

## Run Directory Structure

Each pipeline run creates a timestamped directory:

```
_data/runs/2025_20251227_143022/
├── checkpoints/
│   ├── extraction.json
│   ├── enrichment.json
│   └── ranking.json
├── manual_review.json
├── tracks.json
├── stats.json
├── rankings.json
└── events.jsonl
```
