"""Data persistence modules.

Exports:
    Repository pattern:
        - Repository: Abstract base repository
        - TrackRepository: Repository for Track objects
        - StatsRepository: Repository for TrackWithStats objects
        - JSONTrackRepository: JSON-based track storage
        - JSONStatsRepository: JSON-based stats storage

    Checkpoint management:
        - CheckpointState: Represents pipeline checkpoint state
        - CheckpointManager: Manages checkpoint persistence
        - ManualReviewItem: Item requiring manual review
        - ManualReviewQueue: Queue for manual review items
"""

# Local
from msc.storage.checkpoint import (
    CheckpointManager,
    CheckpointState,
    ManualReviewItem,
    ManualReviewQueue,
)
from msc.storage.json_repository import JSONStatsRepository, JSONTrackRepository
from msc.storage.repository import Repository, StatsRepository, TrackRepository

__all__ = [
    # Repository pattern
    "Repository",
    "TrackRepository",
    "StatsRepository",
    "JSONTrackRepository",
    "JSONStatsRepository",
    # Checkpoint management
    "CheckpointState",
    "CheckpointManager",
    "ManualReviewItem",
    "ManualReviewQueue",
]
