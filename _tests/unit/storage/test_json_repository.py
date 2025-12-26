"""Unit tests for JSON repository implementations.

Tests JSONTrackRepository and JSONStatsRepository.
"""

# Standard library
import json
from pathlib import Path

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import TrackWithStats, PlatformStats
from msc.storage.json_repository import JSONTrackRepository, JSONStatsRepository


class TestJSONTrackRepositoryInit:
    """Tests for JSONTrackRepository initialization."""

    @staticmethod
    def test_creates_empty_repository(tmp_path: Path) -> None:
        """Should create empty repository when file doesn't exist."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)
        assert repo.count() == 0

    @staticmethod
    def test_loads_existing_data(tmp_path: Path) -> None:
        """Should load tracks from existing file."""
        file_path = tmp_path / "tracks.json"
        track_data = [
            {"title": "Test", "artist_list": ["Artist"], "year": 2024}
        ]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(track_data, f)

        repo = JSONTrackRepository(file_path)
        assert repo.count() == 1

    @staticmethod
    def test_handles_corrupt_json(tmp_path: Path) -> None:
        """Should handle corrupt JSON file gracefully."""
        file_path = tmp_path / "tracks.json"
        file_path.write_text("{invalid json}", encoding="utf-8")

        repo = JSONTrackRepository(file_path)
        assert repo.count() == 0

    @staticmethod
    def test_handles_invalid_track_data(tmp_path: Path) -> None:
        """Should handle invalid track data gracefully."""
        file_path = tmp_path / "tracks.json"
        invalid_data = [{"invalid": "data"}]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(invalid_data, f)

        repo = JSONTrackRepository(file_path)
        assert repo.count() == 0


class TestJSONTrackRepositoryAdd:
    """Tests for JSONTrackRepository.add method."""

    @staticmethod
    def test_adds_track(tmp_path: Path, sample_track: Track) -> None:
        """Should add track to repository."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.add(sample_track)
        assert repo.count() == 1

    @staticmethod
    def test_persists_to_file(tmp_path: Path, sample_track: Track) -> None:
        """Should persist track to JSON file."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.add(sample_track)

        assert file_path.exists()
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 1

    @staticmethod
    def test_replaces_existing_track(tmp_path: Path) -> None:
        """Should replace track with same identifier."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        # Same artist, title, year but different genre - same identifier
        track1 = Track(title="Test", artist_list=["Artist"], year=2024, genre=["rock"])
        track2 = Track(title="Test", artist_list=["Artist"], year=2024, genre=["pop"])

        repo.add(track1)
        repo.add(track2)

        assert repo.count() == 1
        retrieved = repo.get(track1.identifier)
        assert retrieved is not None
        assert retrieved.genre == ["pop"]


class TestJSONTrackRepositoryGet:
    """Tests for JSONTrackRepository.get method."""

    @staticmethod
    def test_returns_track_by_identifier(tmp_path: Path, sample_track: Track) -> None:
        """Should return track by identifier."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.add(sample_track)
        retrieved = repo.get(sample_track.identifier)

        assert retrieved is not None
        assert retrieved.title == sample_track.title

    @staticmethod
    def test_returns_none_for_missing(tmp_path: Path) -> None:
        """Should return None for missing identifier."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        result = repo.get("nonexistent")
        assert result is None


class TestJSONTrackRepositoryGetAll:
    """Tests for JSONTrackRepository.get_all method."""

    @staticmethod
    def test_returns_all_tracks(tmp_path: Path) -> None:
        """Should return all tracks."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track1 = Track(title="Track 1", artist_list=["Artist"], year=2024)
        track2 = Track(title="Track 2", artist_list=["Artist"], year=2024)

        repo.add(track1)
        repo.add(track2)

        all_tracks = repo.get_all()
        assert len(all_tracks) == 2

    @staticmethod
    def test_returns_empty_list_when_empty(tmp_path: Path) -> None:
        """Should return empty list for empty repository."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        assert repo.get_all() == []


class TestJSONTrackRepositoryExists:
    """Tests for JSONTrackRepository.exists method."""

    @staticmethod
    def test_returns_true_for_existing(tmp_path: Path, sample_track: Track) -> None:
        """Should return True for existing track."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.add(sample_track)
        assert repo.exists(sample_track.identifier) is True

    @staticmethod
    def test_returns_false_for_missing(tmp_path: Path) -> None:
        """Should return False for missing track."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        assert repo.exists("nonexistent") is False


class TestJSONTrackRepositoryRemove:
    """Tests for JSONTrackRepository.remove method."""

    @staticmethod
    def test_removes_track(tmp_path: Path, sample_track: Track) -> None:
        """Should remove track from repository."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.add(sample_track)
        repo.remove(sample_track.identifier)

        assert repo.count() == 0

    @staticmethod
    def test_safe_for_missing_track(tmp_path: Path) -> None:
        """Should not error when removing missing track."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        repo.remove("nonexistent")  # Should not raise


class TestJSONTrackRepositoryClear:
    """Tests for JSONTrackRepository.clear method."""

    @staticmethod
    def test_removes_all_tracks(tmp_path: Path) -> None:
        """Should remove all tracks."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track1 = Track(title="Track 1", artist_list=["Artist"], year=2024)
        track2 = Track(title="Track 2", artist_list=["Artist"], year=2024)

        repo.add(track1)
        repo.add(track2)
        repo.clear()

        assert repo.count() == 0


class TestJSONTrackRepositoryFindByTitleArtist:
    """Tests for JSONTrackRepository.find_by_title_artist method."""

    @staticmethod
    def test_finds_matching_track(tmp_path: Path) -> None:
        """Should find track by title and artist."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track = Track(title="Test Track", artist_list=["Test Artist"], year=2024)
        repo.add(track)

        found = repo.find_by_title_artist("Test Track", "Test Artist")
        assert found is not None
        assert found.identifier == track.identifier

    @staticmethod
    def test_case_insensitive_match(tmp_path: Path) -> None:
        """Should match case-insensitively."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track = Track(title="Test Track", artist_list=["Test Artist"], year=2024)
        repo.add(track)

        found = repo.find_by_title_artist("TEST TRACK", "test artist")
        assert found is not None

    @staticmethod
    def test_returns_none_for_no_match(tmp_path: Path) -> None:
        """Should return None when no match found."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        found = repo.find_by_title_artist("Missing", "Artist")
        assert found is None


class TestJSONTrackRepositoryGetUnprocessed:
    """Tests for JSONTrackRepository.get_unprocessed method."""

    @staticmethod
    def test_returns_unprocessed_tracks(tmp_path: Path) -> None:
        """Should return only unprocessed tracks."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track1 = Track(title="Track 1", artist_list=["Artist"], year=2024)
        track2 = Track(title="Track 2", artist_list=["Artist"], year=2024)
        track3 = Track(title="Track 3", artist_list=["Artist"], year=2024)

        repo.add(track1)
        repo.add(track2)
        repo.add(track3)

        processed = {track1.identifier, track2.identifier}
        unprocessed = repo.get_unprocessed(processed)

        assert len(unprocessed) == 1
        assert unprocessed[0].identifier == track3.identifier

    @staticmethod
    def test_returns_all_when_none_processed(tmp_path: Path) -> None:
        """Should return all tracks when none processed."""
        file_path = tmp_path / "tracks.json"
        repo = JSONTrackRepository(file_path)

        track1 = Track(title="Track 1", artist_list=["Artist"], year=2024)
        track2 = Track(title="Track 2", artist_list=["Artist"], year=2024)

        repo.add(track1)
        repo.add(track2)

        unprocessed = repo.get_unprocessed(set())
        assert len(unprocessed) == 2


class TestJSONStatsRepositoryInit:
    """Tests for JSONStatsRepository initialization."""

    @staticmethod
    def test_creates_empty_repository(tmp_path: Path) -> None:
        """Should create empty repository when file doesn't exist."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)
        assert repo.count() == 0

    @staticmethod
    def test_loads_nested_format(tmp_path: Path) -> None:
        """Should load stats from nested format."""
        file_path = tmp_path / "stats.json"
        stats_data = [{
            "track": {
                "title": "Test",
                "artist_list": ["Artist"],
                "year": 2024,
            },
            "songstats_identifiers": {
                "songstats_id": "abc123",
                "songstats_title": "Test",
            },
            "platform_stats": {},
        }]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f)

        repo = JSONStatsRepository(file_path)
        assert repo.count() == 1

    @staticmethod
    def test_loads_flat_format(tmp_path: Path) -> None:
        """Should load stats from flat format."""
        file_path = tmp_path / "stats.json"
        stats_data = [{
            "title": "Test",
            "artist_list": ["Artist"],
            "year": 2024,
            "songstats_id": "abc123",
            "songstats_title": "Test",
        }]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(stats_data, f)

        repo = JSONStatsRepository(file_path)
        assert repo.count() == 1


class TestJSONStatsRepositoryAdd:
    """Tests for JSONStatsRepository.add method."""

    @staticmethod
    def test_adds_stats(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should add stats to repository."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        assert repo.count() == 1

    @staticmethod
    def test_persists_to_file(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should persist stats to JSON file."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)

        assert file_path.exists()


class TestJSONStatsRepositorySaveBatch:
    """Tests for JSONStatsRepository.save_batch method."""

    @staticmethod
    def test_saves_multiple_items(tmp_path: Path) -> None:
        """Should save multiple items efficiently."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        items = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=["Artist"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"id{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(),
            )
            for i in range(5)
        ]

        repo.save_batch(items)
        assert repo.count() == 5


class TestJSONStatsRepositoryExportToJson:
    """Tests for JSONStatsRepository.export_to_json method."""

    @staticmethod
    def test_exports_nested_format(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should export in nested format by default."""
        file_path = tmp_path / "stats.json"
        export_path = tmp_path / "export.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.export_to_json(export_path, flat=False)

        assert export_path.exists()
        with open(export_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "songstats_identifiers" in data[0]

    @staticmethod
    def test_exports_flat_format(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should export in flat format when requested."""
        file_path = tmp_path / "stats.json"
        export_path = tmp_path / "export.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.export_to_json(export_path, flat=True)

        assert export_path.exists()
        with open(export_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "songstats_id" in data[0]


class TestJSONStatsRepositoryExportToCsv:
    """Tests for JSONStatsRepository.export_to_csv method."""

    @staticmethod
    def test_exports_to_csv(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should export to CSV file."""
        file_path = tmp_path / "stats.json"
        export_path = tmp_path / "export.csv"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.export_to_csv(export_path)

        assert export_path.exists()
        content = export_path.read_text(encoding="utf-8")
        # to_flat_dict exports track_id and songstats_id
        assert "track_id" in content
        assert "songstats_id" in content

    @staticmethod
    def test_creates_parent_directory(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should create parent directory if needed."""
        file_path = tmp_path / "stats.json"
        export_path = tmp_path / "subdir" / "export.csv"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.export_to_csv(export_path)

        assert export_path.exists()


class TestJSONStatsRepositoryGetBySongstatsId:
    """Tests for JSONStatsRepository.get_by_songstats_id method."""

    @staticmethod
    def test_finds_by_songstats_id(tmp_path: Path) -> None:
        """Should find stats by Songstats ID."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        stats = TrackWithStats(
            track=Track(
                title="Test",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="target123",
                songstats_title="Test",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats)
        found = repo.get_by_songstats_id("target123")

        assert found is not None
        assert found.songstats_identifiers.songstats_id == "target123"

    @staticmethod
    def test_returns_none_for_no_match(tmp_path: Path) -> None:
        """Should return None when Songstats ID not found."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        found = repo.get_by_songstats_id("nonexistent")
        assert found is None


class TestJSONStatsRepositoryCRUD:
    """Tests for JSONStatsRepository CRUD operations."""

    @staticmethod
    def test_get_returns_stats(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should return stats by identifier."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        retrieved = repo.get(sample_track_with_stats.identifier)

        assert retrieved is not None

    @staticmethod
    def test_get_all_returns_all(tmp_path: Path) -> None:
        """Should return all stats."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        stats1 = TrackWithStats(
            track=Track(
                title="Track 1",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id1",
                songstats_title="Track 1",
            ),
            platform_stats=PlatformStats(),
        )
        stats2 = TrackWithStats(
            track=Track(
                title="Track 2",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id2",
                songstats_title="Track 2",
            ),
            platform_stats=PlatformStats(),
        )

        repo.add(stats1)
        repo.add(stats2)

        all_stats = repo.get_all()
        assert len(all_stats) == 2

    @staticmethod
    def test_exists_returns_true(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should return True for existing stats."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        assert repo.exists(sample_track_with_stats.identifier) is True

    @staticmethod
    def test_remove_deletes_stats(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should remove stats from repository."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.remove(sample_track_with_stats.identifier)

        assert repo.count() == 0

    @staticmethod
    def test_clear_removes_all(tmp_path: Path, sample_track_with_stats: TrackWithStats) -> None:
        """Should remove all stats."""
        file_path = tmp_path / "stats.json"
        repo = JSONStatsRepository(file_path)

        repo.add(sample_track_with_stats)
        repo.clear()

        assert repo.count() == 0
