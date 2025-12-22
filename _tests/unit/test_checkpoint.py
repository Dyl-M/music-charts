"""Tests for checkpoint and manual review queue.

Tests CheckpointManager and ManualReviewQueue for pipeline resumability,
state persistence, and atomic operations.
"""

# Standard library
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Local
from msc.storage.checkpoint import (
    CheckpointManager,
    CheckpointState,
    ManualReviewItem,
    ManualReviewQueue,
)


class TestCheckpointState:
    """Tests for CheckpointState dataclass."""

    @staticmethod
    def test_create_checkpoint_state() -> None:
        """Test creating a checkpoint state."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test_stage",
            created_at=now,
            last_updated=now,
            processed_ids={"id1", "id2"},
            failed_ids={"id3"},
            skipped_ids={"id4"},
            metadata={"key": "value"},
        )

        assert state.stage_name == "test_stage"
        assert state.created_at == now
        assert len(state.processed_ids) == 2
        assert len(state.failed_ids) == 1
        assert state.metadata["key"] == "value"

    @staticmethod
    def test_to_dict() -> None:
        """Test converting checkpoint state to dictionary."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test_stage",
            created_at=now,
            last_updated=now,
            processed_ids={"id1", "id2"},
            failed_ids=set(),
            skipped_ids=set(),
        )

        data = state.to_dict()

        assert data["stage_name"] == "test_stage"
        assert isinstance(data["processed_ids"], list)
        assert len(data["processed_ids"]) == 2
        assert "id1" in data["processed_ids"]

    @staticmethod
    def test_from_dict() -> None:
        """Test creating checkpoint state from dictionary."""
        now = datetime.now()
        data = {
            "stage_name": "test_stage",
            "created_at": now.isoformat(),
            "last_updated": now.isoformat(),
            "processed_ids": ["id1", "id2"],
            "failed_ids": [],
            "skipped_ids": [],
            "metadata": {},
        }

        state = CheckpointState.from_dict(data)

        assert state.stage_name == "test_stage"
        assert isinstance(state.processed_ids, set)
        assert len(state.processed_ids) == 2


class TestCheckpointManager:
    """Tests for CheckpointManager."""

    @staticmethod
    def test_init_creates_directory(tmp_path: Path) -> None:
        """Test manager creates checkpoint directory."""
        checkpoint_dir = tmp_path / "checkpoints"
        _manager = CheckpointManager(checkpoint_dir)

        assert checkpoint_dir.exists()
        assert checkpoint_dir.is_dir()

    @staticmethod
    def test_create_checkpoint() -> None:
        """Test creating a new checkpoint."""
        state = CheckpointManager.create_checkpoint(
            "test_stage", metadata={"key": "value"}
        )

        assert state.stage_name == "test_stage"
        assert state.metadata["key"] == "value"
        assert len(state.processed_ids) == 0

    @staticmethod
    def test_save_and_load_checkpoint(tmp_path: Path) -> None:
        """Test saving and loading checkpoint."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        # Create and save checkpoint
        state = CheckpointManager.create_checkpoint("test_stage")
        state.processed_ids.add("id1")
        state.processed_ids.add("id2")
        state.failed_ids.add("id3")

        manager.save_checkpoint(state)

        # Load checkpoint
        loaded = manager.load_checkpoint("test_stage")

        assert loaded is not None
        assert loaded.stage_name == "test_stage"
        assert len(loaded.processed_ids) == 2
        assert "id1" in loaded.processed_ids
        assert len(loaded.failed_ids) == 1

    @staticmethod
    def test_load_nonexistent_checkpoint(tmp_path: Path) -> None:
        """Test loading checkpoint that doesn't exist."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        loaded = manager.load_checkpoint("nonexistent")
        assert loaded is None

    @staticmethod
    def test_clear_checkpoint(tmp_path: Path) -> None:
        """Test clearing a checkpoint file."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        # Create and save checkpoint
        state = CheckpointManager.create_checkpoint("test_stage")
        manager.save_checkpoint(state)

        # Clear checkpoint
        manager.clear_checkpoint("test_stage")

        # Should no longer exist
        loaded = manager.load_checkpoint("test_stage")
        assert loaded is None

    @staticmethod
    def test_checkpoint_path_format(tmp_path: Path) -> None:
        """Test checkpoint file path format."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        state = CheckpointManager.create_checkpoint("extraction")
        manager.save_checkpoint(state)

        checkpoint_file = tmp_path / "checkpoints" / "extraction_checkpoint.json"
        assert checkpoint_file.exists()

    @staticmethod
    def test_atomic_checkpoint_save(tmp_path: Path) -> None:
        """Test that checkpoint saves are atomic."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        state = CheckpointManager.create_checkpoint("test_stage")
        state.processed_ids.add("id1")

        manager.save_checkpoint(state)

        # Temp file should not exist
        checkpoint_path = manager._get_checkpoint_path("test_stage")
        temp_file = checkpoint_path.with_suffix(".tmp")
        assert not temp_file.exists()

        # Main file should exist
        assert checkpoint_path.exists()

    @staticmethod
    def test_checkpoint_immutability(tmp_path: Path) -> None:
        """Test that save_checkpoint doesn't mutate input state."""
        manager = CheckpointManager(tmp_path / "checkpoints")

        state = CheckpointManager.create_checkpoint("test_stage")
        original_timestamp = state.last_updated

        manager.save_checkpoint(state)

        # Original state should not be mutated
        assert state.last_updated == original_timestamp

    @staticmethod
    def test_load_corrupted_checkpoint(tmp_path: Path) -> None:
        """Test loading corrupted checkpoint file."""
        checkpoint_dir = tmp_path / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Write corrupted JSON
        checkpoint_file = checkpoint_dir / "test_stage_checkpoint.json"
        with open(checkpoint_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        manager = CheckpointManager(checkpoint_dir)
        loaded = manager.load_checkpoint("test_stage")

        # Should return None on error
        assert loaded is None


class TestManualReviewItem:
    """Tests for ManualReviewItem dataclass."""

    @staticmethod
    def test_create_review_item() -> None:
        """Test creating a manual review item."""
        now = datetime.now()
        item = ManualReviewItem(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="No Songstats ID found",
            timestamp=now,
            metadata={"query": "test query"},
        )

        assert item.track_id == "test_id"
        assert item.title == "Test Track"
        assert item.reason == "No Songstats ID found"

    @staticmethod
    def test_to_dict() -> None:
        """Test converting review item to dictionary."""
        now = datetime.now()
        item = ManualReviewItem(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="Test reason",
            timestamp=now,
        )

        data = item.to_dict()

        assert data["track_id"] == "test_id"
        assert data["title"] == "Test Track"
        assert isinstance(data["timestamp"], str)

    @staticmethod
    def test_from_dict() -> None:
        """Test creating review item from dictionary."""
        now = datetime.now()
        data = {
            "track_id": "test_id",
            "title": "Test Track",
            "artist": "Test Artist",
            "reason": "Test reason",
            "timestamp": now.isoformat(),
            "metadata": {},
        }

        item = ManualReviewItem.from_dict(data)

        assert item.track_id == "test_id"
        assert item.title == "Test Track"


class TestManualReviewQueue:
    """Tests for ManualReviewQueue."""

    @staticmethod
    def test_init_creates_empty_queue(tmp_path: Path) -> None:
        """Test queue initializes empty."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        assert queue.count() == 0
        assert queue.get_all() == []

    @staticmethod
    def test_add_item(tmp_path: Path) -> None:
        """Test adding item to queue."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        queue.add(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="No Songstats ID found",
            metadata={"query": "test query"},
        )

        assert queue.count() == 1
        items = queue.get_all()
        assert items[0].track_id == "test_id"
        assert items[0].reason == "No Songstats ID found"

    @staticmethod
    def test_remove_item(tmp_path: Path) -> None:
        """Test removing item from queue."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        queue.add(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="Test reason",
        )

        assert queue.count() == 1

        result = queue.remove("test_id")
        assert result is True
        assert queue.count() == 0

    @staticmethod
    def test_remove_nonexistent_item(tmp_path: Path) -> None:
        """Test removing item that doesn't exist."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        result = queue.remove("nonexistent_id")
        assert result is False

    @staticmethod
    def test_clear_queue(tmp_path: Path) -> None:
        """Test clearing all items from queue."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        # Add multiple items
        for i in range(3):
            queue.add(
                track_id=f"id_{i}",
                title=f"Track {i}",
                artist=f"Artist {i}",
                reason="Test reason",
            )

        assert queue.count() == 3

        queue.clear()
        assert queue.count() == 0

    @staticmethod
    def test_persistence(tmp_path: Path) -> None:
        """Test queue persists across instances."""
        queue_file = tmp_path / "review_queue.json"

        # Add items to first instance
        queue1 = ManualReviewQueue(queue_file)
        queue1.add(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="Test reason",
        )

        # Load second instance
        queue2 = ManualReviewQueue(queue_file)
        assert queue2.count() == 1
        assert queue2.get_all()[0].track_id == "test_id"

    @staticmethod
    def test_atomic_queue_save(tmp_path: Path) -> None:
        """Test that queue saves are atomic."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        queue.add(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="Test reason",
        )

        # Temp file should not exist
        temp_file = queue_file.with_suffix(".tmp")
        assert not temp_file.exists()

        # Main file should exist
        assert queue_file.exists()

    @staticmethod
    def test_load_corrupted_queue(tmp_path: Path) -> None:
        """Test loading corrupted queue file."""
        queue_file = tmp_path / "review_queue.json"

        # Write corrupted JSON
        with open(queue_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # Should create empty queue
        queue = ManualReviewQueue(queue_file)
        assert queue.count() == 0

    @staticmethod
    def test_review_queue_save_error_handling(tmp_path: Path) -> None:
        """Test review queue handles save errors."""
        queue_file = tmp_path / "review_queue.json"
        queue = ManualReviewQueue(queue_file)

        queue.add(
            track_id="test_id",
            title="Test Track",
            artist="Test Artist",
            reason="Test reason",
        )

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")), pytest.raises(OSError):
            queue.add(
                track_id="test_id2",
                title="Test Track 2",
                artist="Test Artist 2",
                reason="Test reason 2",
            )


class TestCheckpointManagerExceptions:
    """Tests for CheckpointManager exception handling."""

    @staticmethod
    def test_save_checkpoint_error_handling(tmp_path: Path) -> None:
        """Test checkpoint manager handles save errors."""
        manager = CheckpointManager(tmp_path)

        now = datetime.now()
        state = CheckpointState(
            stage_name="test",
            created_at=now,
            last_updated=now,
            processed_ids={"test"},
        )

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")), pytest.raises(OSError):
            manager.save_checkpoint(state)

    @staticmethod
    def test_clear_checkpoint_error_handling(tmp_path: Path) -> None:
        """Test checkpoint manager handles clear errors."""
        manager = CheckpointManager(tmp_path)

        # Create a checkpoint first
        now = datetime.now()
        state = CheckpointState(
            stage_name="test",
            created_at=now,
            last_updated=now,
            processed_ids={"test"},
        )
        manager.save_checkpoint(state)

        # Mock Path.unlink to raise OSError
        with patch("pathlib.Path.unlink", side_effect=OSError("Permission denied")):
            # Should log error but not raise
            manager.clear_checkpoint("test")
