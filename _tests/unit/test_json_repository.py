"""Tests for JSON repository implementations.

Tests CRUD operations, atomic writes, batch operations, and error handling
for JSONTrackRepository and JSONStatsRepository.
"""

# Standard library
import json
from pathlib import Path

# Third-party
import pytest

# Local
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track
from msc.storage.json_repository import JSONStatsRepository, JSONTrackRepository


class TestJSONTrackRepository:
    """Tests for JSONTrackRepository."""

    @staticmethod
    def test_init_creates_empty_repository(tmp_path: Path) -> None:
        """Test repository initializes with no tracks."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        assert repo.count() == 0
        assert repo.get_all() == []

    @staticmethod
    def test_init_loads_existing_file(tmp_path: Path) -> None:
        """Test repository loads tracks from existing JSON file."""
        repo_file = tmp_path / "tracks.json"

        # Create test data (Track model schema)
        test_data = [
            {
                "title": "Test Track",
                "artist_list": ["Test Artist"],
                "year": 2024,
                "label": ["Test Label"],
                "genre": ["House"],
            }
        ]

        # Write test data
        with open(repo_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Load repository
        repo = JSONTrackRepository(repo_file)

        assert repo.count() == 1
        track = repo.get_all()[0]
        assert track.title == "Test Track"
        assert track.artist_list == ["Test Artist"]

    @staticmethod
    def test_add_and_get_track(tmp_path: Path) -> None:
        """Test adding and retrieving a track."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
            label=["Test Label"],
            genre=["House"],
        )

        repo.add(track)

        retrieved = repo.get(track.identifier)
        assert retrieved is not None
        assert retrieved.title == "Test Track"
        assert retrieved.artist_list == ["Test Artist"]

    @staticmethod
    def test_exists_check(tmp_path: Path) -> None:
        """Test checking if a track exists."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        )

        assert not repo.exists(track.identifier)
        repo.add(track)
        assert repo.exists(track.identifier)

    @staticmethod
    def test_remove_track(tmp_path: Path) -> None:
        """Test removing a track."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        )

        repo.add(track)
        assert repo.count() == 1

        repo.remove(track.identifier)
        assert repo.count() == 0
        assert not repo.exists(track.identifier)

    @staticmethod
    def test_clear_repository(tmp_path: Path) -> None:
        """Test clearing all tracks."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        # Add multiple tracks
        for i in range(3):
            track = Track(
                title=f"Track {i}",
                artist_list=[f"Artist {i}"],
                year=2024,
            )
            repo.add(track)

        assert repo.count() == 3

        repo.clear()
        assert repo.count() == 0

    @staticmethod
    def test_find_by_title_artist(tmp_path: Path) -> None:
        """Test finding track by title and artist."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        )

        repo.add(track)

        # Case-insensitive search using primary_artist property
        found = repo.find_by_title_artist("test track", "test artist")
        assert found is not None
        assert found.title == "Test Track"

        # Not found
        not_found = repo.find_by_title_artist("Unknown", "Unknown")
        assert not_found is None

    @staticmethod
    def test_get_unprocessed(tmp_path: Path) -> None:
        """Test getting unprocessed tracks."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        tracks = [
            Track(
                title=f"Track {i}",
                artist_list=[f"Artist {i}"],
                year=2024,
            )
            for i in range(3)
        ]

        for track in tracks:
            repo.add(track)

        # Mark first two as processed
        processed_ids = {tracks[0].identifier, tracks[1].identifier}

        unprocessed = repo.get_unprocessed(processed_ids)
        assert len(unprocessed) == 1
        assert unprocessed[0].identifier == tracks[2].identifier

    @staticmethod
    def test_atomic_write(tmp_path: Path) -> None:
        """Test that writes are atomic using temp file."""
        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        )

        repo.add(track)

        # Check that temp file doesn't exist after save
        temp_file = repo_file.with_suffix(".tmp")
        assert not temp_file.exists()

        # Check that main file exists and is valid
        assert repo_file.exists()
        with open(repo_file, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1

    @staticmethod
    def test_load_invalid_json(tmp_path: Path) -> None:
        """Test loading repository with invalid JSON."""
        repo_file = tmp_path / "tracks.json"

        # Write invalid JSON
        with open(repo_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # Should create empty repository
        repo = JSONTrackRepository(repo_file)
        assert repo.count() == 0

    @staticmethod
    def test_load_invalid_schema(tmp_path: Path) -> None:
        """Test loading repository with valid JSON but invalid schema."""
        repo_file = tmp_path / "tracks.json"

        # Write valid JSON but missing required fields
        test_data = [{"title": "Test"}]  # Missing required fields

        with open(repo_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Should create empty repository
        repo = JSONTrackRepository(repo_file)
        assert repo.count() == 0


class TestJSONStatsRepository:
    """Tests for JSONStatsRepository."""

    @staticmethod
    def test_init_creates_empty_repository(tmp_path: Path) -> None:
        """Test repository initializes with no stats."""
        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        assert repo.count() == 0
        assert repo.get_all() == []

    @staticmethod
    def test_add_and_get_stats(tmp_path: Path) -> None:
        """Test adding and retrieving stats."""
        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)

        retrieved = repo.get(stats.identifier)
        assert retrieved is not None
        assert retrieved.track.title == "Test Track"
        assert retrieved.songstats_identifiers.songstats_id == "123"

    @staticmethod
    def test_save_batch(tmp_path: Path) -> None:
        """Test batch save operation."""
        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        # Create multiple stats
        stats_list = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=[f"Artist {i}"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(),
            )
            for i in range(3)
        ]

        # Batch save
        repo.save_batch(stats_list)

        assert repo.count() == 3
        for stats in stats_list:
            assert repo.exists(stats.identifier)

    @staticmethod
    def test_get_by_songstats_id(tmp_path: Path) -> None:
        """Test finding stats by Songstats ID."""
        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)

        found = repo.get_by_songstats_id("123")
        assert found is not None
        assert found.track.title == "Test Track"

        not_found = repo.get_by_songstats_id("999")
        assert not_found is None

    @staticmethod
    def test_export_to_json_nested(tmp_path: Path) -> None:
        """Test exporting to nested JSON format."""
        repo_file = tmp_path / "stats.json"
        export_file = tmp_path / "export.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)
        repo.export_to_json(export_file, flat=False)

        assert export_file.exists()
        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        assert "platform_stats" in data[0]

    @staticmethod
    def test_export_to_json_flat(tmp_path: Path) -> None:
        """Test exporting to flat JSON format."""
        repo_file = tmp_path / "stats.json"
        export_file = tmp_path / "export_flat.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)
        repo.export_to_json(export_file, flat=True)

        assert export_file.exists()
        with open(export_file, encoding="utf-8") as f:
            data = json.load(f)

        assert len(data) == 1
        # Flat format should have track fields at top level
        # (check whatever to_flat_dict() outputs)

    @staticmethod
    def test_export_to_csv(tmp_path: Path) -> None:
        """Test exporting to CSV format."""
        repo_file = tmp_path / "stats.json"
        export_file = tmp_path / "export.csv"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)
        repo.export_to_csv(export_file)

        assert export_file.exists()

        # Check CSV has header and data
        with open(export_file, encoding="utf-8") as f:
            lines = f.readlines()
        assert len(lines) >= 2  # Header + at least one data row

    @staticmethod
    def test_load_legacy_format(tmp_path: Path) -> None:
        """Test loading stats from legacy flat format."""
        repo_file = tmp_path / "stats.json"

        # Create legacy flat format data
        test_data = [
            {
                "track": {
                    "title": "Test Track",
                    "artist_list": ["Test Artist"],
                    "year": 2024,
                },
                "songstats_identifiers": {
                    "songstats_id": "123",
                    "songstats_title": "Test Track",
                },
                # Flat platform stats at top level
                "spotify_streams_total": 1000000,
                "apple_music_streams_total": 500000,
            }
        ]

        with open(repo_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        # Should load and convert to nested format
        repo = JSONStatsRepository(repo_file)
        assert repo.count() == 1

        stats = repo.get_all()[0]
        assert stats.track.title == "Test Track"
        assert stats.songstats_identifiers.songstats_id == "123"

    @staticmethod
    def test_track_save_error_handling(tmp_path: Path) -> None:
        """Test track repository handles save errors."""
        from unittest.mock import patch

        repo_file = tmp_path / "tracks.json"
        repo = JSONTrackRepository(repo_file)

        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        )

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                repo.add(track)

    @staticmethod
    def test_stats_save_error_handling(tmp_path: Path) -> None:
        """Test stats repository handles save errors."""
        from unittest.mock import patch

        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                repo.add(stats)

    @staticmethod
    def test_stats_load_with_flat_format_fallback(tmp_path: Path) -> None:
        """Test stats repository falls back to flat format on validation error."""
        repo_file = tmp_path / "stats.json"

        # Create data that fails nested validation but works with flat format
        test_data = [
            {
                "track": {
                    "title": "Test Track",
                    "artist_list": ["Test Artist"],
                    "year": 2024,
                },
                "songstats_identifiers": {
                    "songstats_id": "123",
                    "songstats_title": "Test Track",
                },
                # Flat platform stats (missing nested platform_stats object)
                "spotify_streams_total": 1000000,
            }
        ]

        with open(repo_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        repo = JSONStatsRepository(repo_file)
        assert repo.count() == 1

    @staticmethod
    def test_stats_load_error_handling(tmp_path: Path) -> None:
        """Test stats repository handles complete load failures."""
        repo_file = tmp_path / "stats.json"

        # Write corrupt JSON
        with open(repo_file, "w", encoding="utf-8") as f:
            f.write("{ corrupt json }")

        # Should create empty repository
        repo = JSONStatsRepository(repo_file)
        assert repo.count() == 0

    @staticmethod
    def test_export_to_json_error_handling(tmp_path: Path) -> None:
        """Test export_to_json handles errors gracefully."""
        from unittest.mock import patch

        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )
        repo.add(stats)

        export_file = tmp_path / "export.json"

        # Mock secure_write to raise OSError
        with patch("msc.storage.json_repository.secure_write", side_effect=OSError("Permission denied")):
            # Should log error but not raise
            repo.export_to_json(export_file, flat=False)

    @staticmethod
    def test_export_to_csv_error_handling(tmp_path: Path) -> None:
        """Test export_to_csv handles errors gracefully."""
        from unittest.mock import patch

        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )
        repo.add(stats)

        export_file = tmp_path / "export.csv"

        # Mock DataFrame.to_csv to raise OSError
        with patch("pandas.DataFrame.to_csv", side_effect=OSError("Permission denied")):
            # Should log error but not raise
            repo.export_to_csv(export_file)

    @staticmethod
    def test_stats_remove_error_handling(tmp_path: Path) -> None:
        """Test stats repository handles remove errors."""
        from unittest.mock import patch

        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )
        repo.add(stats)

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                repo.remove(stats.identifier)

    @staticmethod
    def test_stats_clear_error_handling(tmp_path: Path) -> None:
        """Test stats repository handles clear errors."""
        from unittest.mock import patch

        repo_file = tmp_path / "stats.json"
        repo = JSONStatsRepository(repo_file)

        stats = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(),
        )
        repo.add(stats)

        # Mock Path.replace to raise OSError
        with patch("pathlib.Path.replace", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                repo.clear()
