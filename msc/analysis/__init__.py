"""Analytics and scoring modules.

Exports:
    Strategy interfaces:
        - NormalizationStrategy: Interface for normalization algorithms
        - ScoringStrategy: Interface for scoring algorithms
        - WeightingStrategy: Interface for weighting strategies

    Concrete strategies:
        - MinMaxNormalizer: Min-Max normalization (0-1 range)
        - ZScoreNormalizer: Z-Score standardization
        - RobustNormalizer: Median and IQR normalization

    Scoring engine:
        - PowerRankingScorer: Computes power rankings with weighted categories
"""

# Local
from msc.analysis.normalizers import (
    MinMaxNormalizer,
    RobustNormalizer,
    ZScoreNormalizer,
)

from msc.analysis.scorer import PowerRankingScorer

from msc.analysis.strategy import (
    NormalizationStrategy,
    ScoringStrategy,
    WeightingStrategy,
)

__all__ = [
    # Strategy interfaces
    "NormalizationStrategy",
    "ScoringStrategy",
    "WeightingStrategy",
    # Concrete normalizers
    "MinMaxNormalizer",
    "ZScoreNormalizer",
    "RobustNormalizer",
    # Scoring engine
    "PowerRankingScorer",
]
