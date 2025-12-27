"""Unit tests for power ranking models.

Tests CategoryScore, PowerRanking, and PowerRankingResults models.
"""

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.track import Track


class TestCategoryScoreCreation:
    """Tests for CategoryScore model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with all required fields."""
        score = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        assert score.category == "streams"
        assert score.raw_score == 85.0
        assert score.weight == 2.4
        assert score.weighted_score == 204.0

    @staticmethod
    def test_accepts_zero_values() -> None:
        """Should accept zero values for numeric fields."""
        score = CategoryScore(
            category="streams",
            raw_score=0.0,
            weight=0.0,
            weighted_score=0.0,
        )
        assert score.raw_score == 0.0
        assert score.weight == 0.0
        assert score.weighted_score == 0.0


class TestCategoryScoreValidation:
    """Tests for CategoryScore field validation."""

    @staticmethod
    def test_validates_raw_score_minimum() -> None:
        """Should reject raw_score below 0."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=-1.0,
                weight=1.0,
                weighted_score=0.0,
            )

    @staticmethod
    def test_validates_raw_score_maximum() -> None:
        """Should reject raw_score above 100."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=101.0,
                weight=1.0,
                weighted_score=0.0,
            )

    @staticmethod
    def test_accepts_boundary_raw_scores() -> None:
        """Should accept raw_score at boundaries (0 and 100)."""
        score_min = CategoryScore(
            category="streams",
            raw_score=0.0,
            weight=1.0,
            weighted_score=0.0,
        )
        score_max = CategoryScore(
            category="streams",
            raw_score=100.0,
            weight=1.0,
            weighted_score=100.0,
        )
        assert score_min.raw_score == 0.0
        assert score_max.raw_score == 100.0

    @staticmethod
    def test_validates_weight_minimum() -> None:
        """Should reject weight below 0."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=50.0,
                weight=-1.0,
                weighted_score=0.0,
            )

    @staticmethod
    def test_validates_weighted_score_minimum() -> None:
        """Should reject weighted_score below 0."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=50.0,
                weight=1.0,
                weighted_score=-1.0,
            )


class TestCategoryScoreImmutability:
    """Tests for CategoryScore immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        score = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        with pytest.raises(ValidationError):
            score.raw_score = 90.0  # type: ignore[misc]


class TestCategoryScoreEquality:
    """Tests for CategoryScore equality comparison."""

    @staticmethod
    def test_equal_instances() -> None:
        """Should be equal when all fields match."""
        score1 = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        score2 = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        assert score1 == score2


class TestPowerRankingCreation:
    """Tests for PowerRanking model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with required fields."""
        track = Track(title="16", artist_list=["hardwell"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=15.7,
            rank=1,
            category_scores=[score],
        )
        assert ranking.track.title == "16"
        assert ranking.total_score == 15.7
        assert ranking.rank == 1
        assert len(ranking.category_scores) == 1

    @staticmethod
    def test_creates_with_multiple_category_scores() -> None:
        """Should create with multiple category scores."""
        track = Track(title="16", artist_list=["hardwell"], year=2024)
        scores = [
            CategoryScore(
                category="streams",
                raw_score=85.0,
                weight=2.4,
                weighted_score=204.0,
            ),
            CategoryScore(
                category="popularity",
                raw_score=75.0,
                weight=3.2,
                weighted_score=240.0,
            ),
        ]
        ranking = PowerRanking(
            track=track,
            total_score=30.0,
            rank=1,
            category_scores=scores,
        )
        assert len(ranking.category_scores) == 2


class TestPowerRankingValidation:
    """Tests for PowerRanking field validation."""

    @staticmethod
    def test_validates_total_score_minimum() -> None:
        """Should reject total_score below 0."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=0.0,
            weight=0.0,
            weighted_score=0.0,
        )
        with pytest.raises(ValidationError):
            PowerRanking(
                track=track,
                total_score=-1.0,
                rank=1,
                category_scores=[score],
            )

    @staticmethod
    def test_validates_rank_minimum() -> None:
        """Should reject rank below 1."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        with pytest.raises(ValidationError):
            PowerRanking(
                track=track,
                total_score=50.0,
                rank=0,  # Rank must be >= 1
                category_scores=[score],
            )

    @staticmethod
    def test_requires_at_least_one_category_score() -> None:
        """Should require at least one category score."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        with pytest.raises(ValidationError, match="category_scores"):
            PowerRanking(
                track=track,
                total_score=50.0,
                rank=1,
                category_scores=[],  # Empty list should fail
            )


class TestPowerRankingImmutability:
    """Tests for PowerRanking immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        track = Track(title="16", artist_list=["hardwell"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=85.0,
            weight=2.4,
            weighted_score=204.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=15.7,
            rank=1,
            category_scores=[score],
        )
        with pytest.raises(ValidationError):
            ranking.rank = 2  # type: ignore[misc]


class TestPowerRankingArtistDisplay:
    """Tests for PowerRanking.artist_display property."""

    @staticmethod
    def test_single_artist() -> None:
        """Should return single artist name."""
        track = Track(title="test", artist_list=["hardwell"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=50.0,
            rank=1,
            category_scores=[score],
        )
        assert ranking.artist_display == "hardwell"

    @staticmethod
    def test_multiple_artists() -> None:
        """Should return artists joined with &."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024,
        )
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=50.0,
            rank=1,
            category_scores=[score],
        )
        assert ranking.artist_display == "blasterjaxx & hardwell & maddix"

    @staticmethod
    def test_two_artists() -> None:
        """Should handle exactly two artists."""
        track = Track(
            title="test",
            artist_list=["artist a", "artist b"],
            year=2024,
        )
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=50.0,
            rank=1,
            category_scores=[score],
        )
        assert ranking.artist_display == "artist a & artist b"


class TestPowerRankingResultsCreation:
    """Tests for PowerRankingResults model creation."""

    @staticmethod
    def test_creates_with_rankings() -> None:
        """Should create with list of rankings."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=50.0,
            rank=1,
            category_scores=[score],
        )
        results = PowerRankingResults(
            rankings=[ranking],
            year=2024,
        )
        assert len(results.rankings) == 1
        assert results.year == 2024

    @staticmethod
    def test_creates_with_empty_rankings() -> None:
        """Should create with empty rankings list."""
        results = PowerRankingResults(
            rankings=[],
            year=2024,
        )
        assert results.rankings == []


class TestPowerRankingResultsValidation:
    """Tests for PowerRankingResults field validation."""

    @staticmethod
    def test_validates_year_minimum() -> None:
        """Should reject year below 1900."""
        with pytest.raises(ValidationError):
            PowerRankingResults(rankings=[], year=1899)

    @staticmethod
    def test_validates_year_maximum() -> None:
        """Should reject year above 2100."""
        with pytest.raises(ValidationError):
            PowerRankingResults(rankings=[], year=2101)

    @staticmethod
    def test_accepts_boundary_years() -> None:
        """Should accept years at boundaries."""
        results_min = PowerRankingResults(rankings=[], year=1900)
        results_max = PowerRankingResults(rankings=[], year=2100)
        assert results_min.year == 1900
        assert results_max.year == 2100


class TestPowerRankingResultsImmutability:
    """Tests for PowerRankingResults immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        results = PowerRankingResults(rankings=[], year=2024)
        with pytest.raises(ValidationError):
            results.year = 2025  # type: ignore[misc]


class TestPowerRankingResultsTotalTracks:
    """Tests for PowerRankingResults.total_tracks property."""

    @staticmethod
    def test_returns_zero_for_empty() -> None:
        """Should return 0 for empty rankings."""
        results = PowerRankingResults(rankings=[], year=2024)
        assert results.total_tracks == 0

    @staticmethod
    def test_returns_count_for_rankings() -> None:
        """Should return correct count."""
        track1 = Track(title="test1", artist_list=["artist"], year=2024)
        track2 = Track(title="test2", artist_list=["artist"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        rankings = [
            PowerRanking(
                track=track1,
                total_score=60.0,
                rank=1,
                category_scores=[score],
            ),
            PowerRanking(
                track=track2,
                total_score=50.0,
                rank=2,
                category_scores=[score],
            ),
        ]
        results = PowerRankingResults(rankings=rankings, year=2024)
        assert results.total_tracks == 2


class TestPowerRankingResultsGetByRank:
    """Tests for PowerRankingResults.get_by_rank method."""

    @staticmethod
    def test_returns_ranking_at_position() -> None:
        """Should return ranking at given position."""
        track1 = Track(title="top track", artist_list=["artist"], year=2024)
        track2 = Track(title="second track", artist_list=["artist"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        rankings = [
            PowerRanking(
                track=track1,
                total_score=60.0,
                rank=1,
                category_scores=[score],
            ),
            PowerRanking(
                track=track2,
                total_score=50.0,
                rank=2,
                category_scores=[score],
            ),
        ]
        results = PowerRankingResults(rankings=rankings, year=2024)
        top = results.get_by_rank(1)
        assert top is not None
        assert top.track.title == "top track"

    @staticmethod
    def test_returns_none_for_invalid_rank() -> None:
        """Should return None for non-existent rank."""
        results = PowerRankingResults(rankings=[], year=2024)
        assert results.get_by_rank(1) is None
        assert results.get_by_rank(100) is None


class TestPowerRankingResultsGetByArtist:
    """Tests for PowerRankingResults.get_by_artist method."""

    @staticmethod
    def test_returns_matching_rankings() -> None:
        """Should return all rankings with matching artist."""
        track1 = Track(title="track1", artist_list=["hardwell"], year=2024)
        track2 = Track(title="track2", artist_list=["hardwell", "tiesto"], year=2024)
        track3 = Track(title="track3", artist_list=["tiesto"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        rankings = [
            PowerRanking(
                track=track1,
                total_score=60.0,
                rank=1,
                category_scores=[score],
            ),
            PowerRanking(
                track=track2,
                total_score=50.0,
                rank=2,
                category_scores=[score],
            ),
            PowerRanking(
                track=track3,
                total_score=40.0,
                rank=3,
                category_scores=[score],
            ),
        ]
        results = PowerRankingResults(rankings=rankings, year=2024)
        hardwell_tracks = results.get_by_artist("hardwell")
        assert len(hardwell_tracks) == 2
        assert all("hardwell" in r.track.artist_list for r in hardwell_tracks)

    @staticmethod
    def test_is_case_insensitive() -> None:
        """Should match artist case-insensitively."""
        track = Track(title="track", artist_list=["Hardwell"], year=2024)
        score = CategoryScore(
            category="streams",
            raw_score=50.0,
            weight=1.0,
            weighted_score=50.0,
        )
        ranking = PowerRanking(
            track=track,
            total_score=50.0,
            rank=1,
            category_scores=[score],
        )
        results = PowerRankingResults(rankings=[ranking], year=2024)
        assert len(results.get_by_artist("hardwell")) == 1
        assert len(results.get_by_artist("HARDWELL")) == 1

    @staticmethod
    def test_returns_empty_for_no_match() -> None:
        """Should return empty list when no matches."""
        results = PowerRankingResults(rankings=[], year=2024)
        assert results.get_by_artist("nonexistent") == []
