"""Unit tests for constants module.

Tests Platform enum, StatCategory enum, WeightLevel enum, and constant values.
"""

# Third-party
import pytest

# Local
from msc.config.constants import (
    CATEGORY_WEIGHTS,
    DEFAULT_HEADERS,
    Platform,
    REJECT_KEYWORDS,
    SONGSTATS_BASE_URL,
    SONGSTATS_ENDPOINTS,
    StatCategory,
    TITLE_PATTERNS_TO_REMOVE,
    TITLE_PATTERNS_TO_SPACE,
    WeightLevel,
)


class TestPlatformEnum:
    """Tests for Platform enum."""

    @staticmethod
    def test_has_all_platforms() -> None:
        """Should have all 10 streaming platforms."""
        assert len(Platform) == 10

    @staticmethod
    def test_platform_values() -> None:
        """Should have correct string values."""
        assert Platform.SPOTIFY.value == "spotify"
        assert Platform.APPLE_MUSIC.value == "appleMusic"
        assert Platform.YOUTUBE.value == "youtube"
        assert Platform.DEEZER.value == "deezer"
        assert Platform.TIKTOK.value == "tiktok"
        assert Platform.BEATPORT.value == "beatport"
        assert Platform.TIDAL.value == "tidal"
        assert Platform.SOUNDCLOUD.value == "soundcloud"
        assert Platform.AMAZON.value == "amazonMusic"
        assert Platform.TRACKLISTS.value == "1001tracklists"

    @staticmethod
    def test_is_string_enum() -> None:
        """Should be a string enum for comparison."""
        assert Platform.SPOTIFY == "spotify"

    @staticmethod
    def test_songstats_sources_returns_tuple() -> None:
        """Should return tuple of Songstats API source names."""
        sources = Platform.songstats_sources()
        assert isinstance(sources, tuple)
        assert "spotify" in sources
        assert "apple_music" in sources

    @staticmethod
    def test_songstats_sources_has_correct_count() -> None:
        """Should return 10 source names."""
        sources = Platform.songstats_sources()
        assert len(sources) == 10


class TestStatCategoryEnum:
    """Tests for StatCategory enum."""

    @staticmethod
    def test_has_all_categories() -> None:
        """Should have all 8 stat categories."""
        assert len(StatCategory) == 8

    @staticmethod
    def test_category_values() -> None:
        """Should have correct string values."""
        assert StatCategory.CHARTS.value == "charts"
        assert StatCategory.ENGAGEMENT.value == "engagement"
        assert StatCategory.PLAYLISTS.value == "playlists"
        assert StatCategory.POPULARITY.value == "popularity"
        assert StatCategory.PROFESSIONAL.value == "professional_support"
        assert StatCategory.REACH.value == "reach"
        assert StatCategory.SHORTS.value == "shorts"
        assert StatCategory.STREAMS.value == "streams"

    @staticmethod
    def test_is_string_enum() -> None:
        """Should be a string enum for comparison."""
        assert StatCategory.CHARTS == "charts"


class TestWeightLevelEnum:
    """Tests for WeightLevel enum."""

    @staticmethod
    def test_has_three_levels() -> None:
        """Should have 3 weight levels."""
        assert len(WeightLevel) == 3

    @staticmethod
    def test_level_values() -> None:
        """Should have correct integer values."""
        assert WeightLevel.NEGLIGIBLE == 1
        assert WeightLevel.LOW == 2
        assert WeightLevel.HIGH == 4

    @staticmethod
    def test_is_int_enum() -> None:
        """Should be an integer enum for math operations."""
        assert WeightLevel.HIGH * 2 == 8


class TestCategoryWeights:
    """Tests for CATEGORY_WEIGHTS constant."""

    @staticmethod
    def test_has_all_categories() -> None:
        """Should have weights for all categories."""
        assert len(CATEGORY_WEIGHTS) == len(StatCategory)
        for category in StatCategory:
            assert category in CATEGORY_WEIGHTS

    @staticmethod
    def test_negligible_categories() -> None:
        """Should have negligible weight for charts, engagement, shorts."""
        assert CATEGORY_WEIGHTS[StatCategory.CHARTS] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.ENGAGEMENT] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.SHORTS] == WeightLevel.NEGLIGIBLE

    @staticmethod
    def test_low_categories() -> None:
        """Should have low weight for reach, playlists, professional."""
        assert CATEGORY_WEIGHTS[StatCategory.REACH] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PLAYLISTS] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PROFESSIONAL] == WeightLevel.LOW

    @staticmethod
    def test_high_categories() -> None:
        """Should have high weight for popularity, streams."""
        assert CATEGORY_WEIGHTS[StatCategory.POPULARITY] == WeightLevel.HIGH
        assert CATEGORY_WEIGHTS[StatCategory.STREAMS] == WeightLevel.HIGH


class TestTitlePatterns:
    """Tests for title formatting patterns."""

    @staticmethod
    def test_patterns_to_remove_is_tuple() -> None:
        """Should be a tuple of strings."""
        assert isinstance(TITLE_PATTERNS_TO_REMOVE, tuple)
        assert all(isinstance(p, str) for p in TITLE_PATTERNS_TO_REMOVE)

    @staticmethod
    def test_patterns_to_remove_contains_mix_patterns() -> None:
        """Should contain common mix patterns."""
        assert "[Extended Mix]" in TITLE_PATTERNS_TO_REMOVE
        assert "[Original Mix]" in TITLE_PATTERNS_TO_REMOVE
        assert "[Remix]" in TITLE_PATTERNS_TO_REMOVE

    @staticmethod
    def test_patterns_to_space_is_tuple() -> None:
        """Should be a tuple of strings."""
        assert isinstance(TITLE_PATTERNS_TO_SPACE, tuple)

    @staticmethod
    def test_patterns_to_space_contains_separators() -> None:
        """Should contain artist separator patterns."""
        assert " × " in TITLE_PATTERNS_TO_SPACE
        assert " & " in TITLE_PATTERNS_TO_SPACE


class TestApiConstants:
    """Tests for API-related constants."""

    @staticmethod
    def test_songstats_base_url() -> None:
        """Should have correct Songstats base URL."""
        assert "songstats.com" in SONGSTATS_BASE_URL
        assert "enterprise" in SONGSTATS_BASE_URL
        assert "v1" in SONGSTATS_BASE_URL

    @staticmethod
    def test_songstats_endpoints() -> None:
        """Should have all required endpoints."""
        required_endpoints = [
            "artist_link",
            "artist_track",
            "historic",
            "info",
            "search",
            "stats",
            "status",
            "track_link",
        ]
        for endpoint in required_endpoints:
            assert endpoint in SONGSTATS_ENDPOINTS
            assert SONGSTATS_BASE_URL in SONGSTATS_ENDPOINTS[endpoint]

    @staticmethod
    def test_default_headers() -> None:
        """Should have correct default headers."""
        assert "Accept" in DEFAULT_HEADERS
        assert DEFAULT_HEADERS["Accept"] == "application/json"


class TestRejectKeywords:
    """Tests for REJECT_KEYWORDS constant."""

    @staticmethod
    def test_is_tuple() -> None:
        """Should be a tuple of strings."""
        assert isinstance(REJECT_KEYWORDS, tuple)
        assert all(isinstance(k, str) for k in REJECT_KEYWORDS)

    @staticmethod
    def test_contains_false_positive_keywords() -> None:
        """Should contain keywords for false positive detection."""
        assert "karaoke" in REJECT_KEYWORDS
        assert "instrumental" in REJECT_KEYWORDS
        assert "acapella" in REJECT_KEYWORDS
        assert "cover version" in REJECT_KEYWORDS

    @staticmethod
    def test_keywords_are_lowercase() -> None:
        """Should have lowercase keywords for matching."""
        for keyword in REJECT_KEYWORDS:
            assert keyword == keyword.lower()
