"""Unit tests for MusicBeeClient."""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Third-party
import libpybee
import pytest

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.config.settings import Settings


class TestMusicBeeClientInit:
    """Tests for MusicBeeClient initialization."""

    @staticmethod
    def test_init_with_explicit_path(tmp_path: Path) -> None:
        """Should initialize with provided library path."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        client = MusicBeeClient(library_path=library_path)

        assert client.library_path == library_path
        assert client._library is None
        assert client._cached_xml_path is None

    @staticmethod
    def test_init_with_settings(tmp_path: Path) -> None:
        """Should use library path from settings when not provided."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        settings = Settings(musicbee_library=library_path)
        client = MusicBeeClient(settings=settings)

        assert client.library_path == library_path

    @staticmethod
    def test_init_file_not_found() -> None:
        """Should raise FileNotFoundError if library doesn't exist."""
        non_existent_path = Path("/fake/path/library.xml")

        with pytest.raises(FileNotFoundError, match="MusicBee library not found"):
            MusicBeeClient(library_path=non_existent_path)

    @staticmethod
    def test_init_creates_logger() -> None:
        """Should create logger with class name."""
        fixture_path = Path("_tests/fixtures/test_library.xml")

        client = MusicBeeClient(library_path=fixture_path)

        assert client.logger.name == "MusicBeeClient"


class TestGetLibrary:
    """Tests for the get_library() method."""

    @staticmethod
    @patch("shutil.copyfile")
    @patch("libpybee.Library")
    def test_get_library_first_call(
            mock_library_class: MagicMock,
            mock_copyfile: MagicMock,
            tmp_path: Path,
    ) -> None:
        """Should copy XML and parse on first call."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        mock_library = Mock()
        mock_library.playlists = {"1": Mock()}
        mock_library.tracks = {"1": Mock(), "2": Mock()}
        mock_library_class.return_value = mock_library

        settings = Settings(data_dir=tmp_path / "data", musicbee_library=library_path)
        client = MusicBeeClient(settings=settings)

        result = client.get_library()

        # Should copy file
        expected_cache = tmp_path / "data" / "cache" / "lib.xml"
        mock_copyfile.assert_called_once_with(library_path, expected_cache)

        # Should parse XML
        mock_library_class.assert_called_once_with(str(expected_cache))

        # Should return library
        assert result == mock_library
        assert client._library == mock_library

    @staticmethod
    @patch("shutil.copyfile")
    @patch("libpybee.Library")
    def test_get_library_cached(
            mock_library_class: MagicMock,
            mock_copyfile: MagicMock,
            tmp_path: Path,
    ) -> None:
        """Should return cached library on subsequent calls."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        mock_library = Mock()
        mock_library.playlists = {}
        mock_library.tracks = {}
        mock_library_class.return_value = mock_library

        settings = Settings(data_dir=tmp_path / "data", musicbee_library=library_path)
        client = MusicBeeClient(settings=settings)

        # First call
        result1 = client.get_library()

        # Second call
        result2 = client.get_library()

        # Should only copy/parse once
        assert mock_copyfile.call_count == 1
        assert mock_library_class.call_count == 1

        # Should return same object
        assert result1 is result2

    @staticmethod
    @patch("shutil.copyfile")
    @patch("libpybee.Library", side_effect=Exception("Parse error"))
    def test_get_library_parse_error(
            _mock_library_class: MagicMock,
            _mock_copyfile: MagicMock,
            tmp_path: Path,
    ) -> None:
        """Should raise RuntimeError if parsing fails."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        settings = Settings(data_dir=tmp_path / "data", musicbee_library=library_path)
        client = MusicBeeClient(settings=settings)

        with pytest.raises(RuntimeError, match="Failed to parse MusicBee library"):
            client.get_library()

    @staticmethod
    @patch("shutil.copyfile")
    @patch("libpybee.Library")
    def test_get_library_creates_cache_dir(
            mock_library_class: MagicMock,
            _mock_copyfile: MagicMock,
            tmp_path: Path,
    ) -> None:
        """Should create cache directory if it doesn't exist."""
        library_path = tmp_path / "library.xml"
        library_path.write_text('<?xml version="1.0"?><plist></plist>', encoding="utf-8")

        mock_library = Mock()
        mock_library.playlists = {}
        mock_library.tracks = {}
        mock_library_class.return_value = mock_library

        settings = Settings(data_dir=tmp_path / "data", musicbee_library=library_path)
        client = MusicBeeClient(settings=settings)

        cache_dir = tmp_path / "data" / "cache"
        assert not cache_dir.exists()

        client.get_library()

        assert cache_dir.exists()
        assert cache_dir.is_dir()


class TestGetPlaylistTracks:
    """Tests for the get_playlist_tracks() method."""

    @staticmethod
    def test_get_playlist_tracks_success() -> None:
        """Should return tracks from specified playlist."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        tracks = client.get_playlist_tracks("4361")

        assert isinstance(tracks, list)
        assert len(tracks) == 4
        assert all(isinstance(t, libpybee.Track) for t in tracks)

    @staticmethod
    def test_get_playlist_tracks_with_year_filter() -> None:
        """Should filter tracks by year."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        # Playlist 4361 has tracks from 2024 and 2025
        tracks_2024 = client.get_playlist_tracks("4361", year=2024)
        tracks_2025 = client.get_playlist_tracks("4361", year=2025)

        assert len(tracks_2024) == 2
        assert all(t.year == 2024 for t in tracks_2024)

        assert len(tracks_2025) == 2
        assert all(t.year == 2025 for t in tracks_2025)

    @staticmethod
    def test_get_playlist_tracks_year_no_matches() -> None:
        """Should return empty list when year filter has no matches."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        tracks = client.get_playlist_tracks("4361", year=2020)

        assert tracks == []

    @staticmethod
    def test_get_playlist_tracks_playlist_not_found() -> None:
        """Should return empty list when playlist doesn't exist."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        tracks = client.get_playlist_tracks("nonexistent")

        assert tracks == []

    @staticmethod
    def test_get_playlist_tracks_empty_playlist() -> None:
        """Should return empty list for empty playlist."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        tracks = client.get_playlist_tracks("9999")  # Empty playlist

        assert tracks == []

    @staticmethod
    @patch.object(MusicBeeClient, "get_library")
    def test_get_playlist_tracks_calls_get_library(mock_get_library: MagicMock) -> None:
        """Should call get_library() to ensure library is loaded."""
        fixture_path = Path("_tests/fixtures/test_library.xml")

        mock_library = Mock()
        mock_playlist = Mock()
        mock_playlist.tracks = []
        mock_library.playlists = {"4361": mock_playlist}
        mock_get_library.return_value = mock_library

        client = MusicBeeClient(library_path=fixture_path)
        client.get_playlist_tracks("4361")

        mock_get_library.assert_called_once()


class TestGetAllPlaylists:
    """Tests for the get_all_playlists() method."""

    @staticmethod
    def test_get_all_playlists_success() -> None:
        """Should return all playlists with metadata."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        playlists = client.get_all_playlists()

        assert isinstance(playlists, dict)
        # Master playlist is not included in libpybee (All Items = true)
        assert len(playlists) >= 3  # At least 3 regular playlists

        # Check playlist 4361 exists
        assert "4361" in playlists
        assert "track_count" in playlists["4361"]
        assert playlists["4361"]["track_count"] == 4

    @staticmethod
    def test_get_all_playlists_includes_empty() -> None:
        """Should include empty playlists."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        playlists = client.get_all_playlists()

        assert "9999" in playlists
        assert playlists["9999"]["track_count"] == 0

    @staticmethod
    @patch.object(MusicBeeClient, "get_library")
    def test_get_all_playlists_structure(mock_get_library: MagicMock) -> None:
        """Should return correct structure for each playlist."""
        fixture_path = Path("_tests/fixtures/test_library.xml")

        mock_library = Mock()
        mock_playlist = Mock()
        mock_playlist.name = "Test Playlist"
        mock_playlist.tracks = [Mock(), Mock()]
        mock_library.playlists = {"123": mock_playlist}
        mock_get_library.return_value = mock_library

        client = MusicBeeClient(library_path=fixture_path)
        playlists = client.get_all_playlists()

        assert "123" in playlists
        assert playlists["123"]["name"] == "Test Playlist"
        assert playlists["123"]["track_count"] == 2

    @staticmethod
    @patch.object(MusicBeeClient, "get_library")
    def test_get_all_playlists_no_name_attribute(mock_get_library: MagicMock) -> None:
        """Should handle playlists without name attribute."""
        fixture_path = Path("_tests/fixtures/test_library.xml")

        mock_library = Mock()
        mock_playlist = Mock(spec=[])  # No attributes
        mock_playlist.tracks = []
        mock_library.playlists = {"456": mock_playlist}
        mock_get_library.return_value = mock_library

        client = MusicBeeClient(library_path=fixture_path)
        playlists = client.get_all_playlists()

        assert "456" in playlists
        assert playlists["456"]["name"] == "Unknown"


class TestClose:
    """Tests for the close() method."""

    @staticmethod
    def test_close_deletes_cached_xml(tmp_path: Path) -> None:
        """Should delete cached XML file."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client = MusicBeeClient(settings=settings)
        client.get_library()

        cached_xml = tmp_path / "cache" / "lib.xml"
        assert cached_xml.exists()

        client.close()

        assert not cached_xml.exists()

    @staticmethod
    def test_close_clears_library_reference(tmp_path: Path) -> None:
        """Should clear the library reference."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client = MusicBeeClient(settings=settings)
        client.get_library()

        assert client._library is not None

        client.close()

        assert client._library is None

    @staticmethod
    def test_close_clears_cached_path(tmp_path: Path) -> None:
        """Should clear the cached XML path reference."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client = MusicBeeClient(settings=settings)
        client.get_library()

        assert client._cached_xml_path is not None

        client.close()

        assert client._cached_xml_path is None

    @staticmethod
    def test_close_when_not_loaded() -> None:
        """Should not error when closing without loading library."""
        library_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=library_path)

        # Should not raise
        client.close()

        assert client._library is None
        assert client._cached_xml_path is None

    @staticmethod
    def test_close_idempotent(tmp_path: Path) -> None:
        """Should be safe to call close() multiple times."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client = MusicBeeClient(settings=settings)
        client.get_library()

        # Should not raise on multiple calls
        client.close()
        client.close()
        client.close()


class TestContextManager:
    """Tests for context manager support."""

    @staticmethod
    def test_context_manager_enter(tmp_path: Path) -> None:
        """Should return self from __enter__."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client = MusicBeeClient(settings=settings)

        with client as ctx:
            assert ctx is client

    @staticmethod
    def test_context_manager_exit_calls_close(tmp_path: Path) -> None:
        """Should call close() on __exit__."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        with MusicBeeClient(settings=settings) as client:
            client.get_library()
            cached_xml = tmp_path / "cache" / "lib.xml"
            assert cached_xml.exists()

        # After exiting context, file should be deleted
        assert not cached_xml.exists()

    @staticmethod
    def test_context_manager_full_workflow(tmp_path: Path) -> None:
        """Should support full workflow with context manager."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        with MusicBeeClient(settings=settings) as client:
            library = client.get_library()
            tracks = client.get_playlist_tracks("4361", year=2025)
            playlists = client.get_all_playlists()

            assert library is not None
            assert len(tracks) == 2
            assert len(playlists) >= 3

        # Resources should be cleaned up
        assert client._library is None
        assert client._cached_xml_path is None


class TestEdgeCases:
    """Tests for edge cases and error conditions."""

    @staticmethod
    def test_track_attributes_accessible() -> None:
        """Should be able to access track attributes."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        tracks = client.get_playlist_tracks("4361")
        track = tracks[0]

        # Should have standard attributes
        assert hasattr(track, "title")
        assert hasattr(track, "artist_list")
        assert hasattr(track, "year")
        assert isinstance(track.year, int)

    @staticmethod
    def test_multiple_clients_same_library(tmp_path: Path) -> None:
        """Should support multiple client instances."""
        library_path = Path("_tests/fixtures/test_library.xml")
        settings = Settings(data_dir=tmp_path, musicbee_library=library_path)

        client1 = MusicBeeClient(settings=settings)
        tracks1 = client1.get_playlist_tracks("4361")
        client1.close()

        # Clear libpybee state between clients within same test
        if hasattr(libpybee.Track, "all_tracks"):
            libpybee.Track.all_tracks.clear()
        if hasattr(libpybee.Playlist, "all_playlists"):
            libpybee.Playlist.all_playlists.clear()

        client2 = MusicBeeClient(settings=settings)
        tracks2 = client2.get_playlist_tracks("4361")
        client2.close()

        assert len(tracks1) == len(tracks2) == 4

    @staticmethod
    def test_get_playlist_tracks_various_years() -> None:
        """Should correctly filter tracks by various years."""
        fixture_path = Path("_tests/fixtures/test_library.xml")
        client = MusicBeeClient(library_path=fixture_path)

        # Test each year
        tracks_2023 = client.get_playlist_tracks("5555", year=2023)
        tracks_2024 = client.get_playlist_tracks("4361", year=2024)
        tracks_2025 = client.get_playlist_tracks("4361", year=2025)
        tracks_2026 = client.get_playlist_tracks("4361", year=2026)

        assert len(tracks_2023) == 1
        assert len(tracks_2024) == 2
        assert len(tracks_2025) == 2
        assert len(tracks_2026) == 0
