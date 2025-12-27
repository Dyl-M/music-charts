"""Unit tests for track models.

Tests Track and SongstatsIdentifiers models.
"""

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.track import SongstatsIdentifiers, Track


class TestTrackCreation:
    """Tests for Track model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create track with only required fields."""
        track = Track(
            title="test track",
            artist_list=["artist"],
            year=2024,
        )
        assert track.title == "test track"
        assert track.artist_list == ["artist"]
        assert track.year == 2024

    @staticmethod
    def test_defaults_genre_to_empty_list() -> None:
        """Should default genre to empty list."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.genre == []

    @staticmethod
    def test_defaults_grouping_to_empty_list() -> None:
        """Should default grouping to empty list."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.grouping == []

    @staticmethod
    def test_defaults_search_query_to_none() -> None:
        """Should default search_query to None."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.search_query is None

    @staticmethod
    def test_creates_with_all_fields() -> None:
        """Should create track with all optional fields."""
        track = Track(
            title="complete track",
            artist_list=["artist a", "artist b"],
            year=2024,
            genre=["house"],
            grouping=["label"],
            search_query="search query",
        )
        assert track.genre == ["house"]
        assert track.grouping == ["label"]
        assert track.search_query == "search query"


class TestTrackValidation:
    """Tests for Track field validation."""

    @staticmethod
    def test_requires_artist_list() -> None:
        """Should require at least one artist."""
        with pytest.raises(ValidationError, match="artist_list"):
            Track(title="test", artist_list=[], year=2024)

    @staticmethod
    def test_validates_year_minimum() -> None:
        """Should reject year below 1900."""
        with pytest.raises(ValidationError):
            Track(title="test", artist_list=["artist"], year=1899)

    @staticmethod
    def test_validates_year_maximum() -> None:
        """Should reject year above 2100."""
        with pytest.raises(ValidationError):
            Track(title="test", artist_list=["artist"], year=2101)

    @staticmethod
    def test_accepts_valid_year_range() -> None:
        """Should accept years in valid range."""
        track1 = Track(title="test", artist_list=["artist"], year=1900)
        track2 = Track(title="test", artist_list=["artist"], year=2100)
        assert track1.year == 1900
        assert track2.year == 2100


class TestTrackImmutability:
    """Tests for Track immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        with pytest.raises(ValidationError):
            track.title = "new title"  # type: ignore[misc]

    @staticmethod
    def test_equality_works() -> None:
        """Should support equality comparison."""
        track1 = Track(title="test", artist_list=["artist"], year=2024)
        track2 = Track(title="test", artist_list=["artist"], year=2024)
        assert track1 == track2


class TestTrackGroupingField:
    """Tests for grouping field behavior."""

    @staticmethod
    def test_accepts_list_grouping() -> None:
        """Should accept list grouping."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            grouping=["label a", "label b"],
        )
        assert track.grouping == ["label a", "label b"]

    @staticmethod
    def test_accepts_empty_list() -> None:
        """Should accept empty list."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            grouping=[],
        )
        assert track.grouping == []

    @staticmethod
    def test_defaults_to_empty_list() -> None:
        """Should default to empty list when not provided."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.grouping == []


class TestTrackGroupingValidator:
    """Tests for Track.validate_grouping validator."""

    @staticmethod
    def test_converts_none_to_empty_list() -> None:
        """Should convert None to empty list for backward compatibility."""
        # Pydantic will pass None through the validator when loading from JSON
        track = Track.model_validate({
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "grouping": None,
        })
        assert track.grouping == []

    @staticmethod
    def test_converts_string_to_single_item_list() -> None:
        """Should convert string to single-item list for backward compatibility."""
        # Old data might have grouping as a single string
        track = Track.model_validate({
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "grouping": "single label",
        })
        assert track.grouping == ["single label"]

    @staticmethod
    def test_passes_through_list_unchanged() -> None:
        """Should pass through list unchanged."""
        track = Track.model_validate({
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "grouping": ["label a", "label b"],
        })
        assert track.grouping == ["label a", "label b"]


class TestTrackProperties:
    """Tests for Track computed properties."""

    @staticmethod
    def test_primary_artist() -> None:
        """Should return first artist."""
        track = Track(
            title="test",
            artist_list=["artist a", "artist b", "artist c"],
            year=2024,
        )
        assert track.primary_artist == "artist a"

    @staticmethod
    def test_all_artists_string() -> None:
        """Should return comma-separated artists."""
        track = Track(
            title="test",
            artist_list=["artist a", "artist b", "artist c"],
            year=2024,
        )
        assert track.all_artists_string == "artist a, artist b, artist c"

    @staticmethod
    def test_all_artists_string_single_artist() -> None:
        """Should handle single artist."""
        track = Track(title="test", artist_list=["solo artist"], year=2024)
        assert track.all_artists_string == "solo artist"


class TestTrackIdentifier:
    """Tests for Track.identifier property (UUID5-based)."""

    @staticmethod
    def test_returns_8_char_string() -> None:
        """Should return 8-character identifier."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert len(track.identifier) == 8
        assert isinstance(track.identifier, str)

    @staticmethod
    def test_is_deterministic() -> None:
        """Should produce same ID for identical tracks."""
        track1 = Track(title="test track", artist_list=["artist"], year=2024)
        track2 = Track(title="test track", artist_list=["artist"], year=2024)
        assert track1.identifier == track2.identifier

    @staticmethod
    def test_differs_for_different_artists() -> None:
        """Should produce different IDs for different artists."""
        track1 = Track(title="test", artist_list=["artist a"], year=2024)
        track2 = Track(title="test", artist_list=["artist b"], year=2024)
        assert track1.identifier != track2.identifier

    @staticmethod
    def test_differs_for_different_titles() -> None:
        """Should produce different IDs for different titles."""
        track1 = Track(title="title a", artist_list=["artist"], year=2024)
        track2 = Track(title="title b", artist_list=["artist"], year=2024)
        assert track1.identifier != track2.identifier

    @staticmethod
    def test_differs_for_different_years() -> None:
        """Should produce different IDs for different years."""
        track1 = Track(title="test", artist_list=["artist"], year=2024)
        track2 = Track(title="test", artist_list=["artist"], year=2023)
        assert track1.identifier != track2.identifier

    @staticmethod
    def test_uses_primary_artist_only() -> None:
        """Should only use primary artist for ID."""
        track1 = Track(title="test", artist_list=["artist a"], year=2024)
        track2 = Track(title="test", artist_list=["artist a", "artist b"], year=2024)
        assert track1.identifier == track2.identifier

    @staticmethod
    def test_is_case_insensitive() -> None:
        """Should produce same ID regardless of case."""
        track1 = Track(title="TEST TRACK", artist_list=["ARTIST"], year=2024)
        track2 = Track(title="test track", artist_list=["artist"], year=2024)
        assert track1.identifier == track2.identifier


class TestTrackLegacyIdentifier:
    """Tests for Track.legacy_identifier property."""

    @staticmethod
    def test_format() -> None:
        """Should return artist_title_year format."""
        track = Track(title="test track", artist_list=["artist"], year=2024)
        assert track.legacy_identifier == "artist_test_track_2024"

    @staticmethod
    def test_replaces_spaces_with_underscores() -> None:
        """Should replace spaces with underscores."""
        track = Track(title="multi word title", artist_list=["multi word artist"], year=2024)
        assert "_" in track.legacy_identifier
        assert " " not in track.legacy_identifier

    @staticmethod
    def test_is_lowercase() -> None:
        """Should be lowercase."""
        track = Track(title="TEST TITLE", artist_list=["ARTIST"], year=2024)
        assert track.legacy_identifier.islower()


class TestTrackHasGenre:
    """Tests for Track.has_genre method."""

    @staticmethod
    def test_returns_true_for_matching_genre() -> None:
        """Should return True when genre matches."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            genre=["house", "tech house"],
        )
        assert track.has_genre("house") is True

    @staticmethod
    def test_returns_false_for_non_matching_genre() -> None:
        """Should return False when genre doesn't match."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            genre=["house"],
        )
        assert track.has_genre("techno") is False

    @staticmethod
    def test_is_case_insensitive() -> None:
        """Should match genre case-insensitively."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            genre=["Tech House"],
        )
        assert track.has_genre("tech house") is True
        assert track.has_genre("TECH HOUSE") is True

    @staticmethod
    def test_empty_genre_list() -> None:
        """Should return False for empty genre list."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.has_genre("house") is False


class TestTrackLegacyAlias:
    """Tests for Track search_query alias."""

    @staticmethod
    def test_accepts_request_alias() -> None:
        """Should accept 'request' as alias for search_query."""
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            request="search query",  # type: ignore[call-arg]
        )
        assert track.search_query == "search query"


class TestSongstatsIdentifiersCreation:
    """Tests for SongstatsIdentifiers model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with required fields."""
        ids = SongstatsIdentifiers(
            songstats_id="abc12345",
            songstats_title="Test Title",
        )
        assert ids.songstats_id == "abc12345"
        assert ids.songstats_title == "Test Title"

    @staticmethod
    def test_defaults_isrc_to_none() -> None:
        """Should default ISRC to None."""
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        assert ids.isrc is None

    @staticmethod
    def test_defaults_artists_to_empty_list() -> None:
        """Should default artists to empty list."""
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        assert ids.songstats_artists == []

    @staticmethod
    def test_defaults_labels_to_empty_list() -> None:
        """Should default labels to empty list."""
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        assert ids.songstats_labels == []


class TestSongstatsIdentifiersAliases:
    """Tests for SongstatsIdentifiers legacy aliases."""

    @staticmethod
    def test_accepts_s_id_alias() -> None:
        """Should accept 's_id' as alias for songstats_id."""
        ids = SongstatsIdentifiers(s_id="abc", s_title="Title")  # type: ignore[call-arg]
        assert ids.songstats_id == "abc"

    @staticmethod
    def test_accepts_s_title_alias() -> None:
        """Should accept 's_title' as alias for songstats_title."""
        ids = SongstatsIdentifiers(s_id="abc", s_title="Title")  # type: ignore[call-arg]
        assert ids.songstats_title == "Title"


class TestSongstatsIdentifiersImmutability:
    """Tests for SongstatsIdentifiers immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        with pytest.raises(ValidationError):
            ids.songstats_id = "new_id"  # type: ignore[misc]

    @staticmethod
    def test_equality_works() -> None:
        """Should support equality comparison."""
        ids1 = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        ids2 = SongstatsIdentifiers(songstats_id="abc", songstats_title="Title")
        assert ids1 == ids2


class TestTrackWithSongstatsIdentifiers:
    """Tests for Track with embedded SongstatsIdentifiers."""

    @staticmethod
    def test_creates_with_default_identifiers() -> None:
        """Should create with default empty identifiers."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        assert track.songstats_identifiers.songstats_id == ""
        assert track.songstats_identifiers.songstats_title == ""

    @staticmethod
    def test_creates_with_provided_identifiers() -> None:
        """Should create with provided identifiers."""
        ids = SongstatsIdentifiers(songstats_id="xyz", songstats_title="Title")
        track = Track(
            title="test",
            artist_list=["artist"],
            year=2024,
            songstats_identifiers=ids,
        )
        assert track.songstats_identifiers.songstats_id == "xyz"
