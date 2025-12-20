"""Tests for normalization strategies.

Tests MinMaxNormalizer, RobustNormalizer, and ZScoreNormalizer
for edge cases, mathematical correctness, and boundary conditions.
"""

# Third-party
import pytest

# Local
from msc.analysis.normalizers import (
    MinMaxNormalizer,
    RobustNormalizer,
    ZScoreNormalizer,
)


class TestMinMaxNormalizer:
    """Tests for MinMaxNormalizer (0-1 range scaling)."""

    @staticmethod
    def test_normalize_typical_values() -> None:
        """Test normalization of typical values."""
        normalizer = MinMaxNormalizer()
        values = [10.0, 20.0, 30.0, 40.0, 50.0]

        result = normalizer.normalize(values)

        assert len(result) == 5
        assert result[0] == 0.0  # Min value → 0
        assert result[4] == 1.0  # Max value → 1
        assert result[2] == 0.5  # Mid value → 0.5

    @staticmethod
    def test_normalize_single_value() -> None:
        """Test normalization of single value."""
        normalizer = MinMaxNormalizer()
        values = [42.0]

        result = normalizer.normalize(values)

        assert len(result) == 1
        assert result[0] == 0.5  # Single value → 0.5 (all same)

    @staticmethod
    def test_normalize_all_same_values() -> None:
        """Test normalization when all values are identical."""
        normalizer = MinMaxNormalizer()
        values = [5.0, 5.0, 5.0, 5.0]

        result = normalizer.normalize(values)

        assert len(result) == 4
        assert all(v == 0.5 for v in result)  # All same → 0.5

    @staticmethod
    def test_normalize_with_zeros() -> None:
        """Test normalization with zero values."""
        normalizer = MinMaxNormalizer()
        values = [0.0, 10.0, 20.0]

        result = normalizer.normalize(values)

        assert result[0] == 0.0  # Min (0) → 0
        assert result[2] == 1.0  # Max (20) → 1
        assert result[1] == 0.5  # Mid (10) → 0.5

    @staticmethod
    def test_normalize_negative_values() -> None:
        """Test normalization with negative values."""
        normalizer = MinMaxNormalizer()
        values = [-10.0, 0.0, 10.0]

        result = normalizer.normalize(values)

        assert result[0] == 0.0  # Min (-10) → 0
        assert result[2] == 1.0  # Max (10) → 1
        assert result[1] == 0.5  # Mid (0) → 0.5

    @staticmethod
    def test_normalize_empty_list() -> None:
        """Test normalization of empty list."""
        normalizer = MinMaxNormalizer()
        values = []

        result = normalizer.normalize(values)

        assert result == []

    @staticmethod
    def test_normalize_large_range() -> None:
        """Test normalization with very large range."""
        normalizer = MinMaxNormalizer()
        values = [0.0, 1000000.0]

        result = normalizer.normalize(values)

        assert result[0] == 0.0
        assert result[1] == 1.0

    @staticmethod
    def test_normalize_preserves_order() -> None:
        """Test that normalization preserves relative order."""
        normalizer = MinMaxNormalizer()
        values = [5.0, 2.0, 8.0, 1.0, 9.0]

        result = normalizer.normalize(values)

        # Check that relative order is preserved
        for i in range(len(values) - 1):
            for j in range(i + 1, len(values)):
                if values[i] < values[j]:
                    assert result[i] < result[j]
                elif values[i] > values[j]:
                    assert result[i] > result[j]
                else:
                    assert result[i] == result[j]

    @staticmethod
    def test_get_name() -> None:
        """Test getting normalizer name."""
        normalizer = MinMaxNormalizer()
        assert normalizer.get_name() == "MinMax"


class TestRobustNormalizer:
    """Tests for RobustNormalizer (median/IQR scaling)."""

    @staticmethod
    def test_normalize_typical_values() -> None:
        """Test normalization of typical values."""
        normalizer = RobustNormalizer()
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]

        result = normalizer.normalize(values)

        assert len(result) == 9
        # Median is 5.0, should map to 0.5 (center of [0,1])
        assert abs(result[4] - 0.5) < 0.01

    @staticmethod
    def test_normalize_with_outliers() -> None:
        """Test that outliers don't skew normalization."""
        normalizer = RobustNormalizer()
        # Regular values with outliers
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 200.0]

        result = normalizer.normalize(values)

        # Core values should be normalized reasonably
        # despite extreme outliers
        assert len(result) == 7

    @staticmethod
    def test_normalize_all_same_values() -> None:
        """Test normalization when all values are identical."""
        normalizer = RobustNormalizer()
        values = [5.0, 5.0, 5.0, 5.0]

        result = normalizer.normalize(values)

        assert len(result) == 4
        assert all(v == 0.5 for v in result)  # Zero IQR → 0.5

    @staticmethod
    def test_normalize_single_value() -> None:
        """Test normalization of single value."""
        normalizer = RobustNormalizer()
        values = [42.0]

        result = normalizer.normalize(values)

        assert len(result) == 1
        assert result[0] == 0.5  # Zero IQR → 0.5

    @staticmethod
    def test_normalize_empty_list() -> None:
        """Test normalization of empty list."""
        normalizer = RobustNormalizer()
        values = []

        result = normalizer.normalize(values)

        assert result == []

    @staticmethod
    def test_get_name() -> None:
        """Test getting normalizer name."""
        normalizer = RobustNormalizer()
        assert normalizer.get_name() == "Robust"


class TestZScoreNormalizer:
    """Tests for ZScoreNormalizer (standardization)."""

    @staticmethod
    def test_normalize_typical_values() -> None:
        """Test normalization of typical values."""
        normalizer = ZScoreNormalizer()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = normalizer.normalize(values)

        assert len(result) == 5
        # ZScore clips to [-3, 3] and scales to [0, 1]
        # Mean value (3.0) should map close to 0.5
        assert 0.0 <= result[2] <= 1.0

    @staticmethod
    def test_normalize_standard_deviation() -> None:
        """Test that normalized values are in [0, 1] range."""
        normalizer = ZScoreNormalizer()
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

        result = normalizer.normalize(values)

        # All values should be in [0, 1] range after clipping and scaling
        assert all(0.0 <= v <= 1.0 for v in result)

    @staticmethod
    def test_normalize_all_same_values() -> None:
        """Test normalization when all values are identical."""
        normalizer = ZScoreNormalizer()
        values = [5.0, 5.0, 5.0, 5.0]

        result = normalizer.normalize(values)

        assert len(result) == 4
        assert all(v == 0.5 for v in result)  # Zero std dev → 0.5

    @staticmethod
    def test_normalize_single_value() -> None:
        """Test normalization of single value."""
        normalizer = ZScoreNormalizer()
        values = [42.0]

        result = normalizer.normalize(values)

        assert len(result) == 1
        assert result[0] == 0.5  # Zero std dev → 0.5

    @staticmethod
    def test_normalize_negative_values() -> None:
        """Test normalization with negative values."""
        normalizer = ZScoreNormalizer()
        values = [-10.0, -5.0, 0.0, 5.0, 10.0]

        result = normalizer.normalize(values)

        # All values should be in [0, 1] range
        assert all(0.0 <= v <= 1.0 for v in result)

    @staticmethod
    def test_normalize_empty_list() -> None:
        """Test normalization of empty list."""
        normalizer = ZScoreNormalizer()
        values = []

        result = normalizer.normalize(values)

        assert result == []

    @staticmethod
    def test_get_name() -> None:
        """Test getting normalizer name."""
        normalizer = ZScoreNormalizer()
        assert normalizer.get_name() == "ZScore"


class TestNormalizationBoundaryConditions:
    """Tests for boundary conditions across all normalizers."""

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_preserves_length(normalizer_class) -> None:
        """Test that normalization preserves input length."""
        normalizer = normalizer_class()
        values = [1.0, 2.0, 3.0, 4.0, 5.0]

        result = normalizer.normalize(values)

        assert len(result) == len(values)

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_handles_empty(normalizer_class) -> None:
        """Test that all normalizers handle empty input."""
        normalizer = normalizer_class()
        result = normalizer.normalize([])
        assert result == []

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_handles_single_value(normalizer_class) -> None:
        """Test that all normalizers handle single value."""
        normalizer = normalizer_class()
        result = normalizer.normalize([42.0])
        assert len(result) == 1
        assert result[0] == 0.5  # All normalizers return 0.5 for single/same values

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_handles_all_same(normalizer_class) -> None:
        """Test that all normalizers handle identical values."""
        normalizer = normalizer_class()
        result = normalizer.normalize([5.0, 5.0, 5.0, 5.0])
        assert all(v == 0.5 for v in result)  # All normalizers return 0.5

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_returns_floats(normalizer_class) -> None:
        """Test that normalization returns float values."""
        normalizer = normalizer_class()
        values = [1.0, 2.0, 3.0]

        result = normalizer.normalize(values)

        assert all(isinstance(v, float) for v in result)

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_handles_very_small_values(normalizer_class) -> None:
        """Test normalization with very small values."""
        normalizer = normalizer_class()
        values = [0.0001, 0.0002, 0.0003]

        result = normalizer.normalize(values)

        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)

    @staticmethod
    @pytest.mark.parametrize(
        "normalizer_class",
        [MinMaxNormalizer, RobustNormalizer, ZScoreNormalizer],
    )
    def test_normalize_handles_very_large_values(normalizer_class) -> None:
        """Test normalization with very large values."""
        normalizer = normalizer_class()
        values = [1000000.0, 2000000.0, 3000000.0]

        result = normalizer.normalize(values)

        assert len(result) == 3
        assert all(isinstance(v, float) for v in result)
