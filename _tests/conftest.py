"""Pytest configuration and root fixtures.

This file contains only the auto-use fixtures that must run for all tests.
Shared test fixtures are in _tests/unit/conftest.py.
"""

# Third-party
import libpybee
import pytest


@pytest.fixture(autouse=True)
def clear_libpybee_state():
    """Clear libpybee Track and Playlist databases between tests.

    libpybee maintains class-level sets that store all Track/Playlist IDs
    to prevent duplicates. This fixture clears them after each test to
    ensure isolation.

    Yields:
        None: Control is yielded to the test function.
    """
    yield  # Test runs here
    # Clear the Track ID registry after test completes
    if hasattr(libpybee.Track, "all_tracks"):
        libpybee.Track.all_tracks.clear()

    # Clear the Playlist ID registry after test completes
    if hasattr(libpybee.Playlist, "all_playlists"):
        libpybee.Playlist.all_playlists.clear()
