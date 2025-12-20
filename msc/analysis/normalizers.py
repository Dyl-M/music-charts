"""Concrete normalization strategy implementations.

Provides ready-to-use normalization algorithms for
scaling raw metric values to comparable ranges.
"""

# Standard library
import math

# Local
from msc.analysis.strategy import NormalizationStrategy
from msc.utils.logging import get_logger


class MinMaxNormalizer(NormalizationStrategy):
    """Min-Max normalization strategy.

    Scales values to [0, 1] range using formula:
    normalized = (value - min) / (max - min)

    Handles edge cases:
    - All same values → all become 0.5
    - Single value → becomes 0.5
    - Empty list → returns empty list
    """

    def __init__(self) -> None:
        """Initialize Min-Max normalizer."""
        self.logger = get_logger(__name__)

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize values to [0, 1] range using Min-Max scaling.

        Args:
            values: Raw values to normalize

        Returns:
            Normalized values in [0, 1] range
        """
        if not values:
            return []

        # Filter out NaN and infinite values
        clean_values = [v for v in values if math.isfinite(v)]

        if not clean_values:
            self.logger.warning("All values are NaN or infinite, returning zeros")
            return [0.0] * len(values)

        min_val = min(clean_values)
        max_val = max(clean_values)

        # Edge case: all values are the same
        if min_val == max_val:
            self.logger.debug("All values are equal (%f), normalizing to 0.5", min_val)
            return [0.5 if math.isfinite(v) else 0.0 for v in values]

        # Standard Min-Max normalization
        normalized = []
        for value in values:
            if not math.isfinite(value):
                normalized.append(0.0)
            else:
                normalized_value = (value - min_val) / (max_val - min_val)
                normalized.append(normalized_value)

        return normalized

    def get_name(self) -> str:
        """Get the name of this normalization strategy."""
        return "MinMax"


class ZScoreNormalizer(NormalizationStrategy):
    """Z-Score (standardization) normalization strategy.

    Scales values using mean and standard deviation:
    normalized = (value - mean) / std_dev

    Then clips to [0, 1] range for consistency.
    """

    def __init__(self) -> None:
        """Initialize Z-Score normalizer."""
        self.logger = get_logger(__name__)

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize values using Z-score standardization.

        Args:
            values: Raw values to normalize

        Returns:
            Normalized values (clipped to [0, 1])
        """
        if not values:
            return []

        # Filter out NaN and infinite values
        clean_values = [v for v in values if math.isfinite(v)]

        if not clean_values:
            self.logger.warning("All values are NaN or infinite, returning zeros")
            return [0.0] * len(values)

        mean = sum(clean_values) / len(clean_values)

        # Calculate standard deviation
        variance = sum((v - mean) ** 2 for v in clean_values) / len(clean_values)
        std_dev = math.sqrt(variance)

        # Edge case: zero standard deviation
        if std_dev == 0:
            self.logger.debug("Zero standard deviation, normalizing to 0.5")
            return [0.5 if math.isfinite(v) else 0.0 for v in values]

        # Z-score normalization with clipping
        normalized = []
        for value in values:
            if not math.isfinite(value):
                normalized.append(0.0)
            else:
                z_score = (value - mean) / std_dev
                # Clip to reasonable range and scale to [0, 1]
                # Z-scores beyond ±3 are rare (>99% of data is within ±3σ)
                clipped = max(-3.0, min(3.0, z_score))
                scaled = (clipped + 3.0) / 6.0  # Map [-3, 3] to [0, 1]
                normalized.append(scaled)

        return normalized

    def get_name(self) -> str:
        """Get the name of this normalization strategy."""
        return "ZScore"


class RobustNormalizer(NormalizationStrategy):
    """Robust normalization using median and IQR.

    Uses median and interquartile range for normalization,
    making it resistant to outliers:
    normalized = (value - median) / IQR

    Then clips to [0, 1] range.
    """

    def __init__(self) -> None:
        """Initialize Robust normalizer."""
        self.logger = get_logger(__name__)

    @staticmethod
    def _median(values: list[float]) -> float:
        """Calculate median of values.

        Args:
            values: List of values

        Returns:
            Median value
        """
        sorted_values = sorted(values)
        n = len(sorted_values)

        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        return sorted_values[n // 2]

    @staticmethod
    def _percentile(values: list[float], p: float) -> float:
        """Calculate percentile of values.

        Args:
            values: List of values
            p: Percentile (0-100)

        Returns:
            Percentile value
        """
        sorted_values = sorted(values)
        k = (len(sorted_values) - 1) * p / 100
        f = math.floor(k)
        c = math.ceil(k)

        if f == c:
            return sorted_values[int(k)]

        d0 = sorted_values[int(f)] * (c - k)
        d1 = sorted_values[int(c)] * (k - f)
        return d0 + d1

    def normalize(self, values: list[float]) -> list[float]:
        """Normalize values using robust scaling.

        Args:
            values: Raw values to normalize

        Returns:
            Normalized values (clipped to [0, 1])
        """
        if not values:
            return []

        # Filter out NaN and infinite values
        clean_values = [v for v in values if math.isfinite(v)]

        if not clean_values:
            self.logger.warning("All values are NaN or infinite, returning zeros")
            return [0.0] * len(values)

        median = self._median(clean_values)
        q1 = self._percentile(clean_values, 25)
        q3 = self._percentile(clean_values, 75)
        iqr = q3 - q1

        # Edge case: zero IQR
        if iqr == 0:
            self.logger.debug("Zero IQR, normalizing to 0.5")
            return [0.5 if math.isfinite(v) else 0.0 for v in values]

        # Robust normalization with clipping
        normalized = []
        for value in values:
            if not math.isfinite(value):
                normalized.append(0.0)
            else:
                robust_score = (value - median) / iqr
                # Clip to reasonable range
                clipped = max(-3.0, min(3.0, robust_score))
                scaled = (clipped + 3.0) / 6.0  # Map [-3, 3] to [0, 1]
                normalized.append(scaled)

        return normalized

    def get_name(self) -> str:
        """Get the name of this normalization strategy."""
        return "Robust"
