"""Fixtures for analysis tests."""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import TrackWithStats, PlatformStats
from msc.models.platforms import SpotifyStats, DeezerStats


@pytest.fixture
def sample_values() -> list[float]:
    """Sample values for normalization testing."""
    return [10.0, 20.0, 30.0, 40.0, 50.0]


@pytest.fixture
def sample_values_with_outlier() -> list[float]:
    """Sample values with an outlier."""
    return [10.0, 20.0, 30.0, 40.0, 1000.0]


@pytest.fixture
def sample_tracks_with_stats() -> list[TrackWithStats]:
    """Create sample tracks with varying statistics."""
    return [
        TrackWithStats(
            track=Track(title="Track A", artist_list=["Artist 1"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id1", songstats_title="Track A"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=1000000, popularity_current=80),
                deezer=DeezerStats(popularity_peak=75),
            ),
        ),
        TrackWithStats(
            track=Track(title="Track B", artist_list=["Artist 2"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id2", songstats_title="Track B"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=500000, popularity_current=60),
                deezer=DeezerStats(popularity_peak=50),
            ),
        ),
        TrackWithStats(
            track=Track(title="Track C", artist_list=["Artist 3"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id3", songstats_title="Track C"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=2000000, popularity_current=95),
                deezer=DeezerStats(popularity_peak=90),
            ),
        ),
    ]


@pytest.fixture
def temp_category_config(tmp_path: Path) -> Path:
    """Create temporary category config file."""
    config_path = tmp_path / "categories.json"
    config_path.write_text(
        '{"popularity": ["spotify_popularity_current", "deezer_popularity_peak"],'
        ' "streams": ["spotify_streams_total"]}',
        encoding="utf-8",
    )
    return config_path
