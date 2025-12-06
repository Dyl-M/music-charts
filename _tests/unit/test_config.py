"""Unit tests for configuration module."""

from msc.config.constants import (
    CATEGORY_WEIGHTS,
    Platform,
    StatCategory,
    WeightLevel,
)


class TestPlatform:
    """Tests for the Platform enum."""

    @staticmethod
    def test_all_platforms_defined() -> None:
        """Should have all expected platforms."""
        expected = {
            "SPOTIFY", "APPLE_MUSIC", "YOUTUBE", "DEEZER",
            "TIKTOK", "BEATPORT", "TIDAL", "SOUNDCLOUD",
            "AMAZON", "TRACKLISTS"
        }
        actual = {p.name for p in Platform}
        assert actual == expected

    @staticmethod
    def test_songstats_sources_returns_tuple() -> None:
        """Should return tuple of source strings."""
        sources = Platform.songstats_sources()
        assert isinstance(sources, tuple)
        assert len(sources) == 10

    @staticmethod
    def test_songstats_sources_lowercase() -> None:
        """All sources should be lowercase."""
        for source in Platform.songstats_sources():
            assert source == source.lower()


class TestStatCategory:
    """Tests for the StatCategory enum."""

    @staticmethod
    def test_all_categories_defined() -> None:
        """Should have all expected categories."""
        expected = {
            "CHARTS", "ENGAGEMENT", "PLAYLISTS", "POPULARITY",
            "PROFESSIONAL", "REACH", "SHORTS", "STREAMS"
        }
        actual = {c.name for c in StatCategory}
        assert actual == expected


class TestWeightLevel:
    """Tests for the WeightLevel enum."""

    @staticmethod
    def test_weight_values() -> None:
        """Weight levels should have correct values."""
        assert WeightLevel.NEGLIGIBLE == 1
        assert WeightLevel.LOW == 2
        assert WeightLevel.HIGH == 4


class TestCategoryWeights:
    """Tests for category weight assignments."""

    @staticmethod
    def test_all_categories_have_weights() -> None:
        """Every category should have a weight assigned."""
        for category in StatCategory:
            assert category in CATEGORY_WEIGHTS

    @staticmethod
    def test_negligible_weights() -> None:
        """Charts, Engagement, and Shorts should be negligible."""
        assert CATEGORY_WEIGHTS[StatCategory.CHARTS] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.ENGAGEMENT] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.SHORTS] == WeightLevel.NEGLIGIBLE

    @staticmethod
    def test_low_weights() -> None:
        """Reach, Playlists, and Professional should be low."""
        assert CATEGORY_WEIGHTS[StatCategory.REACH] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PLAYLISTS] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PROFESSIONAL] == WeightLevel.LOW

    @staticmethod
    def test_high_weights() -> None:
        """Popularity and Streams should be high."""
        assert CATEGORY_WEIGHTS[StatCategory.POPULARITY] == WeightLevel.HIGH
        assert CATEGORY_WEIGHTS[StatCategory.STREAMS] == WeightLevel.HIGH
