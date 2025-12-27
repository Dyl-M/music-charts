"""Fixtures for utils module tests."""

# Third-party
import pytest


@pytest.fixture
def sample_track_title() -> str:
    """Sample track title with mix suffix for testing."""
    return "Sample Track (Extended Mix)"


@pytest.fixture
def sample_artist_list() -> list[str]:
    """Sample artist list for testing."""
    return ["Artist A", "Artist B"]
