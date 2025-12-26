"""Unit tests for MusicBee client module.

Tests MusicBeeClient library parsing functionality.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.config.settings import Settings


class TestMusicBeeClientInit:
    """Tests for MusicBeeClient initialization."""

    @staticmethod
    def test_raises_for_missing_library(tmp_path: Path) -> None:
        """Should raise FileNotFoundError if library file missing."""
        missing_path = tmp_path / "nonexistent.xml"
        with pytest.raises(FileNotFoundError, match="not found"):
            MusicBeeClient(library_path=missing_path)

    @staticmethod
    def test_stores_library_path(temp_library_file: Path) -> None:
        """Should store library path."""
        client = MusicBeeClient(library_path=temp_library_file)
        assert client.library_path == temp_library_file

    @staticmethod
    def test_uses_settings_library_path(tmp_path: Path) -> None:
        """Should use settings library path if not provided."""
        lib_file = tmp_path / "library.xml"
        lib_file.write_text("<plist></plist>", encoding="utf-8")

        settings = Settings(musicbee_library=lib_file, data_dir=tmp_path)
        client = MusicBeeClient(settings=settings)
        assert client.library_path == lib_file

    @staticmethod
    def test_starts_with_no_library(temp_library_file: Path) -> None:
        """Should start with no cached library."""
        client = MusicBeeClient(library_path=temp_library_file)
        assert client._library is None


class TestMusicBeeClientGetLibrary:
    """Tests for MusicBeeClient.get_library method."""

    @staticmethod
    def test_parses_library(temp_library_file: Path, tmp_path: Path) -> None:
        """Should parse and return library."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            library = client.get_library()
            assert library is not None

    @staticmethod
    def test_caches_library(temp_library_file: Path, tmp_path: Path) -> None:
        """Should cache library after first parse."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            library1 = client.get_library()
            library2 = client.get_library()
            # Library should be parsed only once
            assert mock_lib.call_count == 1
            assert library1 is library2

    @staticmethod
    def test_copies_to_cache(temp_library_file: Path, tmp_path: Path) -> None:
        """Should copy library file to cache directory."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            client.get_library()
            assert client._cached_xml_path is not None
            assert client._cached_xml_path.exists()


class TestMusicBeeClientGetPlaylistTracks:
    """Tests for MusicBeeClient.get_playlist_tracks method."""

    @staticmethod
    def test_returns_empty_for_missing_playlist(temp_library_file: Path, tmp_path: Path) -> None:
        """Should return empty list if playlist not found."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            tracks = client.get_playlist_tracks("9999")
            assert tracks == []

    @staticmethod
    def test_returns_playlist_tracks(temp_library_file: Path, tmp_path: Path) -> None:
        """Should return tracks from playlist."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        mock_track = MagicMock()
        mock_track.year = 2024
        mock_playlist = MagicMock()
        mock_playlist.tracks = [mock_track]

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            tracks = client.get_playlist_tracks("4361")
            assert len(tracks) == 1

    @staticmethod
    def test_filters_by_year(temp_library_file: Path, tmp_path: Path) -> None:
        """Should filter tracks by year."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        track_2024 = MagicMock()
        track_2024.year = 2024
        track_2025 = MagicMock()
        track_2025.year = 2025

        mock_playlist = MagicMock()
        mock_playlist.tracks = [track_2024, track_2025]

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            tracks = client.get_playlist_tracks("4361", year=2024)
            assert len(tracks) == 1
            assert tracks[0].year == 2024


class TestMusicBeeClientGetAllPlaylists:
    """Tests for MusicBeeClient.get_all_playlists method."""

    @staticmethod
    def test_returns_playlist_info(temp_library_file: Path, tmp_path: Path) -> None:
        """Should return playlist metadata."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        mock_playlist = MagicMock()
        mock_playlist.name = "Test Playlist"
        mock_playlist.tracks = [MagicMock(), MagicMock()]

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            playlists = client.get_all_playlists()
            assert "4361" in playlists
            assert playlists["4361"]["name"] == "Test Playlist"
            assert playlists["4361"]["track_count"] == 2


class TestMusicBeeClientFindPlaylistByName:
    """Tests for MusicBeeClient.find_playlist_by_name method."""

    @staticmethod
    def test_finds_exact_match(temp_library_file: Path, tmp_path: Path) -> None:
        """Should find playlist by exact name match."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        mock_playlist = MagicMock()
        mock_playlist.name = "Test Playlist"

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            result = client.find_playlist_by_name("Test Playlist", exact_match=True)
            assert result == "4361"

    @staticmethod
    def test_finds_partial_match(temp_library_file: Path, tmp_path: Path) -> None:
        """Should find playlist by partial name match."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        mock_playlist = MagicMock()
        mock_playlist.name = "My Test Playlist 2024"

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            result = client.find_playlist_by_name("Test")
            assert result == "4361"

    @staticmethod
    def test_returns_none_for_no_match(temp_library_file: Path, tmp_path: Path) -> None:
        """Should return None if no playlist found."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            result = client.find_playlist_by_name("Nonexistent")
            assert result is None

    @staticmethod
    def test_returns_none_for_empty_name(temp_library_file: Path, tmp_path: Path) -> None:
        """Should return None for empty name."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)
        result = client.find_playlist_by_name("")
        assert result is None

    @staticmethod
    def test_case_insensitive_match(temp_library_file: Path, tmp_path: Path) -> None:
        """Should match case-insensitively."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        mock_playlist = MagicMock()
        mock_playlist.name = "TEST PLAYLIST"

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {"4361": mock_playlist}
            mock_lib.return_value.tracks = {}
            result = client.find_playlist_by_name("test playlist", exact_match=True)
            assert result == "4361"


class TestMusicBeeClientClose:
    """Tests for MusicBeeClient cleanup."""

    @staticmethod
    def test_deletes_cached_file(temp_library_file: Path, tmp_path: Path) -> None:
        """Should delete cached XML file on close."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            client.get_library()
            cached_path = client._cached_xml_path
            assert cached_path.exists()

            client.close()
            assert not cached_path.exists()
            assert client._cached_xml_path is None

    @staticmethod
    def test_clears_library_cache(temp_library_file: Path, tmp_path: Path) -> None:
        """Should clear library cache on close."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            client.get_library()
            client.close()
            assert client._library is None


class TestMusicBeeClientContextManager:
    """Tests for MusicBeeClient context manager."""

    @staticmethod
    def test_enter_returns_self(temp_library_file: Path) -> None:
        """Should return self on enter."""
        client = MusicBeeClient(library_path=temp_library_file)
        with client as ctx:
            assert ctx is client

    @staticmethod
    def test_exit_closes_client(temp_library_file: Path, tmp_path: Path) -> None:
        """Should close client on exit."""
        settings = Settings(data_dir=tmp_path)
        client = MusicBeeClient(library_path=temp_library_file, settings=settings)

        with patch("libpybee.Library") as mock_lib:
            mock_lib.return_value.playlists = {}
            mock_lib.return_value.tracks = {}
            with client:
                client.get_library()

            assert client._library is None
