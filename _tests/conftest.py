"""Pytest configuration and shared fixtures."""

# Standard library
from pathlib import Path

# Third-party
import pytest


@pytest.fixture
def sample_track_data() -> dict:
    """Sample track data for testing."""
    return {
        "title": "sample track extended mix",
        "artist_list": ["artist a", "artist b"],
        "label": ["sample records"],
        "genre": ["house"],
        "request": "artist a, artist b sample track",
        "data": {
            "s_id": "abc123",
            "s_title": "Sample Track"
        }
    }


@pytest.fixture
def sample_stats_data() -> dict:
    """Sample statistics data for testing."""
    return {
        "spotify_streams": 1000000,
        "spotify_playlist_reach": 500000,
        "spotify_playlist_count": 150,
        "spotify_popularity_peak": 75,
        "apple_music_playlist_reach": 200000,
        "deezer_popularity_peak": 60,
        "youtube_views": 2000000,
    }


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory structure."""
    data_dir = tmp_path / "_data"
    (data_dir / "input").mkdir(parents=True)
    (data_dir / "output").mkdir(parents=True)
    (data_dir / "cache").mkdir(parents=True)
    return data_dir


@pytest.fixture
def temp_tokens_dir(tmp_path: Path) -> Path:
    """Create a temporary tokens directory with mock credentials."""
    tokens_dir = tmp_path / "_tokens"
    tokens_dir.mkdir(parents=True)

    # Create mock API key file
    (tokens_dir / "songstats_key.txt").write_text("mock_api_key_for_testing")

    return tokens_dir
