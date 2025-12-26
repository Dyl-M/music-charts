"""Unit tests for checkpoint and manual review queue.

Tests CheckpointState, CheckpointManager, ManualReviewItem, and ManualReviewQueue.
"""

# Standard library
import json
from datetime import datetime
from pathlib import Path

# Third-party
import pytest

# Local
from msc.storage.checkpoint import (
    CheckpointState,
    CheckpointManager,
    ManualReviewItem,
    ManualReviewQueue,
)


class TestCheckpointStateInit:
    """Tests for CheckpointState initialization."""

    @staticmethod
    def test_stores_stage_name() -> None:
        """Should store stage name."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test_stage",
            created_at=now,
            last_updated=now,
        )
        assert state.stage_name == "test_stage"

    @staticmethod
    def test_stores_timestamps() -> None:
        """Should store created_at and last_updated timestamps."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test",
            created_at=now,
            last_updated=now,
        )
        assert state.created_at == now
        assert state.last_updated == now

    @staticmethod
    def test_default_empty_sets() -> None:
        """Should default to empty sets."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test",
            created_at=now,
            last_updated=now,
        )
        assert state.processed_ids == set()
        assert state.failed_ids == set()
        assert state.skipped_ids == set()

    @staticmethod
    def test_default_empty_metadata() -> None:
        """Should default to empty metadata."""
        now = datetime.now()
        state = CheckpointState(
            stage_name="test",
            created_at=now,
            last_updated=now,
        )
        assert state.metadata == {}


class TestCheckpointStateToDict:
    """Tests for CheckpointState.to_dict method."""

    @staticmethod
    def test_converts_to_dict(sample_checkpoint_state: CheckpointState) -> None:
        """Should convert state to dictionary."""
        result = sample_checkpoint_state.to_dict()

        assert result["stage_name"] == "test_stage"
        assert "created_at" in result
        assert "last_updated" in result

    @staticmethod
    def test_converts_sets_to_lists(sample_checkpoint_state: CheckpointState) -> None:
        """Should convert sets to lists for JSON serialization."""
        result = sample_checkpoint_state.to_dict()

        assert isinstance(result["processed_ids"], list)
        assert isinstance(result["failed_ids"], list)
        assert isinstance(result["skipped_ids"], list)

    @staticmethod
    def test_includes_metadata(sample_checkpoint_state: CheckpointState) -> None:
        """Should include metadata in dictionary."""
        result = sample_checkpoint_state.to_dict()
        assert result["metadata"] == {"key": "value"}


class TestCheckpointStateFromDict:
    """Tests for CheckpointState.from_dict method."""

    @staticmethod
    def test_creates_from_dict() -> None:
        """Should create state from dictionary."""
        data = {
            "stage_name": "test",
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
            "processed_ids": ["id1", "id2"],
            "failed_ids": ["id3"],
            "skipped_ids": [],
            "metadata": {"key": "value"},
        }

        state = CheckpointState.from_dict(data)

        assert state.stage_name == "test"
        assert state.processed_ids == {"id1", "id2"}
        assert state.failed_ids == {"id3"}
        assert state.metadata == {"key": "value"}

    @staticmethod
    def test_handles_missing_optional_fields() -> None:
        """Should handle missing optional fields."""
        data = {
            "stage_name": "test",
            "created_at": "2024-01-01T12:00:00",
            "last_updated": "2024-01-01T12:00:00",
        }

        state = CheckpointState.from_dict(data)

        assert state.processed_ids == set()
        assert state.failed_ids == set()
        assert state.skipped_ids == set()
        assert state.metadata == {}

    @staticmethod
    def test_roundtrip_conversion(sample_checkpoint_state: CheckpointState) -> None:
        """Should survive roundtrip to/from dict."""
        data = sample_checkpoint_state.to_dict()
        restored = CheckpointState.from_dict(data)

        assert restored.stage_name == sample_checkpoint_state.stage_name
        assert restored.processed_ids == sample_checkpoint_state.processed_ids


class TestCheckpointManagerInit:
    """Tests for CheckpointManager initialization."""

    @staticmethod
    def test_creates_directory(tmp_path: Path) -> None:
        """Should create checkpoint directory."""
        checkpoint_dir = tmp_path / "checkpoints"
        CheckpointManager(checkpoint_dir)
        assert checkpoint_dir.exists()

    @staticmethod
    def test_resolves_path(tmp_path: Path) -> None:
        """Should resolve path to absolute."""
        manager = CheckpointManager(tmp_path)
        assert manager.checkpoint_dir.is_absolute()


class TestCheckpointManagerSaveCheckpoint:
    """Tests for CheckpointManager.save_checkpoint method."""

    @staticmethod
    def test_saves_to_file(tmp_path: Path, sample_checkpoint_state: CheckpointState) -> None:
        """Should save checkpoint to file."""
        manager = CheckpointManager(tmp_path)
        manager.save_checkpoint(sample_checkpoint_state)

        checkpoint_file = tmp_path / "test_stage_checkpoint.json"
        assert checkpoint_file.exists()

    @staticmethod
    def test_saves_valid_json(tmp_path: Path, sample_checkpoint_state: CheckpointState) -> None:
        """Should save valid JSON."""
        manager = CheckpointManager(tmp_path)
        manager.save_checkpoint(sample_checkpoint_state)

        checkpoint_file = tmp_path / "test_stage_checkpoint.json"
        with open(checkpoint_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["stage_name"] == "test_stage"

    @staticmethod
    def test_updates_timestamp(tmp_path: Path) -> None:
        """Should update last_updated timestamp."""
        manager = CheckpointManager(tmp_path)
        old_time = datetime(2020, 1, 1)
        state = CheckpointState(
            stage_name="test",
            created_at=old_time,
            last_updated=old_time,
        )

        manager.save_checkpoint(state)

        loaded = manager.load_checkpoint("test")
        assert loaded is not None
        assert loaded.last_updated > old_time


class TestCheckpointManagerLoadCheckpoint:
    """Tests for CheckpointManager.load_checkpoint method."""

    @staticmethod
    def test_loads_existing_checkpoint(tmp_path: Path, sample_checkpoint_state: CheckpointState) -> None:
        """Should load existing checkpoint."""
        manager = CheckpointManager(tmp_path)
        manager.save_checkpoint(sample_checkpoint_state)

        loaded = manager.load_checkpoint("test_stage")

        assert loaded is not None
        assert loaded.stage_name == "test_stage"

    @staticmethod
    def test_returns_none_for_missing(tmp_path: Path) -> None:
        """Should return None for missing checkpoint."""
        manager = CheckpointManager(tmp_path)
        result = manager.load_checkpoint("nonexistent")
        assert result is None

    @staticmethod
    def test_handles_corrupt_json(tmp_path: Path) -> None:
        """Should handle corrupt checkpoint file."""
        manager = CheckpointManager(tmp_path)
        checkpoint_file = tmp_path / "corrupt_checkpoint.json"
        checkpoint_file.write_text("{invalid}", encoding="utf-8")

        result = manager.load_checkpoint("corrupt")
        assert result is None


class TestCheckpointManagerCreateCheckpoint:
    """Tests for CheckpointManager.create_checkpoint method."""

    @staticmethod
    def test_creates_new_checkpoint() -> None:
        """Should create new checkpoint state."""
        state = CheckpointManager.create_checkpoint("test_stage")

        assert state.stage_name == "test_stage"
        assert state.processed_ids == set()

    @staticmethod
    def test_includes_metadata() -> None:
        """Should include provided metadata."""
        state = CheckpointManager.create_checkpoint(
            "test_stage",
            metadata={"year": 2024}
        )
        assert state.metadata == {"year": 2024}

    @staticmethod
    def test_sets_timestamps() -> None:
        """Should set created_at and last_updated."""
        before = datetime.now()
        state = CheckpointManager.create_checkpoint("test")
        after = datetime.now()

        assert before <= state.created_at <= after
        assert before <= state.last_updated <= after


class TestCheckpointManagerClearCheckpoint:
    """Tests for CheckpointManager.clear_checkpoint method."""

    @staticmethod
    def test_deletes_checkpoint_file(tmp_path: Path, sample_checkpoint_state: CheckpointState) -> None:
        """Should delete checkpoint file."""
        manager = CheckpointManager(tmp_path)
        manager.save_checkpoint(sample_checkpoint_state)

        checkpoint_file = tmp_path / "test_stage_checkpoint.json"
        assert checkpoint_file.exists()

        manager.clear_checkpoint("test_stage")
        assert not checkpoint_file.exists()

    @staticmethod
    def test_safe_for_missing_checkpoint(tmp_path: Path) -> None:
        """Should not error for missing checkpoint."""
        manager = CheckpointManager(tmp_path)
        manager.clear_checkpoint("nonexistent")  # Should not raise


class TestManualReviewItemInit:
    """Tests for ManualReviewItem initialization."""

    @staticmethod
    def test_stores_fields() -> None:
        """Should store all fields."""
        now = datetime.now()
        item = ManualReviewItem(
            track_id="track123",
            title="Test Track",
            artist="Test Artist",
            reason="No match",
            timestamp=now,
        )
        assert item.track_id == "track123"
        assert item.title == "Test Track"
        assert item.artist == "Test Artist"
        assert item.reason == "No match"
        assert item.timestamp == now

    @staticmethod
    def test_default_empty_metadata() -> None:
        """Should default to empty metadata."""
        item = ManualReviewItem(
            track_id="id",
            title="title",
            artist="artist",
            reason="reason",
            timestamp=datetime.now(),
        )
        assert item.metadata == {}


class TestManualReviewItemToDict:
    """Tests for ManualReviewItem.to_dict method."""

    @staticmethod
    def test_converts_to_dict(sample_review_item: ManualReviewItem) -> None:
        """Should convert to dictionary."""
        result = sample_review_item.to_dict()

        assert result["track_id"] == "track123"
        assert result["title"] == "Test Track"
        assert result["artist"] == "Test Artist"

    @staticmethod
    def test_converts_timestamp_to_iso(sample_review_item: ManualReviewItem) -> None:
        """Should convert timestamp to ISO format."""
        result = sample_review_item.to_dict()
        assert isinstance(result["timestamp"], str)


class TestManualReviewItemFromDict:
    """Tests for ManualReviewItem.from_dict method."""

    @staticmethod
    def test_creates_from_dict() -> None:
        """Should create from dictionary."""
        data = {
            "track_id": "id123",
            "title": "Test",
            "artist": "Artist",
            "reason": "Reason",
            "timestamp": "2024-01-01T12:00:00",
            "metadata": {"key": "value"},
        }

        item = ManualReviewItem.from_dict(data)

        assert item.track_id == "id123"
        assert item.metadata == {"key": "value"}

    @staticmethod
    def test_handles_missing_metadata() -> None:
        """Should handle missing metadata."""
        data = {
            "track_id": "id",
            "title": "title",
            "artist": "artist",
            "reason": "reason",
            "timestamp": "2024-01-01T12:00:00",
        }

        item = ManualReviewItem.from_dict(data)
        assert item.metadata == {}


class TestManualReviewQueueInit:
    """Tests for ManualReviewQueue initialization."""

    @staticmethod
    def test_creates_empty_queue(tmp_path: Path) -> None:
        """Should create empty queue when file doesn't exist."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)
        assert queue.count() == 0

    @staticmethod
    def test_loads_existing_queue(tmp_path: Path) -> None:
        """Should load existing queue from file."""
        file_path = tmp_path / "review.json"
        data = [{
            "track_id": "id1",
            "title": "Test",
            "artist": "Artist",
            "reason": "Reason",
            "timestamp": "2024-01-01T12:00:00",
        }]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

        queue = ManualReviewQueue(file_path)
        assert queue.count() == 1

    @staticmethod
    def test_handles_corrupt_file(tmp_path: Path) -> None:
        """Should handle corrupt file gracefully."""
        file_path = tmp_path / "review.json"
        file_path.write_text("{invalid}", encoding="utf-8")

        queue = ManualReviewQueue(file_path)
        assert queue.count() == 0


class TestManualReviewQueueAdd:
    """Tests for ManualReviewQueue.add method."""

    @staticmethod
    def test_adds_item(tmp_path: Path) -> None:
        """Should add item to queue."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title", "Artist", "Reason")
        assert queue.count() == 1

    @staticmethod
    def test_deduplicates_by_track_id(tmp_path: Path) -> None:
        """Should not add duplicate track IDs."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title 1", "Artist", "Reason 1")
        queue.add("id1", "Title 2", "Artist", "Reason 2")

        assert queue.count() == 1

    @staticmethod
    def test_persists_to_file(tmp_path: Path) -> None:
        """Should persist to file."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title", "Artist", "Reason")

        assert file_path.exists()

    @staticmethod
    def test_includes_metadata(tmp_path: Path) -> None:
        """Should include metadata in item."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title", "Artist", "Reason", metadata={"query": "test"})

        items = queue.get_all()
        assert items[0].metadata == {"query": "test"}


class TestManualReviewQueueGetAll:
    """Tests for ManualReviewQueue.get_all method."""

    @staticmethod
    def test_returns_all_items(tmp_path: Path) -> None:
        """Should return all items."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title 1", "Artist", "Reason")
        queue.add("id2", "Title 2", "Artist", "Reason")

        items = queue.get_all()
        assert len(items) == 2

    @staticmethod
    def test_returns_copy(tmp_path: Path) -> None:
        """Should return copy, not reference."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title", "Artist", "Reason")
        items = queue.get_all()
        items.clear()

        assert queue.count() == 1


class TestManualReviewQueueRemove:
    """Tests for ManualReviewQueue.remove method."""

    @staticmethod
    def test_removes_item(tmp_path: Path) -> None:
        """Should remove item by track ID."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title", "Artist", "Reason")
        result = queue.remove("id1")

        assert result is True
        assert queue.count() == 0

    @staticmethod
    def test_returns_false_for_missing(tmp_path: Path) -> None:
        """Should return False if item not found."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        result = queue.remove("nonexistent")
        assert result is False


class TestManualReviewQueueClear:
    """Tests for ManualReviewQueue.clear method."""

    @staticmethod
    def test_clears_all_items(tmp_path: Path) -> None:
        """Should remove all items."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title 1", "Artist", "Reason")
        queue.add("id2", "Title 2", "Artist", "Reason")
        queue.clear()

        assert queue.count() == 0


class TestManualReviewQueueCount:
    """Tests for ManualReviewQueue.count method."""

    @staticmethod
    def test_returns_zero_for_empty(tmp_path: Path) -> None:
        """Should return 0 for empty queue."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)
        assert queue.count() == 0

    @staticmethod
    def test_returns_correct_count(tmp_path: Path) -> None:
        """Should return correct count."""
        file_path = tmp_path / "review.json"
        queue = ManualReviewQueue(file_path)

        queue.add("id1", "Title 1", "Artist", "Reason")
        queue.add("id2", "Title 2", "Artist", "Reason")

        assert queue.count() == 2
