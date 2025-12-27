"""Unit tests for PowerRankingScorer.

Tests the scoring algorithm and category computation.
"""

# Standard library
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Local
from msc.analysis.scorer import PowerRankingScorer, PLATFORM_NAME_MAP
from msc.analysis.normalizers import MinMaxNormalizer, ZScoreNormalizer
from msc.models.stats import TrackWithStats
from msc.models.ranking import PowerRankingResults


class TestPowerRankingScorerInit:
    """Tests for PowerRankingScorer initialization."""

    @staticmethod
    def test_uses_default_normalizer(temp_category_config: Path) -> None:
        """Should use MinMaxNormalizer by default."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        assert isinstance(scorer.normalizer, MinMaxNormalizer)

    @staticmethod
    def test_uses_custom_normalizer(temp_category_config: Path) -> None:
        """Should accept custom normalizer."""
        normalizer = ZScoreNormalizer()
        scorer = PowerRankingScorer(
            category_config_path=temp_category_config,
            normalizer=normalizer,
        )
        assert isinstance(scorer.normalizer, ZScoreNormalizer)

    @staticmethod
    def test_loads_category_config(temp_category_config: Path) -> None:
        """Should load category configuration from file."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        assert "popularity" in scorer.category_config
        assert "streams" in scorer.category_config

    @staticmethod
    def test_handles_missing_config() -> None:
        """Should return empty config for missing file."""
        with patch("msc.analysis.scorer.get_settings") as mock_settings:
            mock_settings.return_value.config_dir = Path("/nonexistent")
            mock_settings.return_value.year = 2024

            scorer = PowerRankingScorer(
                category_config_path=Path("/nonexistent/categories.json")
            )
            assert scorer.category_config == {}


class TestPowerRankingScorerPlatformNameMap:
    """Tests for PLATFORM_NAME_MAP constant."""

    @staticmethod
    def test_maps_1001tracklists() -> None:
        """Should map 1001tracklists to tracklists."""
        assert PLATFORM_NAME_MAP["1001tracklists"] == "tracklists"

    @staticmethod
    def test_maps_amazon() -> None:
        """Should map amazon to amazon_music."""
        assert PLATFORM_NAME_MAP["amazon"] == "amazon_music"


class TestPowerRankingScorerGetMetricValue:
    """Tests for PowerRankingScorer._get_metric_value method."""

    @staticmethod
    def test_extracts_metric(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should extract metric value from track."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        track = sample_tracks_with_stats[0]

        value = scorer._get_metric_value(track, "spotify_streams_total")
        assert value == 1000000

    @staticmethod
    def test_returns_none_for_invalid_format(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should return None for invalid metric name format."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        track = sample_tracks_with_stats[0]

        value = scorer._get_metric_value(track, "invalid")
        assert value is None

    @staticmethod
    def test_returns_none_for_missing_platform(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should return None for missing platform."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        track = sample_tracks_with_stats[0]

        value = scorer._get_metric_value(track, "nonexistent_metric")
        assert value is None

    @staticmethod
    def test_returns_none_for_missing_metric(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should return None for missing metric on platform."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        track = sample_tracks_with_stats[0]

        # Spotify exists but this metric doesn't
        value = scorer._get_metric_value(track, "spotify_nonexistent_metric")
        assert value is None


class TestPowerRankingScorerCollectMetricValues:
    """Tests for PowerRankingScorer._collect_metric_values method."""

    @staticmethod
    def test_collects_values(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should collect metric values for all tracks."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        metrics = ["spotify_streams_total"]

        values = scorer._collect_metric_values(sample_tracks_with_stats, metrics)

        assert "spotify_streams_total" in values
        assert len(values["spotify_streams_total"]) == 3

    @staticmethod
    def test_uses_zero_for_missing(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should use 0.0 for missing metric values."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)
        metrics = ["nonexistent_metric"]

        values = scorer._collect_metric_values(sample_tracks_with_stats, metrics)

        assert all(v == 0.0 for v in values["nonexistent_metric"])


class TestPowerRankingScorerAvailabilityWeights:
    """Tests for PowerRankingScorer._compute_availability_weights method."""

    @staticmethod
    def test_computes_availability() -> None:
        """Should compute proportion of non-zero values."""
        metric_values = {
            "metric_a": [100.0, 0.0, 50.0, 0.0],  # 2/4 = 0.5
            "metric_b": [10.0, 20.0, 30.0, 40.0],  # 4/4 = 1.0
        }

        weights = PowerRankingScorer._compute_availability_weights(metric_values)

        assert weights["metric_a"] == 0.5
        assert weights["metric_b"] == 1.0

    @staticmethod
    def test_empty_values() -> None:
        """Should return 0.0 for empty values list."""
        metric_values = {"empty": []}

        weights = PowerRankingScorer._compute_availability_weights(metric_values)

        assert weights["empty"] == 0.0

    @staticmethod
    def test_all_zeros() -> None:
        """Should return 0.0 when all values are zero."""
        metric_values = {"zeros": [0.0, 0.0, 0.0]}

        weights = PowerRankingScorer._compute_availability_weights(metric_values)

        assert weights["zeros"] == 0.0


class TestPowerRankingScorerComputeRankings:
    """Tests for PowerRankingScorer.compute_rankings method."""

    @staticmethod
    def test_returns_power_ranking_results(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should return PowerRankingResults."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        assert isinstance(results, PowerRankingResults)

    @staticmethod
    def test_ranks_all_tracks(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should rank all input tracks."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        assert len(results.rankings) == 3

    @staticmethod
    def test_assigns_consecutive_ranks(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should assign consecutive ranks starting at 1."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        ranks = [r.rank for r in results.rankings]
        assert ranks == [1, 2, 3]

    @staticmethod
    def test_sorts_by_score_descending(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should sort by total score in descending order."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        scores = [r.total_score for r in results.rankings]
        assert scores == sorted(scores, reverse=True)

    @staticmethod
    def test_empty_tracks_list(temp_category_config: Path) -> None:
        """Should return empty results for empty input."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings([])

        assert results.rankings == []

    @staticmethod
    def test_includes_category_scores(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should include category scores in rankings."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        for ranking in results.rankings:
            assert len(ranking.category_scores) > 0

    @staticmethod
    def test_scores_in_valid_range(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should produce scores in 0-100 range."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        results = scorer.compute_rankings(sample_tracks_with_stats)

        for ranking in results.rankings:
            assert 0.0 <= ranking.total_score <= 100.0


class TestPowerRankingScorerEmptyConfig:
    """Tests for PowerRankingScorer with empty category config."""

    @staticmethod
    def test_handles_empty_config(
            tmp_path: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should raise validation error for empty category configuration.

        PowerRanking model requires at least one category score.
        """
        from pydantic import ValidationError

        config_path = tmp_path / "empty.json"
        config_path.write_text("{}", encoding="utf-8")

        scorer = PowerRankingScorer(category_config_path=config_path)

        # Empty config produces empty category_scores which violates model constraint
        with pytest.raises(ValidationError, match="category_scores"):
            scorer.compute_rankings(sample_tracks_with_stats)

    @staticmethod
    def test_handles_missing_category_weight(
            tmp_path: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should handle unknown category names."""
        config_path = tmp_path / "unknown.json"
        config_path.write_text(
            '{"unknown_category": ["spotify_streams_total"]}',
            encoding="utf-8",
        )

        scorer = PowerRankingScorer(category_config_path=config_path)
        results = scorer.compute_rankings(sample_tracks_with_stats)

        # Should use default importance of 1
        assert len(results.rankings) == 3


class TestPowerRankingScorerCategoryScores:
    """Tests for category score computation."""

    @staticmethod
    def test_empty_metrics_returns_zeros(temp_category_config: Path) -> None:
        """Should return zeros for empty metrics list."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        with patch.object(scorer, "_collect_metric_values") as mock_collect:
            mock_collect.return_value = {}
            scores, weight = scorer._compute_category_scores([], "test", [])

            assert scores == []
            assert weight == 0.0

    @staticmethod
    def test_category_weight_based_on_availability(
            temp_category_config: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should compute category weight from average availability."""
        scorer = PowerRankingScorer(category_config_path=temp_category_config)

        _scores, weight = scorer._compute_category_scores(
            sample_tracks_with_stats,
            "test",
            ["spotify_streams_total"],  # All tracks have this
        )

        # All tracks have streams, so availability should be 1.0
        assert weight == 1.0
