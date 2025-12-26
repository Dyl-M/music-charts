"""Unit tests for text processing utilities.

Tests format_title, format_artist, build_search_query, remove_remixer,
normalize_label, normalize_genre, and truncate functions.
"""

# Third-party
import pytest

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
    """Tests for format_title function."""

    @staticmethod
    def test_removes_extended_mix_suffix() -> None:
        """Should remove [Extended Mix] suffix."""
        result = format_title("Song Name [Extended Mix]")
        assert result == "song name"

    @staticmethod
    def test_removes_original_mix_suffix() -> None:
        """Should remove [Original Mix] suffix."""
        result = format_title("Song Name [Original Mix]")
        assert result == "song name"

    @staticmethod
    def test_removes_extended_suffix() -> None:
        """Should remove [Extended] suffix."""
        result = format_title("Song Name [Extended]")
        assert result == "song name"

    @staticmethod
    def test_removes_remix_suffix() -> None:
        """Should remove [Remix] suffix."""
        result = format_title("Song Name [Remix]")
        assert result == "song name"

    @staticmethod
    def test_removes_question_mark() -> None:
        """Should remove question mark characters."""
        result = format_title("Song Name?")
        assert "?" not in result

    @staticmethod
    def test_removes_exclamation_mark() -> None:
        """Should remove exclamation mark characters."""
        result = format_title("Song Name!")
        assert "!" not in result

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert title to lowercase."""
        result = format_title("SONG NAME")
        assert result == "song name"

    @staticmethod
    def test_replaces_multiplication_sign_with_space() -> None:
        """Should replace × with space."""
        result = format_title("Artist A × Artist B")
        assert "×" not in result
        assert "artist a" in result
        assert "artist b" in result

    @staticmethod
    def test_replaces_ampersand_with_space() -> None:
        """Should replace & with space."""
        result = format_title("Artist A & Artist B")
        assert "&" not in result

    @staticmethod
    def test_strips_whitespace() -> None:
        """Should strip leading and trailing whitespace."""
        result = format_title("  Song Name  ")
        assert result == "song name"

    @staticmethod
    def test_handles_empty_string() -> None:
        """Should handle empty string input."""
        result = format_title("")
        assert result == ""

    @staticmethod
    def test_preserves_title_without_patterns() -> None:
        """Should preserve title when no patterns match."""
        result = format_title("Simple Title")
        assert result == "simple title"

    @staticmethod
    def test_removes_punctuation() -> None:
        """Should remove punctuation like periods and commas."""
        result = format_title("Song Name, Vol. 1")
        assert "," not in result
        assert "." not in result

    @staticmethod
    def test_case_insensitive_pattern_removal() -> None:
        """Should remove patterns regardless of case."""
        result = format_title("Song Name [EXTENDED MIX]")
        assert result == "song name"


class TestRemoveRemixer:
    """Tests for remove_remixer function."""

    @staticmethod
    def test_removes_remixer_from_artist_list() -> None:
        """Should remove artist that appears in title."""
        result = remove_remixer(
            "Original Song (Artist B Remix)", ["Artist A", "Artist B"]
        )
        assert result == ["Artist A"]

    @staticmethod
    def test_keeps_all_artists_when_no_remixer() -> None:
        """Should keep all artists when none appear in title."""
        result = remove_remixer("Original Song", ["Artist A", "Artist B"])
        assert result == ["Artist A", "Artist B"]

    @staticmethod
    def test_case_insensitive_matching() -> None:
        """Should match remixer case-insensitively."""
        result = remove_remixer(
            "original song (artist b remix)", ["Artist A", "Artist B"]
        )
        assert result == ["Artist A"]

    @staticmethod
    def test_handles_empty_artist_list() -> None:
        """Should handle empty artist list."""
        result = remove_remixer("Song Title", [])
        assert result == []

    @staticmethod
    def test_removes_multiple_remixers() -> None:
        """Should remove multiple artists that appear in title."""
        result = remove_remixer(
            "Song (Artist A & Artist B Remix)", ["Artist A", "Artist B", "Artist C"]
        )
        assert result == ["Artist C"]


class TestFormatArtist:
    """Tests for format_artist function."""

    @staticmethod
    def test_removes_featuring_annotation() -> None:
        """Should remove (feat. ...) annotation."""
        result = format_artist("Artist A (feat. Artist B)")
        assert result == "artist a"

    @staticmethod
    def test_removes_ft_annotation() -> None:
        """Should remove (ft. ...) annotation."""
        result = format_artist("Artist A (ft. Artist B)")
        assert result == "artist a"

    @staticmethod
    def test_removes_featuring_in_brackets() -> None:
        """Should remove [feat. ...] annotation."""
        result = format_artist("Artist A [feat. Artist B]")
        assert result == "artist a"

    @staticmethod
    def test_replaces_multiplication_sign() -> None:
        """Should replace × with space."""
        result = format_artist("Artist A × Artist B")
        assert result == "artist a artist b"

    @staticmethod
    def test_replaces_ampersand() -> None:
        """Should replace & with space."""
        result = format_artist("Artist A & Artist B")
        assert result == "artist a artist b"

    @staticmethod
    def test_removes_parentheses() -> None:
        """Should remove remaining parentheses."""
        result = format_artist("Artist (Live)")
        assert result == "artist live"

    @staticmethod
    def test_removes_square_brackets() -> None:
        """Should remove square brackets."""
        result = format_artist("Artist [DJ]")
        assert result == "artist dj"

    @staticmethod
    def test_normalizes_whitespace() -> None:
        """Should normalize multiple spaces to single space."""
        result = format_artist("Artist   A")
        assert result == "artist a"

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert to lowercase."""
        result = format_artist("ARTIST NAME")
        assert result == "artist name"

    @staticmethod
    def test_handles_empty_string() -> None:
        """Should handle empty string."""
        result = format_artist("")
        assert result == ""


class TestBuildSearchQuery:
    """Tests for build_search_query function."""

    @staticmethod
    def test_combines_artists_and_title() -> None:
        """Should combine artists and title with space."""
        result = build_search_query("song name", ["artist a", "artist b"])
        assert result == "artist a artist b song name"

    @staticmethod
    def test_single_artist() -> None:
        """Should handle single artist."""
        result = build_search_query("song name", ["artist a"])
        assert result == "artist a song name"

    @staticmethod
    def test_empty_artist_list() -> None:
        """Should handle empty artist list."""
        result = build_search_query("song name", [])
        assert result == "song name"

    @staticmethod
    def test_cleans_artist_names() -> None:
        """Should clean artist names with format_artist."""
        result = build_search_query("song", ["Artist A (feat. B)"])
        assert result == "artist a song"

    @staticmethod
    def test_strips_result() -> None:
        """Should strip whitespace from result."""
        result = build_search_query("song", [])
        assert result == "song"


class TestNormalizeLabel:
    """Tests for normalize_label function."""

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert label to lowercase."""
        result = normalize_label("Sample Records")
        assert result == "sample records"

    @staticmethod
    def test_strips_whitespace() -> None:
        """Should strip leading and trailing whitespace."""
        result = normalize_label("  Sample Records  ")
        assert result == "sample records"

    @staticmethod
    def test_handles_empty_string() -> None:
        """Should handle empty string."""
        result = normalize_label("")
        assert result == ""


class TestNormalizeGenre:
    """Tests for normalize_genre function."""

    @staticmethod
    def test_converts_to_lowercase() -> None:
        """Should convert genre to lowercase."""
        result = normalize_genre("House")
        assert result == "house"

    @staticmethod
    def test_strips_whitespace() -> None:
        """Should strip leading and trailing whitespace."""
        result = normalize_genre("  Tech House  ")
        assert result == "tech house"

    @staticmethod
    def test_handles_empty_string() -> None:
        """Should handle empty string."""
        result = normalize_genre("")
        assert result == ""


class TestTruncate:
    """Tests for truncate function."""

    @staticmethod
    def test_returns_short_text_unchanged() -> None:
        """Should return text unchanged if within limit."""
        result = truncate("short", max_length=50)
        assert result == "short"

    @staticmethod
    def test_truncates_long_text() -> None:
        """Should truncate text longer than limit."""
        result = truncate("this is a very long text", max_length=10)
        assert len(result) == 10
        assert result.endswith("...")

    @staticmethod
    def test_default_suffix() -> None:
        """Should use ... as default suffix."""
        result = truncate("this is a very long text", max_length=10)
        assert result == "this is..."

    @staticmethod
    def test_custom_suffix() -> None:
        """Should use custom suffix when provided."""
        result = truncate("this is a very long text", max_length=10, suffix="~")
        assert result == "this is a~"

    @staticmethod
    def test_exact_length() -> None:
        """Should handle text exactly at limit."""
        result = truncate("12345", max_length=5)
        assert result == "12345"

    @staticmethod
    def test_empty_string() -> None:
        """Should handle empty string."""
        result = truncate("", max_length=10)
        assert result == ""

    @staticmethod
    @pytest.mark.parametrize(
        "text,max_length,expected",
        [
            ("hello", 5, "hello"),
            ("hello world", 8, "hello..."),
            ("a" * 100, 20, "a" * 17 + "..."),
        ],
    )
    def test_parametrized_truncation(text: str, max_length: int, expected: str) -> None:
        """Should correctly truncate various inputs."""
        result = truncate(text, max_length=max_length)
        assert result == expected
