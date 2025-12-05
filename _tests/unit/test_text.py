"""Unit tests for text utilities."""

import pytest

from msc.utils.text import (
    format_title,
    remove_remixer,
    build_search_query,
    normalize_label,
    normalize_genre,
    truncate,
)


class TestFormatTitle:
    """Tests for the format_title function."""

    def test_removes_extended_mix(self) -> None:
        """Should remove [Extended Mix] suffix."""
        assert format_title("Song Name [Extended Mix]") == "song name"

    def test_removes_original_mix(self) -> None:
        """Should remove [Original Mix] suffix."""
        assert format_title("Track Title [Original Mix]") == "track title"

    def test_removes_remix_tag(self) -> None:
        """Should remove [Remix] suffix."""
        assert format_title("Another Song [Remix]") == "another song"

    def test_removes_brackets(self) -> None:
        """Should remove standalone brackets."""
        assert format_title("Song [Something]") == "song something"

    def test_removes_parentheses(self) -> None:
        """Should remove parentheses."""
        assert format_title("Song (feat. Artist)") == "song feat. artist"

    def test_removes_question_mark(self) -> None:
        """Should remove question marks."""
        assert format_title("Why?") == "why"

    def test_replaces_cross_symbol_with_space(self) -> None:
        """Should replace × with space."""
        assert format_title("Artist A × Artist B") == "artist a  artist b"

    def test_replaces_comma_with_space(self) -> None:
        """Should replace comma-space with space."""
        result = format_title("One, Two, Three")
        assert "," not in result

    def test_converts_to_lowercase(self) -> None:
        """Should convert to lowercase."""
        assert format_title("UPPERCASE TITLE") == "uppercase title"

    def test_strips_whitespace(self) -> None:
        """Should strip leading/trailing whitespace."""
        assert format_title("  Title With Spaces  ") == "title with spaces"

    def test_empty_string(self) -> None:
        """Should handle empty string."""
        assert format_title("") == ""


class TestRemoveRemixer:
    """Tests for the remove_remixer function."""

    def test_removes_remixer_from_list(self) -> None:
        """Should remove artist whose name appears in title."""
        result = remove_remixer(
            "original song (artist b remix)",
            ["artist a", "artist b"]
        )
        assert result == ["artist a"]

    def test_keeps_all_when_no_match(self) -> None:
        """Should keep all artists when none appear in title."""
        result = remove_remixer(
            "song title",
            ["artist a", "artist b"]
        )
        assert result == ["artist a", "artist b"]

    def test_case_insensitive(self) -> None:
        """Should be case-insensitive when matching."""
        result = remove_remixer(
            "Song (ARTIST B Remix)",
            ["artist a", "artist b"]
        )
        assert result == ["artist a"]

    def test_empty_list(self) -> None:
        """Should handle empty artist list."""
        result = remove_remixer("song title", [])
        assert result == []


class TestBuildSearchQuery:
    """Tests for the build_search_query function."""

    def test_combines_artists_and_title(self) -> None:
        """Should combine artists and title into query."""
        result = build_search_query("song name", ["artist a", "artist b"])
        assert result == "artist a, artist b song name"

    def test_single_artist(self) -> None:
        """Should handle single artist."""
        result = build_search_query("song name", ["artist"])
        assert result == "artist song name"

    def test_empty_artists(self) -> None:
        """Should handle empty artist list."""
        result = build_search_query("song name", [])
        assert result == "song name"


class TestNormalize:
    """Tests for normalization functions."""

    def test_normalize_label(self) -> None:
        """Should lowercase and strip label."""
        assert normalize_label("  Sample Records  ") == "sample records"

    def test_normalize_genre(self) -> None:
        """Should lowercase and strip genre."""
        assert normalize_genre("  Progressive House  ") == "progressive house"


class TestTruncate:
    """Tests for the truncate function."""

    def test_no_truncation_needed(self) -> None:
        """Should return original if within limit."""
        assert truncate("short", 10) == "short"

    def test_truncates_long_text(self) -> None:
        """Should truncate text exceeding limit."""
        result = truncate("this is a very long text", 10)
        assert len(result) == 10
        assert result.endswith("...")

    def test_custom_suffix(self) -> None:
        """Should use custom suffix."""
        result = truncate("long text here", 10, suffix="…")
        assert result.endswith("…")

    def test_exact_length(self) -> None:
        """Should not truncate at exact length."""
        assert truncate("exact", 5) == "exact"
