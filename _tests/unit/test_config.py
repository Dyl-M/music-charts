"""Unit tests for configuration module."""

import pytest
from pathlib import Path

from msc.config.constants import (
    Platform,
    StatCategory,
    WeightLevel,
    CATEGORY_WEIGHTS,
)


class TestPlatform:
    """Tests for the Platform enum."""

    def test_all_platforms_defined(self) -> None:
        """Should have all expected platforms."""
        expected = {
            "SPOTIFY", "APPLE_MUSIC", "YOUTUBE", "DEEZER",
            "TIKTOK", "BEATPORT", "TIDAL", "SOUNDCLOUD",
            "AMAZON", "TRACKLISTS"
        }
        actual = {p.name for p in Platform}
        assert actual == expected

    def test_songstats_sources_returns_tuple(self) -> None:
        """Should return tuple of source strings."""
        sources = Platform.songstats_sources()
        assert isinstance(sources, tuple)
        assert len(sources) == 10

    def test_songstats_sources_lowercase(self) -> None:
        """All sources should be lowercase."""
        for source in Platform.songstats_sources():
            assert source == source.lower()


class TestStatCategory:
    """Tests for the StatCategory enum."""

    def test_all_categories_defined(self) -> None:
        """Should have all expected categories."""
        expected = {
            "CHARTS", "ENGAGEMENT", "PLAYLISTS", "POPULARITY",
            "PROFESSIONAL", "REACH", "SHORTS", "STREAMS"
        }
        actual = {c.name for c in StatCategory}
        assert actual == expected


class TestWeightLevel:
    """Tests for the WeightLevel enum."""

    def test_weight_values(self) -> None:
        """Weight levels should have correct values."""
        assert WeightLevel.NEGLIGIBLE == 1
        assert WeightLevel.LOW == 2
        assert WeightLevel.HIGH == 4


class TestCategoryWeights:
    """Tests for category weight assignments."""

    def test_all_categories_have_weights(self) -> None:
        """Every category should have a weight assigned."""
        for category in StatCategory:
            assert category in CATEGORY_WEIGHTS

    def test_negligible_weights(self) -> None:
        """Charts, Engagement, and Shorts should be negligible."""
        assert CATEGORY_WEIGHTS[StatCategory.CHARTS] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.ENGAGEMENT] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.SHORTS] == WeightLevel.NEGLIGIBLE

    def test_low_weights(self) -> None:
        """Reach, Playlists, and Professional should be low."""
        assert CATEGORY_WEIGHTS[StatCategory.REACH] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PLAYLISTS] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PROFESSIONAL] == WeightLevel.LOW

    def test_high_weights(self) -> None:
        """Popularity and Streams should be high."""
        assert CATEGORY_WEIGHTS[StatCategory.POPULARITY] == WeightLevel.HIGH
        assert CATEGORY_WEIGHTS[StatCategory.STREAMS] == WeightLevel.HIGH
