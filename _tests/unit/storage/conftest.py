"""Fixtures for storage tests."""

# Standard library
from datetime import datetime
from pathlib import Path

# Third-party
import pytest

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import TrackWithStats, PlatformStats
from msc.storage.checkpoint import CheckpointState, ManualReviewItem


@pytest.fixture
def temp_storage_dir(tmp_path: Path) -> Path:
    """Create temporary storage directory."""
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir(parents=True, exist_ok=True)
    return storage_dir


@pytest.fixture
def sample_track() -> Track:
    """Create a sample track for testing."""
    return Track(
        title="Test Track",
        artist_list=["Test Artist"],
        year=2024,
    )


@pytest.fixture
def sample_track_with_isrc() -> Track:
    """Create a sample track with ISRC."""
    return Track(
        title="Test Track ISRC",
        artist_list=["Test Artist"],
        year=2024,
    )


@pytest.fixture
def sample_track_with_stats() -> TrackWithStats:
    """Create a sample TrackWithStats for testing."""
    return TrackWithStats(
        track=Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        ),
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test Track",
        ),
        platform_stats=PlatformStats(),
    )


@pytest.fixture
def sample_checkpoint_state() -> CheckpointState:
    """Create a sample checkpoint state."""
    now = datetime.now()
    return CheckpointState(
        stage_name="test_stage",
        created_at=now,
        last_updated=now,
        processed_ids={"id1", "id2"},
        failed_ids={"id3"},
        skipped_ids={"id4"},
        metadata={"key": "value"},
    )


@pytest.fixture
def sample_review_item() -> ManualReviewItem:
    """Create a sample manual review item."""
    return ManualReviewItem(
        track_id="track123",
        title="Test Track",
        artist="Test Artist",
        reason="No match found",
        timestamp=datetime.now(),
        metadata={"query": "test query"},
    )
