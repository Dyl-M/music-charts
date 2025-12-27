# Storage Module

Data persistence with repository pattern, checkpointing, and manual review queues.

## Modules

| Module               | Purpose                                            |
|----------------------|----------------------------------------------------|
| `repository.py`      | Abstract repository interface                      |
| `json_repository.py` | JSON file-based track and stats repositories       |
| `checkpoint.py`      | Pipeline state persistence and manual review queue |

## Repository Pattern

Abstract interface for data access, decoupling storage from business logic.

```python
from msc.storage.json_repository import JSONTrackRepository, JSONStatsRepository
from pathlib import Path

# Track repository (stores Track models)
track_repo = JSONTrackRepository(file_path=Path("_data/output/2025/tracks.json"))

# Save tracks
tracks = [track1, track2, track3]
track_repo.save_all(tracks)

# Load tracks
loaded = track_repo.get_all()

# Get by identifier
track = track_repo.get_by_id("a1b2c3d4")

# Stats repository (stores TrackWithStats models)
stats_repo = JSONStatsRepository(file_path=Path("_data/output/2025/stats.json"))

# Same interface
stats_repo.save_all(enriched_tracks)
all_stats = stats_repo.get_all()
```

## Checkpoint Manager

Enables pipeline resumability by tracking processed items.

```python
from msc.storage.checkpoint import CheckpointManager, CheckpointState
from pathlib import Path

# Initialize with checkpoint directory
manager = CheckpointManager(checkpoint_dir=Path("_data/runs/2025_123456/checkpoints"))

# Create or load checkpoint for a stage
state = manager.get_or_create("extraction")

# Mark items as processed
state.processed_ids.add("track_id_1")
state.processed_ids.add("track_id_2")

# Mark failures
state.failed_ids.add("track_id_3")

# Save checkpoint
manager.save(state)

# Resume later - skip already processed items
state = manager.get_or_create("extraction")
for track in tracks:
    if track.identifier in state.processed_ids:
        continue  # Skip already processed

    # Process track...
    state.processed_ids.add(track.identifier)
    manager.save(state)  # Save after each item for safety

# Check progress
print(f"Processed: {len(state.processed_ids)}")
print(f"Failed: {len(state.failed_ids)}")
```

## Manual Review Queue

Collects items that require human intervention (e.g., unmatched tracks).

```python
from msc.storage.checkpoint import ManualReviewQueue, ReviewItem
from pathlib import Path

# Initialize queue
queue = ManualReviewQueue(file_path=Path("_data/runs/2025_123456/manual_review.json"))

# Add item for review
item = ReviewItem(
    track_id="a1b2c3d4",
    track_info={"title": "Unknown Track", "artist": "Unknown Artist"},
    reason="No Songstats match found",
    stage="extraction",
    search_query="unknown artist unknown track",
)
queue.add(item)

# Automatic deduplication - won't add duplicate track_id
queue.add(item)  # Ignored if already exists

# Get all items pending review
pending = queue.get_pending()
for item in pending:
    print(f"{item.track_info['artist']} - {item.track_info['title']}")
    print(f"  Reason: {item.reason}")
    print(f"  Query: {item.search_query}")

# Mark as resolved
queue.resolve(track_id="a1b2c3d4", resolution="Manually matched to ID xyz123")

# Save queue
queue.save()

# Statistics
print(f"Pending: {queue.pending_count}")
print(f"Resolved: {queue.resolved_count}")
```

## File Structure

Typical run directory structure:

```
_data/runs/2025_20251227_123456/
├── checkpoints/
│   ├── extraction.json     # Extraction stage state
│   ├── enrichment.json     # Enrichment stage state
│   └── ranking.json        # Ranking stage state
├── manual_review.json      # Items needing human review
├── tracks.json             # Extracted tracks
├── stats.json              # Enriched tracks with stats
└── rankings.json           # Final power rankings
```

## Repository Interface

Custom repositories must implement:

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    @abstractmethod
    def get_all(self) -> list[T]: ...

    @abstractmethod
    def get_by_id(self, item_id: str) -> T | None: ...

    @abstractmethod
    def save_all(self, items: list[T]) -> None: ...

    @abstractmethod
    def exists(self) -> bool: ...
```
