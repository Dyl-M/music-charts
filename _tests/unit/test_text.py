"""Unit tests for text utilities."""

# Local
from msc.utils.text import (
    build_search_query,
    format_artist,
    format_title,
    normalize_genre,
    normalize_label,
    remove_remixer,
    truncate,
)


class TestFormatTitle:
    """Tests for the format_title function."""

    @staticmethod
    def test_removes_extended_mix() -> None:
        """Should remove [Extended Mix] suffix."""
        assert format_title("Song Name [Extended Mix]") == "song name"

    @staticmethod
    def test_removes_extended() -> None:
        """Should remove [Extended] suffix."""
        assert format_title("All I Need [Extended]") == "all i need"

    @staticmethod
    def test_removes_original_mix() -> None:
        """Should remove [Original Mix] suffix."""
        assert format_title("Track Title [Original Mix]") == "track title"

    @staticmethod
    def test_removes_remix_tag() -> None:
        """Should remove [Remix] suffix."""
        assert format_title("Another Song [Remix]") == "another song"

    @staticmethod
    def test_removes_brackets() -> None:
        """Should remove standalone brackets."""
        assert format_title("Song [Something]") == "song something"

    @staticmethod
    def test_removes_parentheses() -> None:
        """Should remove parentheses."""
        assert format_title("Song (feat. Artist)") == "song feat artist"

    @staticmethod
    def test_removes_question_mark() -> None:
        """Should remove question marks."""
        assert format_title("Why?") == "why"

    @staticmethod
    def test_removes_exclamation_mark() -> None:
        """Should remove exclamation marks."""
        assert format_title("Feel It!") == "feel it"

    @staticmethod
    def test_keeps_apostrophe() -> None:
        """Should keep apostrophes as they are semantically important."""
        assert format_title("Don't Stop") == "don't stop"

    @staticmethod
    def test_removes_comma() -> None:
        """Should remove commas."""
        assert format_title("One, Two, Three") == "one two three"

    @staticmethod
    def test_removes_period() -> None:
        """Should remove periods."""
        assert format_title("Dr. Dre") == "dr dre"

    @staticmethod
    def test_replaces_cross_symbol_with_space() -> None:
        """Should replace × with space."""
        assert format_title("Artist A × Artist B") == "artist a artist b"

    @staticmethod
    def test_replaces_comma_with_space() -> None:
        """Should replace comma-space with space."""
        result = format_title("One, Two, Three")
        assert "," not in result

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert to lowercase."""
        assert format_title("UPPERCASE TITLE") == "uppercase title"

    @staticmethod
    def test_strips_whitespace() -> None:
        """Should strip leading/trailing whitespace."""
        assert format_title("  Title With Spaces  ") == "title with spaces"

    @staticmethod
    def test_empty_string() -> None:
        """Should handle empty string."""
        assert format_title("") == ""


class TestFormatArtist:
    """Tests for the format_artist function."""

    @staticmethod
    def test_removes_feat_annotation_parentheses() -> None:
        """Should remove (feat. ...) annotations - featured artists cause query mismatches."""
        assert format_artist("Artist A (feat. Artist B)") == "artist a"

    @staticmethod
    def test_removes_feat_annotation_brackets() -> None:
        """Should remove [feat. ...] annotations - featured artists cause query mismatches."""
        assert format_artist("Artist A [feat. Artist B]") == "artist a"

    @staticmethod
    def test_removes_ft_annotation() -> None:
        """Should remove (ft. ...) annotations - featured artists cause query mismatches."""
        assert format_artist("Artist A (ft. Artist B)") == "artist a"

    @staticmethod
    def test_removes_featuring_annotation() -> None:
        """Should remove (featuring ...) annotations - featured artists cause query mismatches."""
        assert format_artist("Artist A (featuring Artist B)") == "artist a"

    @staticmethod
    def test_case_insensitive_feat() -> None:
        """Should handle case variations of feat."""
        assert format_artist("Artist A (FEAT. Artist B)") == "artist a"
        assert format_artist("Artist A (Feat. Artist B)") == "artist a"

    @staticmethod
    def test_replaces_multiplication_sign() -> None:
        """Should replace × with space."""
        assert format_artist("Artist A × Artist B") == "artist a artist b"

    @staticmethod
    def test_replaces_ampersand() -> None:
        """Should replace & with space."""
        assert format_artist("Artist A & Artist B") == "artist a artist b"

    @staticmethod
    def test_removes_parentheses() -> None:
        """Should remove remaining parentheses."""
        assert format_artist("Artist (Name)") == "artist name"

    @staticmethod
    def test_removes_brackets() -> None:
        """Should remove remaining brackets."""
        assert format_artist("Artist [Name]") == "artist name"

    @staticmethod
    def test_normalizes_whitespace() -> None:
        """Should normalize multiple spaces to single space."""
        assert format_artist("Artist   A    &    Artist   B") == "artist a artist b"

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert to lowercase."""
        assert format_artist("UPPERCASE ARTIST") == "uppercase artist"

    @staticmethod
    def test_strips_whitespace() -> None:
        """Should strip leading/trailing whitespace."""
        assert format_artist("  Artist Name  ") == "artist name"

    @staticmethod
    def test_complex_real_world_case() -> None:
        """Should handle complex real-world artist names."""
        assert format_artist("Oliverse & MØØNE") == "oliverse møøne"
        assert format_artist("RIENK × Lukher") == "rienk lukher"
        assert format_artist("ROY KNOX & Austin Christopher (feat. Stephanie Schulte)") == "roy knox austin christopher"
        assert format_artist("Andromedik (feat. Lauren L'aimant)") == "andromedik"

    @staticmethod
    def test_empty_string() -> None:
        """Should handle empty string."""
        assert format_artist("") == ""


class TestRemoveRemixer:
    """Tests for the remove_remixer function."""

    @staticmethod
    def test_removes_remixer_from_list() -> None:
        """Should remove artist whose name appears in title."""
        result = remove_remixer(
            "original song (artist b remix)",
            ["artist a", "artist b"]
        )
        assert result == ["artist a"]

    @staticmethod
    def test_keeps_all_when_no_match() -> None:
        """Should keep all artists when none appear in title."""
        result = remove_remixer(
            "song title",
            ["artist a", "artist b"]
        )
        assert result == ["artist a", "artist b"]

    @staticmethod
    def test_case_insensitive() -> None:
        """Should be case-insensitive when matching."""
        result = remove_remixer(
            "Song (ARTIST B Remix)",
            ["artist a", "artist b"]
        )
        assert result == ["artist a"]

    @staticmethod
    def test_empty_list() -> None:
        """Should handle empty artist list."""
        result = remove_remixer("song title", [])
        assert result == []


class TestBuildSearchQuery:
    """Tests for the build_search_query function."""

    @staticmethod
    def test_combines_artists_and_title() -> None:
        """Should combine artists and title into query."""
        result = build_search_query("song name", ["artist a", "artist b"])
        assert result == "artist a artist b song name"

    @staticmethod
    def test_single_artist() -> None:
        """Should handle single artist."""
        result = build_search_query("song name", ["artist"])
        assert result == "artist song name"

    @staticmethod
    def test_empty_artists() -> None:
        """Should handle empty artist list."""
        result = build_search_query("song name", [])
        assert result == "song name"

    @staticmethod
    def test_cleans_artist_names_with_feat() -> None:
        """Should remove featured artists from annotations to avoid query mismatches."""
        result = build_search_query("song name", ["Artist A (feat. Artist B)"])
        assert result == "artist a song name"

    @staticmethod
    def test_cleans_artist_names_with_special_chars() -> None:
        """Should clean artist names with special characters."""
        result = build_search_query("song name", ["Artist A × Artist B"])
        assert result == "artist a artist b song name"

    @staticmethod
    def test_cleans_multiple_artists_with_ampersand() -> None:
        """Should clean artist names with ampersand."""
        result = build_search_query("song name", ["Artist A & Artist B"])
        assert result == "artist a artist b song name"

    @staticmethod
    def test_real_world_complex_query() -> None:
        """Should handle real-world complex artist names."""
        result = build_search_query("adrenaline", ["Oliverse & MØØNE"])
        assert result == "oliverse møøne adrenaline"


class TestNormalize:
    """Tests for normalization functions."""

    @staticmethod
    def test_normalize_label() -> None:
        """Should lowercase and strip label."""
        assert normalize_label("  Sample Records  ") == "sample records"

    @staticmethod
    def test_normalize_genre() -> None:
        """Should lowercase and strip genre."""
        assert normalize_genre("  Progressive House  ") == "progressive house"


class TestTruncate:
    """Tests for the truncate function."""

    @staticmethod
    def test_no_truncation_needed() -> None:
        """Should return original if within limit."""
        assert truncate("short", 10) == "short"

    @staticmethod
    def test_truncates_long_text() -> None:
        """Should truncate text exceeding limit."""
        result = truncate("this is a very long text", 10)
        assert len(result) == 10
        assert result.endswith("...")

    @staticmethod
    def test_custom_suffix() -> None:
        """Should use custom suffix."""
        result = truncate("long text here", 10, suffix="…")
        assert result.endswith("…")

    @staticmethod
    def test_exact_length() -> None:
        """Should not truncate at exact length."""
        assert truncate("exact", 5) == "exact"
