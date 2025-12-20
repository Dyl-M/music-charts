"""Strategy pattern interfaces for scoring algorithms.

Defines abstract strategies for normalization and scoring,
allowing different algorithms to be plugged in without
modifying the core scoring engine.
"""

# Standard library
from abc import ABC, abstractmethod
from typing import Any

# Local
from msc.models.stats import TrackWithStats
from msc.models.ranking import CategoryScore, PowerRanking


class NormalizationStrategy(ABC):
    """Abstract strategy for data normalization.

    Defines the interface for different normalization algorithms
    (MinMax, Z-score, RobustScaler, etc.).
    """

    @abstractmethod
    def normalize(self, values: list[float]) -> list[float]:
        """Normalize a list of values to 0-1 range.

        Args:
            values: Raw values to normalize

        Returns:
            Normalized values in [0, 1] range
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this normalization strategy.

        Returns:
            Strategy name for logging/debugging
        """
        ...


class ScoringStrategy(ABC):
    """Abstract strategy for computing power rankings.

    Defines the interface for different scoring algorithms,
    allowing customization of how category scores are combined
    into final rankings.
    """

    @abstractmethod
    def compute_category_scores(
        self, tracks: list[TrackWithStats], category_config: dict[str, Any]
    ) -> dict[str, list[CategoryScore]]:
        """Compute category scores for all tracks.

        Args:
            tracks: List of tracks with statistics
            category_config: Mapping of categories to metrics

        Returns:
            Dictionary mapping category names to lists of CategoryScore objects
        """
        ...

    @abstractmethod
    def compute_power_ranking(
        self,
        track: TrackWithStats,
        category_scores: dict[str, CategoryScore],
        weights: dict[str, int],
    ) -> PowerRanking:
        """Compute final power ranking for a track.

        Args:
            track: Track with statistics
            category_scores: Scores for each category
            weights: Category weight multipliers

        Returns:
            PowerRanking with final score
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this scoring strategy.

        Returns:
            Strategy name for logging/debugging
        """
        ...


class WeightingStrategy(ABC):
    """Abstract strategy for applying category weights.

    Defines how category importance weights are applied
    when computing final scores.
    """

    @abstractmethod
    def apply_weights(
        self, category_scores: dict[str, float], weights: dict[str, int]
    ) -> float:
        """Apply weights to category scores.

        Args:
            category_scores: Raw category scores
            weights: Category weight multipliers

        Returns:
            Weighted final score
        """
        ...

    @abstractmethod
    def get_name(self) -> str:
        """Get the name of this weighting strategy.

        Returns:
            Strategy name for logging/debugging
        """
        ...
