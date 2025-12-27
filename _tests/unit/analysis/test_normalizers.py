"""Unit tests for normalizer implementations.

Tests MinMaxNormalizer, ZScoreNormalizer, and RobustNormalizer.
"""

# Local
from msc.analysis.normalizers import (
    MinMaxNormalizer,
    ZScoreNormalizer,
    RobustNormalizer,
)


class TestMinMaxNormalizerInit:
    """Tests for MinMaxNormalizer initialization."""

    @staticmethod
    def test_default_range() -> None:
        """Should default to 0-100 range."""
        normalizer = MinMaxNormalizer()
        assert normalizer.feature_range == (0.0, 100.0)

    @staticmethod
    def test_custom_range() -> None:
        """Should accept custom feature range."""
        normalizer = MinMaxNormalizer(feature_range=(0.0, 1.0))
        assert normalizer.feature_range == (0.0, 1.0)

    @staticmethod
    def test_get_name() -> None:
        """Should return 'MinMax' as name."""
        assert MinMaxNormalizer.get_name() == "MinMax"


class TestMinMaxNormalizerNormalize:
    """Tests for MinMaxNormalizer.normalize method."""

    @staticmethod
    def test_empty_list() -> None:
        """Should return empty list for empty input."""
        normalizer = MinMaxNormalizer()
        assert normalizer.normalize([]) == []

    @staticmethod
    def test_single_value() -> None:
        """Should return midpoint for single value."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize([100.0])
        assert result == [50.0]

    @staticmethod
    def test_all_same_values() -> None:
        """Should return midpoint for all same values."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize([50.0, 50.0, 50.0])
        assert all(v == 50.0 for v in result)

    @staticmethod
    def test_normal_values(sample_values: list[float]) -> None:
        """Should normalize to 0-100 range."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize(sample_values)

        assert result[0] == 0.0  # min
        assert result[-1] == 100.0  # max
        assert len(result) == len(sample_values)

    @staticmethod
    def test_custom_range() -> None:
        """Should normalize to custom range."""
        normalizer = MinMaxNormalizer(feature_range=(0.0, 1.0))
        result = normalizer.normalize([0.0, 50.0, 100.0])

        assert result[0] == 0.0
        assert result[1] == 0.5
        assert result[2] == 1.0

    @staticmethod
    def test_handles_nan() -> None:
        """Should handle NaN values."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize([10.0, float("nan"), 30.0])

        assert len(result) == 3
        assert result[1] == 0.0  # NaN becomes range_min

    @staticmethod
    def test_handles_inf() -> None:
        """Should handle infinite values."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize([10.0, float("inf"), 30.0])

        assert len(result) == 3
        assert result[1] == 0.0  # inf becomes range_min

    @staticmethod
    def test_all_nan_values() -> None:
        """Should return zeros for all NaN values."""
        normalizer = MinMaxNormalizer()
        result = normalizer.normalize([float("nan"), float("nan")])

        assert result == [0.0, 0.0]

    @staticmethod
    def test_preserves_order() -> None:
        """Should preserve relative order of values."""
        normalizer = MinMaxNormalizer()
        values = [30.0, 10.0, 50.0, 20.0, 40.0]
        result = normalizer.normalize(values)

        # Original order should be preserved
        assert result[1] == 0.0  # 10 is min
        assert result[2] == 100.0  # 50 is max


class TestZScoreNormalizerInit:
    """Tests for ZScoreNormalizer initialization."""

    @staticmethod
    def test_get_name() -> None:
        """Should return 'ZScore' as name."""
        assert ZScoreNormalizer.get_name() == "ZScore"


class TestZScoreNormalizerNormalize:
    """Tests for ZScoreNormalizer.normalize method."""

    @staticmethod
    def test_empty_list() -> None:
        """Should return empty list for empty input."""
        normalizer = ZScoreNormalizer()
        assert normalizer.normalize([]) == []

    @staticmethod
    def test_single_value() -> None:
        """Should return 0.5 for single value."""
        normalizer = ZScoreNormalizer()
        result = normalizer.normalize([100.0])
        assert result == [0.5]

    @staticmethod
    def test_all_same_values() -> None:
        """Should return 0.5 for all same values (zero std)."""
        normalizer = ZScoreNormalizer()
        result = normalizer.normalize([50.0, 50.0, 50.0])
        assert all(v == 0.5 for v in result)

    @staticmethod
    def test_normal_values() -> None:
        """Should normalize using z-scores."""
        normalizer = ZScoreNormalizer()
        result = normalizer.normalize([10.0, 20.0, 30.0])

        assert len(result) == 3
        # Mean is 20, so 20 should map to 0.5
        assert 0.4 < result[1] < 0.6  # middle value near 0.5

    @staticmethod
    def test_clipping() -> None:
        """Should clip extreme z-scores to [0, 1]."""
        normalizer = ZScoreNormalizer()
        # Create values with extreme outlier
        result = normalizer.normalize([0.0, 0.0, 0.0, 0.0, 1000.0])

        assert all(0.0 <= v <= 1.0 for v in result)

    @staticmethod
    def test_handles_nan() -> None:
        """Should handle NaN values."""
        normalizer = ZScoreNormalizer()
        result = normalizer.normalize([10.0, float("nan"), 30.0])

        assert len(result) == 3
        assert result[1] == 0.0  # NaN becomes 0

    @staticmethod
    def test_all_nan_values() -> None:
        """Should return zeros for all NaN values."""
        normalizer = ZScoreNormalizer()
        result = normalizer.normalize([float("nan"), float("nan")])

        assert result == [0.0, 0.0]


class TestRobustNormalizerInit:
    """Tests for RobustNormalizer initialization."""

    @staticmethod
    def test_get_name() -> None:
        """Should return 'Robust' as name."""
        assert RobustNormalizer.get_name() == "Robust"


class TestRobustNormalizerNormalize:
    """Tests for RobustNormalizer.normalize method."""

    @staticmethod
    def test_empty_list() -> None:
        """Should return empty list for empty input."""
        normalizer = RobustNormalizer()
        assert normalizer.normalize([]) == []

    @staticmethod
    def test_single_value() -> None:
        """Should return 0.5 for single value."""
        normalizer = RobustNormalizer()
        result = normalizer.normalize([100.0])
        assert result == [0.5]

    @staticmethod
    def test_all_same_values() -> None:
        """Should return 0.5 for all same values (zero IQR)."""
        normalizer = RobustNormalizer()
        result = normalizer.normalize([50.0, 50.0, 50.0])
        assert all(v == 0.5 for v in result)

    @staticmethod
    def test_normal_values() -> None:
        """Should normalize using median and IQR."""
        normalizer = RobustNormalizer()
        result = normalizer.normalize([10.0, 20.0, 30.0, 40.0, 50.0])

        assert len(result) == 5
        # Median is 30, which should map to around 0.5
        assert 0.4 < result[2] < 0.6

    @staticmethod
    def test_resistant_to_outliers() -> None:
        """Should be resistant to outliers."""
        normalizer = RobustNormalizer()
        # Add extreme outlier
        values = [10.0, 20.0, 30.0, 40.0, 1000.0]
        result = normalizer.normalize(values)

        # Middle values should still be reasonable
        assert all(0.0 <= v <= 1.0 for v in result)

    @staticmethod
    def test_handles_nan() -> None:
        """Should handle NaN values."""
        normalizer = RobustNormalizer()
        result = normalizer.normalize([10.0, float("nan"), 30.0])

        assert len(result) == 3
        assert result[1] == 0.0  # NaN becomes 0

    @staticmethod
    def test_all_nan_values() -> None:
        """Should return zeros for all NaN values."""
        normalizer = RobustNormalizer()
        result = normalizer.normalize([float("nan"), float("nan")])

        assert result == [0.0, 0.0]


class TestRobustNormalizerMedian:
    """Tests for RobustNormalizer._median helper."""

    @staticmethod
    def test_odd_count() -> None:
        """Should return middle value for odd count."""
        result = RobustNormalizer._median([1.0, 2.0, 3.0])
        assert result == 2.0

    @staticmethod
    def test_even_count() -> None:
        """Should return average of middle values for even count."""
        result = RobustNormalizer._median([1.0, 2.0, 3.0, 4.0])
        assert result == 2.5

    @staticmethod
    def test_single_value() -> None:
        """Should return value for single element."""
        result = RobustNormalizer._median([5.0])
        assert result == 5.0

    @staticmethod
    def test_unsorted_values() -> None:
        """Should handle unsorted values."""
        result = RobustNormalizer._median([3.0, 1.0, 2.0])
        assert result == 2.0


class TestRobustNormalizerPercentile:
    """Tests for RobustNormalizer._percentile helper."""

    @staticmethod
    def test_25th_percentile() -> None:
        """Should calculate 25th percentile correctly."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = RobustNormalizer._percentile(values, 25)
        assert result == 2.0

    @staticmethod
    def test_50th_percentile() -> None:
        """Should calculate 50th percentile (median) correctly."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = RobustNormalizer._percentile(values, 50)
        assert result == 3.0

    @staticmethod
    def test_75th_percentile() -> None:
        """Should calculate 75th percentile correctly."""
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = RobustNormalizer._percentile(values, 75)
        assert result == 4.0

    @staticmethod
    def test_interpolation() -> None:
        """Should interpolate between values."""
        values = [1.0, 2.0, 3.0, 4.0]
        result = RobustNormalizer._percentile(values, 50)
        assert result == 2.5  # Average of 2 and 3


class TestNormalizerComparison:
    """Tests comparing different normalizers."""

    @staticmethod
    def test_all_produce_valid_range() -> None:
        """All normalizers should produce values in valid range."""
        values = [10.0, 20.0, 30.0, 40.0, 50.0]

        minmax = MinMaxNormalizer(feature_range=(0.0, 1.0))
        zscore = ZScoreNormalizer()
        robust = RobustNormalizer()

        minmax_result = minmax.normalize(values)
        zscore_result = zscore.normalize(values)
        robust_result = robust.normalize(values)

        for result in [minmax_result, zscore_result, robust_result]:
            assert all(0.0 <= v <= 1.0 for v in result)

    @staticmethod
    def test_minmax_0_100_range() -> None:
        """MinMax with default range should produce 0-100 values."""
        normalizer = MinMaxNormalizer()  # Default 0-100
        result = normalizer.normalize([10.0, 50.0, 100.0])

        assert result[0] == 0.0
        assert result[-1] == 100.0
