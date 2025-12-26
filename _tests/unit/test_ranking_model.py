"""Tests for power ranking models."""

# Standard library
import json

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.track import Track


class TestCategoryScore:
    """Tests for CategoryScore model."""

    @staticmethod
    def test_create_valid_score() -> None:
        """Test creating valid CategoryScore instance."""
        score = CategoryScore(
            category="streams",
            raw_score=0.85,
            weight=4,
            weighted_score=3.4
        )
        assert score.category == "streams"
        assert score.raw_score == 0.85
        assert score.weight == 4
        assert score.weighted_score == 3.4

    @staticmethod
    def test_raw_score_validation_min() -> None:
        """Test raw_score must be >= 0.0."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=-0.1,
                weight=4,
                weighted_score=0.0
            )

    @staticmethod
    def test_raw_score_validation_max() -> None:
        """Test raw_score must be <= 100.0."""
        with pytest.raises(ValidationError):
            CategoryScore(
                category="streams",
                raw_score=100.1,
                weight=4.0,
                weighted_score=400.4
            )

    @staticmethod
    def test_weight_validation() -> None:
        """Test weight must be >= 0.0 (availability × importance)."""
        # Valid weights (now floats representing availability × importance)
        CategoryScore(category="test", raw_score=50.0, weight=0.0, weighted_score=0.0)
        CategoryScore(category="test", raw_score=50.0, weight=0.5, weighted_score=25.0)
        CategoryScore(category="test", raw_score=50.0, weight=2.0, weighted_score=100.0)
        CategoryScore(category="test", raw_score=50.0, weight=4.0, weighted_score=200.0)

        # Invalid: negative weight
        with pytest.raises(ValidationError):
            CategoryScore(category="test", raw_score=50.0, weight=-0.5, weighted_score=-25.0)

    @staticmethod
    def test_frozen_model() -> None:
        """Test CategoryScore is immutable."""
        score = CategoryScore(
            category="streams",
            raw_score=0.85,
            weight=4,
            weighted_score=3.4
        )
        with pytest.raises(ValidationError):
            score.weighted_score = 5.0

    @staticmethod
    def test_json_serialization() -> None:
        """Test CategoryScore can be serialized to JSON."""
        score = CategoryScore(
            category="streams",
            raw_score=0.85,
            weight=4,
            weighted_score=3.4
        )
        json_str = score.model_dump_json()
        data = json.loads(json_str)
        assert data["category"] == "streams"
        assert data["raw_score"] == 0.85


class TestPowerRanking:
    """Tests for PowerRanking model."""

    @staticmethod
    def test_create_valid_ranking() -> None:
        """Test creating valid PowerRanking instance."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024
        )
        category_scores = [
            CategoryScore(
                category="streams",
                raw_score=0.85,
                weight=4,
                weighted_score=3.4
            )
        ]
        ranking = PowerRanking(
            track=track,
            total_score=15.7,
            rank=1,
            category_scores=category_scores
        )

        assert ranking.track.title == "16"
        assert ranking.total_score == 15.7
        assert ranking.rank == 1
        assert len(ranking.category_scores) == 1

    @staticmethod
    def test_total_score_validation() -> None:
        """Test total_score must be >= 0.0."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        with pytest.raises(ValidationError):
            PowerRanking(
                track=track,
                total_score=-1.0,
                rank=1,
                category_scores=category_scores
            )

    @staticmethod
    def test_rank_validation() -> None:
        """Test rank must be >= 1."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        with pytest.raises(ValidationError):
            PowerRanking(
                track=track,
                total_score=5.0,
                rank=0,
                category_scores=category_scores
            )

    @staticmethod
    def test_category_scores_min_length() -> None:
        """Test category_scores must have at least one score."""
        track = Track(title="Test", artist_list=["artist"], year=2024)

        with pytest.raises(ValidationError):
            PowerRanking(
                track=track,
                total_score=5.0,
                rank=1,
                category_scores=[]
            )

    @staticmethod
    def test_artist_display_single() -> None:
        """Test artist_display with single artist."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        ranking = PowerRanking(
            track=track,
            total_score=5.0,
            rank=1,
            category_scores=category_scores
        )

        assert ranking.artist_display == "artist"

    @staticmethod
    def test_artist_display_multiple() -> None:
        """Test artist_display with multiple artists."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024
        )
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        ranking = PowerRanking(
            track=track,
            total_score=5.0,
            rank=1,
            category_scores=category_scores
        )

        assert ranking.artist_display == "blasterjaxx & hardwell & maddix"

    @staticmethod
    def test_frozen_model() -> None:
        """Test PowerRanking is immutable."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        ranking = PowerRanking(
            track=track,
            total_score=5.0,
            rank=1,
            category_scores=category_scores
        )

        with pytest.raises(ValidationError):
            ranking.rank = 2

    @staticmethod
    def test_json_serialization() -> None:
        """Test PowerRanking can be serialized to JSON."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        ranking = PowerRanking(
            track=track,
            total_score=5.0,
            rank=1,
            category_scores=category_scores
        )

        json_str = ranking.model_dump_json()
        data = json.loads(json_str)

        assert data["track"]["title"] == "Test"
        assert data["total_score"] == 5.0
        assert data["rank"] == 1


class TestPowerRankingResults:
    """Tests for PowerRankingResults model."""

    @staticmethod
    def test_create_valid_results() -> None:
        """Test creating valid PowerRankingResults instance."""
        track1 = Track(title="Track1", artist_list=["artist1"], year=2024)
        track2 = Track(title="Track2", artist_list=["artist2"], year=2024)

        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        rankings = [
            PowerRanking(track=track1, total_score=15.7, rank=1, category_scores=category_scores),
            PowerRanking(track=track2, total_score=12.3, rank=2, category_scores=category_scores),
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)

        assert len(results.rankings) == 2
        assert results.year == 2024

    @staticmethod
    def test_rankings_empty_list_allowed() -> None:
        """Test that empty rankings list is allowed (e.g., when no tracks to rank)."""
        results = PowerRankingResults(rankings=[], year=2024)
        assert results.rankings == []
        assert results.total_tracks == 0

    @staticmethod
    def test_total_tracks_property() -> None:
        """Test total_tracks property returns correct count."""
        track1 = Track(title="Track1", artist_list=["artist1"], year=2024)
        track2 = Track(title="Track2", artist_list=["artist2"], year=2024)

        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        rankings = [
            PowerRanking(track=track1, total_score=15.7, rank=1, category_scores=category_scores),
            PowerRanking(track=track2, total_score=12.3, rank=2, category_scores=category_scores),
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)
        assert results.total_tracks == 2

    @staticmethod
    def test_get_by_rank_found() -> None:
        """Test get_by_rank returns correct ranking."""
        track1 = Track(title="Track1", artist_list=["artist1"], year=2024)
        track2 = Track(title="Track2", artist_list=["artist2"], year=2024)

        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        rankings = [
            PowerRanking(track=track1, total_score=15.7, rank=1, category_scores=category_scores),
            PowerRanking(track=track2, total_score=12.3, rank=2, category_scores=category_scores),
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)

        top_track = results.get_by_rank(1)
        assert top_track is not None
        assert top_track.track.title == "Track1"

    @staticmethod
    def test_get_by_rank_not_found() -> None:
        """Test get_by_rank returns None when rank not found."""
        track = Track(title="Track1", artist_list=["artist1"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        rankings = [
            PowerRanking(track=track, total_score=15.7, rank=1, category_scores=category_scores)
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)
        not_found = results.get_by_rank(99)
        assert not_found is None

    @staticmethod
    def test_get_by_artist_found() -> None:
        """Test get_by_artist returns matching rankings."""
        track1 = Track(title="Track1", artist_list=["hardwell"], year=2024)
        track2 = Track(title="Track2", artist_list=["hardwell", "maddix"], year=2024)
        track3 = Track(title="Track3", artist_list=["blasterjaxx"], year=2024)

        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]

        rankings = [
            PowerRanking(track=track1, total_score=15.7, rank=1, category_scores=category_scores),
            PowerRanking(track=track2, total_score=12.3, rank=2, category_scores=category_scores),
            PowerRanking(track=track3, total_score=10.0, rank=3, category_scores=category_scores),
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)
        hardwell_tracks = results.get_by_artist("hardwell")

        assert len(hardwell_tracks) == 2
        assert hardwell_tracks[0].track.title == "Track1"
        assert hardwell_tracks[1].track.title == "Track2"

    @staticmethod
    def test_get_by_artist_case_insensitive() -> None:
        """Test get_by_artist is case-insensitive."""
        track = Track(title="Track1", artist_list=["Hardwell"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        rankings = [
            PowerRanking(track=track, total_score=15.7, rank=1, category_scores=category_scores)
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)

        # All these should match
        assert len(results.get_by_artist("hardwell")) == 1
        assert len(results.get_by_artist("HARDWELL")) == 1
        assert len(results.get_by_artist("Hardwell")) == 1

    @staticmethod
    def test_frozen_model() -> None:
        """Test PowerRankingResults is immutable."""
        track = Track(title="Track1", artist_list=["artist1"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        rankings = [
            PowerRanking(track=track, total_score=15.7, rank=1, category_scores=category_scores)
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)

        with pytest.raises(ValidationError):
            results.year = 2025

    @staticmethod
    def test_json_serialization() -> None:
        """Test PowerRankingResults can be serialized to JSON."""
        track = Track(title="Track1", artist_list=["artist1"], year=2024)
        category_scores = [
            CategoryScore(category="test", raw_score=0.5, weight=1, weighted_score=0.5)
        ]
        rankings = [
            PowerRanking(track=track, total_score=15.7, rank=1, category_scores=category_scores)
        ]

        results = PowerRankingResults(rankings=rankings, year=2024)
        json_str = results.model_dump_json()
        data = json.loads(json_str)

        assert data["year"] == 2024
        assert len(data["rankings"]) == 1
