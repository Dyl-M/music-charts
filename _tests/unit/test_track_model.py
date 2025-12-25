"""Tests for Track and SongstatsIdentifiers models."""

# Standard library
import json
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.config.settings import PROJECT_ROOT
from msc.models.track import SongstatsIdentifiers, Track


class TestTrack:
    """Tests for Track model."""

    @staticmethod
    def test_create_valid_track() -> None:
        """Test creating a valid Track instance."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024
        )
        assert track.title == "16"
        assert track.artist_list == ["blasterjaxx", "hardwell", "maddix"]
        assert track.year == 2024

    @staticmethod
    def test_title_required() -> None:
        """Test that title is required."""
        with pytest.raises(ValidationError) as exc_info:
            Track(artist_list=["artist"], year=2024)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    @staticmethod
    def test_artist_list_required() -> None:
        """Test that artist_list is required."""
        with pytest.raises(ValidationError) as exc_info:
            Track(title="Test", year=2024)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("artist_list",) for e in errors)

    @staticmethod
    def test_artist_list_min_length() -> None:
        """Test that artist_list must have at least one artist."""
        with pytest.raises(ValidationError) as exc_info:
            Track(title="Test", artist_list=[], year=2024)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("artist_list",) for e in errors)
        assert any("at least 1" in str(e["msg"]).lower() for e in errors)

    @staticmethod
    def test_year_validation_min() -> None:
        """Test year minimum validation."""
        with pytest.raises(ValidationError) as exc_info:
            Track(title="Test", artist_list=["artist"], year=1899)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("year",) for e in errors)

    @staticmethod
    def test_year_validation_max() -> None:
        """Test year maximum validation."""
        with pytest.raises(ValidationError) as exc_info:
            Track(title="Test", artist_list=["artist"], year=2101)

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("year",) for e in errors)

    @staticmethod
    def test_year_validation_boundaries() -> None:
        """Test year boundary values are valid."""
        # Min boundary
        track_min = Track(title="Test", artist_list=["artist"], year=1900)
        assert track_min.year == 1900

        # Max boundary
        track_max = Track(title="Test", artist_list=["artist"], year=2100)
        assert track_max.year == 2100

    @staticmethod
    def test_default_genre_empty_list() -> None:
        """Test genre defaults to empty list."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        assert track.genre == []

    @staticmethod
    def test_default_grouping_empty_list() -> None:
        """Test grouping defaults to empty list."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        assert track.grouping == []

    @staticmethod
    def test_search_query_optional() -> None:
        """Test search_query is optional and defaults to None."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        assert track.search_query is None

    @staticmethod
    def test_search_query_alias() -> None:
        """Test search_query can be set via 'request' alias."""
        # Using field name
        track1 = Track(
            title="Test",
            artist_list=["artist"],
            year=2024,
            search_query="artist Test"
        )
        assert track1.search_query == "artist Test"

        # Using alias
        track2 = Track(
            title="Test",
            artist_list=["artist"],
            year=2024,
            request="artist Test"
        )
        assert track2.search_query == "artist Test"

    @staticmethod
    def test_frozen_model() -> None:
        """Test Track is immutable (frozen)."""
        track = Track(title="Test", artist_list=["artist"], year=2024)

        with pytest.raises(ValidationError):
            track.title = "New Title"

    @staticmethod
    def test_primary_artist_property() -> None:
        """Test primary_artist property returns first artist."""
        track = Track(
            title="Test",
            artist_list=["artist1", "artist2", "artist3"],
            year=2024
        )
        assert track.primary_artist == "artist1"

    @staticmethod
    def test_all_artists_string_property() -> None:
        """Test all_artists_string property joins artists."""
        track = Track(
            title="Test",
            artist_list=["artist1", "artist2", "artist3"],
            year=2024
        )
        assert track.all_artists_string == "artist1, artist2, artist3"

    @staticmethod
    def test_all_artists_string_single_artist() -> None:
        """Test all_artists_string with single artist."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
        )
        assert track.all_artists_string == "artist"

    @staticmethod
    def test_identifier_is_uuid_based() -> None:
        """Test identifier generates UUID5-based ID."""
        track = Track(
            title="Scary Monsters and Nice Sprites",
            artist_list=["skrillex"],
            year=2010
        )
        # Should be 8-character hexadecimal string
        assert len(track.identifier) == 8
        assert all(c in "0123456789abcdef" for c in track.identifier)

    @staticmethod
    def test_identifier_is_deterministic() -> None:
        """Test identifier is deterministic (same track = same ID)."""
        track1 = Track(
            title="Scary Monsters and Nice Sprites",
            artist_list=["skrillex"],
            year=2010
        )
        track2 = Track(
            title="Scary Monsters and Nice Sprites",
            artist_list=["skrillex"],
            year=2010
        )
        # Same track should always produce same identifier
        assert track1.identifier == track2.identifier

    @staticmethod
    def test_identifier_is_stable_across_runs() -> None:
        """Test identifier remains stable across multiple instantiations."""
        # Create same track multiple times
        identifiers = [
            Track(
                title="16",
                artist_list=["blasterjaxx", "hardwell", "maddix"],
                year=2024
            ).identifier
            for _ in range(5)
        ]
        # All should be identical
        assert len(set(identifiers)) == 1

    @staticmethod
    def test_identifier_differs_for_different_tracks() -> None:
        """Test different tracks produce different identifiers."""
        track1 = Track(
            title="Track One",
            artist_list=["artist"],
            year=2024
        )
        track2 = Track(
            title="Track Two",
            artist_list=["artist"],
            year=2024
        )
        track3 = Track(
            title="Track One",
            artist_list=["different artist"],
            year=2024
        )
        track4 = Track(
            title="Track One",
            artist_list=["artist"],
            year=2023  # Different year
        )
        # All should have different identifiers
        ids = {track1.identifier, track2.identifier, track3.identifier, track4.identifier}
        assert len(ids) == 4

    @staticmethod
    def test_identifier_case_insensitive() -> None:
        """Test identifier is case-insensitive."""
        track1 = Track(
            title="Test Track",
            artist_list=["Artist Name"],
            year=2024
        )
        track2 = Track(
            title="test track",
            artist_list=["artist name"],
            year=2024
        )
        # Same content in different cases should produce same identifier
        assert track1.identifier == track2.identifier

    @staticmethod
    def test_legacy_identifier_format() -> None:
        """Test legacy_identifier uses old string concatenation format."""
        track = Track(
            title="Scary Monsters and Nice Sprites",
            artist_list=["skrillex"],
            year=2010
        )
        # Should use old format: "artist_title_year"
        assert track.legacy_identifier == "skrillex_scary_monsters_and_nice_sprites_2010"

    @staticmethod
    def test_legacy_identifier_vs_new_identifier() -> None:
        """Test legacy and new identifiers are different formats."""
        track = Track(
            title="Test Track",
            artist_list=["Artist Name"],
            year=2024
        )
        # Legacy should be long string, new should be 8-char UUID
        assert len(track.legacy_identifier) > 8
        assert len(track.identifier) == 8
        assert track.legacy_identifier != track.identifier

    @staticmethod
    def test_identifier_with_special_characters() -> None:
        """Test identifier handles special characters in title/artist."""
        track = Track(
            title="Track (feat. Artist)",
            artist_list=["Artist & Co."],
            year=2024
        )
        # Should still generate valid 8-char hex identifier
        assert len(track.identifier) == 8
        assert all(c in "0123456789abcdef" for c in track.identifier)

    @staticmethod
    def test_has_genre_method() -> None:
        """Test has_genre method for exact match."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024,
            genre=["hard techno", "techno"]
        )
        assert track.has_genre("hard techno") is True
        assert track.has_genre("techno") is True
        assert track.has_genre("house") is False

    @staticmethod
    def test_has_genre_case_insensitive() -> None:
        """Test has_genre is case-insensitive."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024,
            genre=["Hard Techno"]
        )
        assert track.has_genre("hard techno") is True
        assert track.has_genre("HARD TECHNO") is True
        assert track.has_genre("Hard Techno") is True

    @staticmethod
    def test_string_strip_whitespace() -> None:
        """Test string fields are automatically stripped."""
        track = Track(
            title="  Test  ",
            artist_list=["  artist  "],
            year=2024
        )
        assert track.title == "Test"
        assert track.artist_list == ["artist"]

    @staticmethod
    def test_json_serialization() -> None:
        """Test model can be serialized to JSON."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024,
            genre=["techno"]
        )
        json_str = track.model_dump_json()
        assert isinstance(json_str, str)

        # Verify it's valid JSON
        data = json.loads(json_str)
        assert data["title"] == "Test"
        assert data["year"] == 2024

    @staticmethod
    def test_json_deserialization() -> None:
        """Test model can be deserialized from JSON."""
        json_str = '{"title": "Test", "artist_list": ["artist"], "year": 2024}'
        track = Track.model_validate_json(json_str)
        assert track.title == "Test"
        assert track.artist_list == ["artist"]
        assert track.year == 2024

    @staticmethod
    def test_from_dict() -> None:
        """Test creating Track from dictionary."""
        data = {
            "title": "Test",
            "artist_list": ["artist1", "artist2"],
            "year": 2024,
            "genre": ["techno"]
        }
        track = Track(**data)
        assert track.title == "Test"
        assert track.artist_list == ["artist1", "artist2"]
        assert track.year == 2024
        assert track.genre == ["techno"]

    @staticmethod
    def test_model_dump_excludes_none() -> None:
        """Test model_dump excludes None values when requested."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
            # search_query is None
        )
        data = track.model_dump(exclude_none=True)
        assert "search_query" not in data
        assert "title" in data
        assert "grouping" in data  # grouping defaults to [], not None

    @staticmethod
    def test_validate_path_within_project() -> None:
        """Test path validation accepts paths within project."""
        # Path within project should be accepted
        valid_path = PROJECT_ROOT / "_data" / "test.json"
        validated = Track._validate_path(valid_path)
        assert validated == valid_path.resolve()

    @staticmethod
    def test_validate_path_rejects_traversal() -> None:
        """Test path validation rejects path traversal attempts."""
        # Path escaping project should be rejected
        with pytest.raises(ValueError, match="attempts to escape project directory"):
            Track._validate_path(Path("../../../etc/passwd"))

    @staticmethod
    def test_validate_path_rejects_absolute_outside() -> None:
        """Test path validation rejects absolute paths outside project."""
        # Absolute path outside project should be rejected
        with pytest.raises(ValueError, match="attempts to escape project directory"):
            Track._validate_path(Path("/tmp/malicious.json"))

    @staticmethod
    def test_to_json_file(tmp_path: Path) -> None:
        """Test saving Track to JSON file."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
        )

        # Mock PROJECT_ROOT to allow tmp_path
        with patch("msc.models.base.PROJECT_ROOT", tmp_path):
            output_path = tmp_path / "track.json"
            track.to_json_file(output_path)

            assert output_path.exists()

            # Verify content
            with open(output_path, encoding="utf-8") as f:
                data = json.load(f)

            assert data["title"] == "Test"
            assert data["year"] == 2024

    @staticmethod
    def test_to_json_file_creates_directories(tmp_path: Path) -> None:
        """Test to_json_file creates parent directories if they don't exist."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
        )

        # Mock PROJECT_ROOT to allow tmp_path
        with patch("msc.models.base.PROJECT_ROOT", tmp_path):
            # Path with non-existent parent directory
            output_path = tmp_path / "subdir" / "track.json"
            track.to_json_file(output_path)

            assert output_path.exists()
            assert output_path.parent.exists()

    @staticmethod
    def test_to_json_file_rejects_path_traversal() -> None:
        """Test to_json_file rejects path traversal attempts."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
        )

        # Attempt path traversal
        with pytest.raises(ValueError, match="attempts to escape project directory"):
            track.to_json_file(Path("../../../etc/passwd"))

    @staticmethod
    def test_from_json_file(tmp_path: Path) -> None:
        """Test loading Track from JSON file."""
        # Create test file
        data = {
            "title": "Test",
            "artist_list": ["artist"],
            "year": 2024,
            "genre": ["techno"]
        }

        # Mock PROJECT_ROOT to allow tmp_path
        with patch("msc.models.base.PROJECT_ROOT", tmp_path):
            input_path = tmp_path / "track.json"
            with open(input_path, "w", encoding="utf-8") as f:
                json.dump(data, f)

            # Load and verify
            track = Track.from_json_file(input_path)
            assert track.title == "Test"
            assert track.artist_list == ["artist"]
            assert track.year == 2024
            assert track.genre == ["techno"]

    @staticmethod
    def test_from_json_file_not_found(tmp_path: Path) -> None:
        """Test from_json_file raises FileNotFoundError for missing file."""
        # Mock PROJECT_ROOT to allow tmp_path
        with patch("msc.models.base.PROJECT_ROOT", tmp_path), pytest.raises(FileNotFoundError, match="File not found"):
            Track.from_json_file(tmp_path / "nonexistent.json")

    @staticmethod
    def test_from_json_file_rejects_path_traversal() -> None:
        """Test from_json_file rejects path traversal attempts."""
        # Attempt path traversal
        with pytest.raises(ValueError, match="attempts to escape project directory"):
            Track.from_json_file(Path("../../../etc/passwd"))

    @staticmethod
    def test_full_track_with_all_fields() -> None:
        """Test creating Track with all optional fields populated."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024,
            genre=["hard techno"],
            grouping=["revealed"],
            search_query="blasterjaxx, hardwell, maddix 16"
        )
        assert track.title == "16"
        assert track.artist_list == ["blasterjaxx", "hardwell", "maddix"]
        assert track.year == 2024
        assert track.genre == ["hard techno"]
        assert track.grouping == ["revealed"]
        assert track.search_query == "blasterjaxx, hardwell, maddix 16"


class TestSongstatsIdentifiers:
    """Tests for SongstatsIdentifiers model."""

    @staticmethod
    def test_create_valid_identifiers() -> None:
        """Test creating valid SongstatsIdentifiers."""
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        assert ids.songstats_id == "qmr6e0bx"
        assert ids.songstats_title == "16"

    @staticmethod
    def test_alias_s_id() -> None:
        """Test songstats_id can be set via 's_id' alias."""
        # Using field name
        ids1 = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )
        assert ids1.songstats_id == "abc123"

        # Using alias
        ids2 = SongstatsIdentifiers(
            s_id="abc123",
            s_title="Test"
        )
        assert ids2.songstats_id == "abc123"

    @staticmethod
    def test_alias_s_title() -> None:
        """Test songstats_title can be set via 's_title' alias."""
        ids = SongstatsIdentifiers(
            s_id="abc123",
            s_title="Test Track"
        )
        assert ids.songstats_title == "Test Track"

    @staticmethod
    def test_isrc_optional() -> None:
        """Test isrc is optional and defaults to None."""
        ids = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )
        assert ids.isrc is None

    @staticmethod
    def test_isrc_can_be_set() -> None:
        """Test isrc can be provided."""
        ids = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test",
            isrc="USRC17607839"
        )
        assert ids.isrc == "USRC17607839"

    @staticmethod
    def test_frozen_model() -> None:
        """Test SongstatsIdentifiers is immutable (frozen)."""
        ids = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )

        with pytest.raises(ValidationError):
            ids.songstats_id = "new_id"

    @staticmethod
    def test_songstats_id_required() -> None:
        """Test songstats_id is required."""
        with pytest.raises(ValidationError) as exc_info:
            SongstatsIdentifiers(songstats_title="Test")

        errors = exc_info.value.errors()
        # Check for either field name or alias
        assert any(e["loc"] in [("songstats_id",), ("s_id",)] for e in errors)

    @staticmethod
    def test_songstats_title_required() -> None:
        """Test songstats_title is required."""
        with pytest.raises(ValidationError) as exc_info:
            SongstatsIdentifiers(songstats_id="abc123")

        errors = exc_info.value.errors()
        # Check for either field name or alias
        assert any(e["loc"] in [("songstats_title",), ("s_title",)] for e in errors)

    @staticmethod
    def test_json_serialization() -> None:
        """Test identifiers can be serialized to JSON."""
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        json_str = ids.model_dump_json()
        data = json.loads(json_str)
        assert data["songstats_id"] == "qmr6e0bx"
        assert data["songstats_title"] == "16"

    @staticmethod
    def test_json_deserialization_with_aliases() -> None:
        """Test identifiers can be loaded from JSON with aliases."""
        # Legacy format with s_id/s_title
        json_str = '{"s_id": "qmr6e0bx", "s_title": "16"}'
        ids = SongstatsIdentifiers.model_validate_json(json_str)
        assert ids.songstats_id == "qmr6e0bx"
        assert ids.songstats_title == "16"

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        data = ids.model_dump(by_alias=True)
        assert "s_id" in data
        assert "s_title" in data
        assert data["s_id"] == "qmr6e0bx"
        assert data["s_title"] == "16"

    @staticmethod
    def test_string_strip_whitespace() -> None:
        """Test string fields are automatically stripped."""
        ids = SongstatsIdentifiers(
            songstats_id="  abc123  ",
            songstats_title="  Test  "
        )
        assert ids.songstats_id == "abc123"
        assert ids.songstats_title == "Test"

    @staticmethod
    def test_to_flat_dict() -> None:
        """Test to_flat_dict method from base model."""
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        flat = ids.to_flat_dict()
        assert "s_id" in flat
        assert "s_title" in flat
        assert flat["s_id"] == "qmr6e0bx"
        assert flat["s_title"] == "16"
