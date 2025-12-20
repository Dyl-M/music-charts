"""Checkpoint and cache management for pipeline resumability.

Provides mechanisms for tracking pipeline progress, caching processed items,
and managing manual review queues for items that require human intervention.
"""

# Standard library
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# Local
from msc.utils.logging import get_logger


@dataclass
class CheckpointState:
    """Represents the current state of a pipeline checkpoint.

    Tracks what has been processed, what failed, and what needs
    manual review.
    """

    stage_name: str
    created_at: datetime
    last_updated: datetime
    processed_ids: set[str] = field(default_factory=set)
    failed_ids: set[str] = field(default_factory=set)
    skipped_ids: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert checkpoint state to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "stage_name": self.stage_name,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "processed_ids": list(self.processed_ids),
            "failed_ids": list(self.failed_ids),
            "skipped_ids": list(self.skipped_ids),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CheckpointState":
        """Create checkpoint state from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            CheckpointState instance
        """
        return cls(
            stage_name=data["stage_name"],
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            processed_ids=set(data.get("processed_ids", [])),
            failed_ids=set(data.get("failed_ids", [])),
            skipped_ids=set(data.get("skipped_ids", [])),
            metadata=data.get("metadata", {}),
        )


class CheckpointManager:
    """Manages pipeline checkpoints for resumability.

    Handles saving and loading pipeline state, allowing pipelines
    to resume from the last successful point after interruption.
    """

    def __init__(self, checkpoint_dir: Path) -> None:
        """Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory for storing checkpoint files
        """
        # Normalize path to prevent directory traversal
        self.checkpoint_dir = checkpoint_dir.resolve()
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger(__name__)

    def _get_checkpoint_path(self, stage_name: str) -> Path:
        """Get the file path for a stage's checkpoint.

        Args:
            stage_name: Name of the pipeline stage

        Returns:
            Path to checkpoint file
        """
        return self.checkpoint_dir / f"{stage_name}_checkpoint.json"

    def save_checkpoint(self, state: CheckpointState) -> None:
        """Save checkpoint state to disk atomically.

        Args:
            state: Checkpoint state to save (will not be mutated)
        """
        checkpoint_path = self._get_checkpoint_path(state.stage_name)

        try:
            # Update timestamp without mutating input
            from dataclasses import replace
            state = replace(state, last_updated=datetime.now())

            # Write to temp file first for atomicity
            temp_file = checkpoint_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2, ensure_ascii=False)

            # Atomic replace (works on Windows and POSIX)
            temp_file.replace(checkpoint_path)

            self.logger.debug(
                "Saved checkpoint for %s: %d processed, %d failed, %d skipped",
                state.stage_name,
                len(state.processed_ids),
                len(state.failed_ids),
                len(state.skipped_ids),
            )

        except (OSError, json.JSONEncodeError, TypeError) as error:
            self.logger.exception("Failed to save checkpoint for %s: %s", state.stage_name, error)
            raise  # Re-raise to let caller handle failure

    def load_checkpoint(self, stage_name: str) -> CheckpointState | None:
        """Load checkpoint state from disk.

        Args:
            stage_name: Name of the pipeline stage

        Returns:
            CheckpointState if found, None otherwise
        """
        checkpoint_path = self._get_checkpoint_path(stage_name)

        if not checkpoint_path.exists():
            self.logger.debug("No checkpoint found for %s", stage_name)
            return None

        try:
            with open(checkpoint_path, encoding="utf-8") as f:
                data = json.load(f)

            state = CheckpointState.from_dict(data)

            self.logger.info(
                "Loaded checkpoint for %s: %d processed, %d failed, %d skipped",
                stage_name,
                len(state.processed_ids),
                len(state.failed_ids),
                len(state.skipped_ids),
            )
            return state

        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            self.logger.exception("Failed to load checkpoint for %s: %s", stage_name, error)
            return None

    @staticmethod
    def create_checkpoint(
            stage_name: str, metadata: dict[str, Any] | None = None
    ) -> CheckpointState:
        """Create a new checkpoint state.

        Args:
            stage_name: Name of the pipeline stage
            metadata: Additional metadata to store

        Returns:
            New CheckpointState instance
        """
        now = datetime.now()
        return CheckpointState(
            stage_name=stage_name,
            created_at=now,
            last_updated=now,
            metadata=metadata or {},
        )

    def clear_checkpoint(self, stage_name: str) -> None:
        """Delete a checkpoint file.

        Args:
            stage_name: Name of the pipeline stage
        """
        checkpoint_path = self._get_checkpoint_path(stage_name)

        if checkpoint_path.exists():
            try:
                checkpoint_path.unlink()
                self.logger.info("Cleared checkpoint for %s", stage_name)

            except OSError as error:
                self.logger.exception("Failed to clear checkpoint for %s: %s", stage_name, error)


@dataclass
class ManualReviewItem:
    """Represents an item that requires manual review.

    Used for tracks that couldn't be automatically matched
    in Songstats and need human intervention.
    """

    track_id: str
    title: str
    artist: str
    reason: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "track_id": self.track_id,
            "title": self.title,
            "artist": self.artist,
            "reason": self.reason,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ManualReviewItem":
        """Create from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            ManualReviewItem instance
        """
        return cls(
            track_id=data["track_id"],
            title=data["title"],
            artist=data["artist"],
            reason=data["reason"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )


class ManualReviewQueue:
    """Manages items that require manual review.

    Tracks tracks that couldn't be automatically processed
    and need human intervention (e.g., missing Songstats IDs).
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize manual review queue.

        Args:
            file_path: Path to review queue file
        """
        # Normalize path to prevent directory traversal
        self.file_path = file_path.resolve()
        self.logger = get_logger(__name__)
        self.items: list[ManualReviewItem] = []
        self._load()

    def _load(self) -> None:
        """Load review queue from disk."""
        if not self.file_path.exists():
            self.logger.debug("No review queue file found: %s", self.file_path)
            return

        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)

            self.items = [ManualReviewItem.from_dict(item) for item in data]
            self.logger.info("Loaded %d items from review queue", len(self.items))

        except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
            self.logger.exception("Failed to load review queue from %s: %s", self.file_path, error)
            self.items = []

    def _save(self) -> None:
        """Save review queue to disk atomically."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            data = [item.to_dict() for item in self.items]

            # Write to temp file first for atomicity
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic replace (works on Windows and POSIX)
            temp_file.replace(self.file_path)

            self.logger.debug("Saved %d items to review queue", len(self.items))

        except (OSError, json.JSONEncodeError, TypeError) as error:
            self.logger.exception("Failed to save review queue to %s: %s", self.file_path, error)
            raise  # Re-raise to let caller handle failure

    def add(
            self,
            track_id: str,
            title: str,
            artist: str,
            reason: str,
            metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add an item to the review queue.

        Args:
            track_id: Track identifier
            title: Track title
            artist: Artist name
            reason: Reason for manual review
            metadata: Additional metadata
        """
        item = ManualReviewItem(
            track_id=track_id,
            title=title,
            artist=artist,
            reason=reason,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )

        self.items.append(item)
        self._save()
        self.logger.info("Added to review queue: %s - %s (%s)", title, artist, reason)

    def get_all(self) -> list[ManualReviewItem]:
        """Get all items in the review queue.

        Returns:
            List of review items
        """
        return self.items.copy()

    def remove(self, track_id: str) -> bool:
        """Remove an item from the review queue.

        Args:
            track_id: Track identifier to remove

        Returns:
            True if item was found and removed, False otherwise
        """
        original_count = len(self.items)
        self.items = [item for item in self.items if item.track_id != track_id]

        if len(self.items) < original_count:
            self._save()
            self.logger.info("Removed track %s from review queue", track_id)
            return True

        return False

    def clear(self) -> None:
        """Clear all items from the review queue."""
        self.items.clear()
        self._save()
        self.logger.info("Cleared review queue")

    def count(self) -> int:
        """Get the number of items in the queue.

        Returns:
            Number of items
        """
        return len(self.items)
