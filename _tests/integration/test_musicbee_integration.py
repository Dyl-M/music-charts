"""Integration tests for MusicBee client with real XML files.

Tests parsing of actual MusicBee library XML files.
"""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.clients.musicbee import MusicBeeClient


class TestMusicBeeClientRealXML:
    """Integration tests for MusicBeeClient with real XML."""

    @staticmethod
    def test_loads_test_library(test_library_path: Path) -> None:
        """Should load test library XML file."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)
        assert client.library_path == test_library_path

    @staticmethod
    def test_parses_playlists(test_library_path: Path) -> None:
        """Should parse playlists from test library."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)
        playlists = client.get_all_playlists()

        # Returns dict with playlist info
        assert isinstance(playlists, dict)

    @staticmethod
    def test_finds_playlist_by_name(test_library_path: Path) -> None:
        """Should find playlist by name."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)

        # This should return None for non-existent playlist
        result = client.find_playlist_by_name("Nonexistent Playlist 12345")
        assert result is None

    @staticmethod
    def test_get_library(test_library_path: Path) -> None:
        """Should get library object."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)
        library = client.get_library()

        # Library should be parsed
        assert library is not None

    @staticmethod
    def test_context_manager(test_library_path: Path) -> None:
        """Should work as context manager."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        with MusicBeeClient(test_library_path) as client:
            playlists = client.get_all_playlists()
            assert isinstance(playlists, dict)

    @staticmethod
    def test_close_method(test_library_path: Path) -> None:
        """Should have close method."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)
        # Close should not raise
        client.close()

    @staticmethod
    def test_handles_missing_file() -> None:
        """Should handle missing file appropriately."""
        nonexistent = Path("/nonexistent/library.xml")

        # Should raise on instantiation or first access
        with pytest.raises((FileNotFoundError, OSError)):
            client = MusicBeeClient(nonexistent)
            client.get_library()

    @staticmethod
    def test_get_playlist_tracks(test_library_path: Path) -> None:
        """Should get tracks from playlist by ID."""
        if not test_library_path.exists():
            pytest.skip("Test library fixture not found")

        client = MusicBeeClient(test_library_path)
        playlists = client.get_all_playlists()

        # If there are playlists, try to get tracks
        if playlists:
            # Get first playlist ID
            playlist_ids = list(playlists.keys())
            if playlist_ids:
                tracks = client.get_playlist_tracks(playlist_ids[0])
                assert isinstance(tracks, list)
