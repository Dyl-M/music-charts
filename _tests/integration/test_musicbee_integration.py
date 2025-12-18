"""Integration tests for MusicBeeClient with real XML parsing."""

# Standard library
from pathlib import Path

# Third-party
import libpybee
import pytest

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.config.settings import Settings

# Skip all tests if fixture doesn't exist
FIXTURE_PATH = Path("_tests/fixtures/test_library.xml")
pytestmark = pytest.mark.skipif(
    not FIXTURE_PATH.exists(),
    reason="Test fixture XML not found",
)


class TestMusicBeeClientIntegration:
    """Integration tests using real libpybee parsing."""

    @staticmethod
    def test_full_workflow(tmp_path: Path) -> None:
        """Should complete full workflow with real XML parsing."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)

        with MusicBeeClient(settings=settings) as client:
            # Load library
            library = client.get_library()
            assert isinstance(library, libpybee.Library)

            # Get playlists
            playlists = client.get_all_playlists()
            assert isinstance(playlists, dict)
            assert len(playlists) > 0

            # Get tracks without filter
            tracks_all = client.get_playlist_tracks("4361")
            assert len(tracks_all) == 4

            # Get tracks with year filter
            tracks_2024 = client.get_playlist_tracks("4361", year=2024)
            tracks_2025 = client.get_playlist_tracks("4361", year=2025)

            assert len(tracks_2024) == 2
            assert len(tracks_2025) == 2

            # Verify track attributes
            for track in tracks_2024:
                assert track.year == 2024
                assert isinstance(track.title, str)
                assert isinstance(track.artist_list, list)

        # Verify cleanup
        cached_xml = tmp_path / "cache" / "lib.xml"
        assert not cached_xml.exists()

    @staticmethod
    def test_library_structure(tmp_path: Path) -> None:
        """Should parse library with correct structure."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        library = client.get_library()

        # Verify library has expected structure
        assert hasattr(library, "playlists")
        assert hasattr(library, "tracks")
        assert isinstance(library.playlists, dict)
        assert isinstance(library.tracks, dict)

        # Verify playlist exists
        assert "4361" in library.playlists

        client.close()

    @staticmethod
    def test_playlist_track_details(tmp_path: Path) -> None:
        """Should parse track details correctly."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        tracks = client.get_playlist_tracks("4361")

        # Verify we have tracks
        assert len(tracks) > 0

        # Check first track has expected attributes
        track = tracks[0]
        assert hasattr(track, "title")
        assert hasattr(track, "artist_list")
        assert hasattr(track, "year")
        assert hasattr(track, "genre")
        assert hasattr(track, "grouping")

        # Verify types
        assert isinstance(track.title, str)
        assert isinstance(track.artist_list, list)
        assert isinstance(track.year, int)

        client.close()

    @staticmethod
    def test_year_filtering_accuracy(tmp_path: Path) -> None:
        """Should accurately filter tracks by year."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        # Get all tracks
        all_tracks = client.get_playlist_tracks("4361")

        # Get tracks by year
        tracks_2024 = client.get_playlist_tracks("4361", year=2024)
        tracks_2025 = client.get_playlist_tracks("4361", year=2025)

        # Sum of filtered tracks should equal total
        assert len(tracks_2024) + len(tracks_2025) == len(all_tracks)

        # All tracks should have correct year
        assert all(t.year == 2024 for t in tracks_2024)
        assert all(t.year == 2025 for t in tracks_2025)

        client.close()

    @staticmethod
    def test_empty_playlist(tmp_path: Path) -> None:
        """Should handle empty playlists correctly."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        tracks = client.get_playlist_tracks("9999")  # Empty playlist

        assert tracks == []

        client.close()

    @staticmethod
    def test_nonexistent_playlist(tmp_path: Path) -> None:
        """Should return empty list for nonexistent playlist."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        tracks = client.get_playlist_tracks("nonexistent_id")

        assert tracks == []

        client.close()

    @staticmethod
    def test_multiple_operations_same_client(tmp_path: Path) -> None:
        """Should support multiple operations on same client."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        # Multiple calls should work
        playlists1 = client.get_all_playlists()
        tracks1 = client.get_playlist_tracks("4361", year=2024)
        library1 = client.get_library()

        playlists2 = client.get_all_playlists()
        tracks2 = client.get_playlist_tracks("4361", year=2024)
        library2 = client.get_library()

        # Results should be consistent
        assert playlists1 == playlists2
        assert len(tracks1) == len(tracks2)
        assert library1 is library2  # Same cached object

        client.close()

    @staticmethod
    def test_xml_caching_behavior(tmp_path: Path) -> None:
        """Should cache XML copy and library object."""
        settings = Settings(data_dir=tmp_path, musicbee_library=FIXTURE_PATH)
        client = MusicBeeClient(settings=settings)

        cached_xml = tmp_path / "cache" / "lib.xml"

        # Before loading, cache shouldn't exist
        assert not cached_xml.exists()

        # Load library
        library1 = client.get_library()

        # Cache should now exist
        assert cached_xml.exists()

        # Second call should use cached library (not re-parse)
        library2 = client.get_library()
        assert library1 is library2

        # Cleanup
        client.close()

        # Cache should be deleted
        assert not cached_xml.exists()
