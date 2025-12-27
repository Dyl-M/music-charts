"""Fixtures for commands tests."""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock

# Third-party
import pytest

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.platforms import SpotifyStats, DeezerStats


@pytest.fixture
def sample_track() -> Track:
    """Create a sample track for testing."""
    return Track(
        title="Test Track",
        artist_list=["Test Artist"],
        year=2024,
    )


@pytest.fixture
def sample_track_with_stats() -> TrackWithStats:
    """Create a sample track with stats for testing."""
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
        platform_stats=PlatformStats(
            spotify=SpotifyStats(streams_total=1000000, popularity_current=80),
            deezer=DeezerStats(popularity_peak=75),
        ),
    )


@pytest.fixture
def sample_tracks_with_stats() -> list[TrackWithStats]:
    """Create sample tracks with stats for testing."""
    return [
        TrackWithStats(
            track=Track(title="Track A", artist_list=["Artist 1"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id1", songstats_title="Track A"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=1000000, popularity_current=80),
            ),
        ),
        TrackWithStats(
            track=Track(title="Track B", artist_list=["Artist 2"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id2", songstats_title="Track B"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=500000, popularity_current=60),
            ),
        ),
    ]


@pytest.fixture
def mock_stats_repository() -> MagicMock:
    """Create a mock stats repository."""
    mock = MagicMock()
    mock.get_all.return_value = []
    return mock


@pytest.fixture
def sample_quota_data() -> dict:
    """Create sample Songstats API quota data."""
    return {
        "status": {
            "current_month_total_requests": 1234,
            "current_month_total_requested_objects": 5678,
            "current_month_total_bill": "12.34",
            "previous_month_total_requests": 9876,
            "previous_month_total_bill": "98.76",
        }
    }


@pytest.fixture
def sample_validation_errors() -> list[dict]:
    """Create sample validation errors."""
    return [
        {
            "loc": ["title"],
            "msg": "Field required",
            "type": "missing",
        },
        {
            "loc": ["artist_list", 0],
            "msg": "Invalid artist name",
            "type": "value_error",
        },
    ]


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Create a temporary cache directory with test files."""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create some test files
    (cache_dir / "file1.json").write_text("{}", encoding="utf-8")
    (cache_dir / "file2.json").write_text("{}", encoding="utf-8")

    # Create a subdirectory with files
    subdir = cache_dir / "subdir"
    subdir.mkdir()
    (subdir / "nested.json").write_text("{}", encoding="utf-8")

    return cache_dir
