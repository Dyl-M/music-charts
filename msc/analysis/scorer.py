"""Power ranking scorer with strategy pattern.

Implements the core scoring algorithm for computing power rankings
using pluggable normalization and weighting strategies.
"""

# Standard library
import json
from pathlib import Path

# Local
from msc.analysis.normalizers import MinMaxNormalizer
from msc.analysis.strategy import NormalizationStrategy
from msc.config.constants import CATEGORY_WEIGHTS, StatCategory
from msc.config.settings import get_settings
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.stats import TrackWithStats
from msc.utils.logging import get_logger

# Platform name mapping: categories.json naming → PlatformStats field names
PLATFORM_NAME_MAP = {
    "1001tracklists": "tracklists",  # 1001tracklists_unique_support → tracklists
    "amazon": "amazon_music",  # amazon_charts_total → amazon_music
}


class PowerRankingScorer:
    """Computes power rankings for tracks using weighted category scoring.

    Implements the two-level weighting system:
    1. Data availability: proportion of metrics with data in each category
    2. Category importance: predefined weights (negligible, low, high)

    Uses a pluggable normalization strategy (default: MinMaxScaler).
    """

    def __init__(
            self,
            category_config_path: Path | None = None,
            normalizer: NormalizationStrategy | None = None,
    ) -> None:
        """Initialize the power ranking scorer.

        Args:
            category_config_path: Path to categories.json file
            normalizer: Normalization strategy (default: MinMaxNormalizer)
        """
        self.settings = get_settings()
        self.logger = get_logger(__name__)

        # Load category configuration
        if category_config_path is None:
            category_config_path = self.settings.config_dir / "categories.json"

        self.category_config = self._load_category_config(category_config_path)

        # Set normalization strategy
        self.normalizer = normalizer or MinMaxNormalizer()

        self.logger.info(
            "Initialized PowerRankingScorer with %s normalization",
            self.normalizer.get_name(),
        )

    def _load_category_config(self, config_path: Path) -> dict[str, list[str]]:
        """Load category configuration from JSON file.

        Args:
            config_path: Path to categories.json

        Returns:
            Dictionary mapping category names to metric lists
        """
        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            self.logger.info("Loaded category config from %s", config_path)
            return config
        except (FileNotFoundError, json.JSONDecodeError, OSError) as error:
            self.logger.exception("Failed to load category config from %s: %s", config_path, error)
            # Return empty config as fallback (defensive coding)
            return {}

    def _get_metric_value(self, track: TrackWithStats, metric_name: str) -> float | None:
        """Extract a metric value from track stats.

        Args:
            track: Track with platform statistics
            metric_name: Name of the metric to extract

        Returns:
            Metric value if available, None otherwise
        """
        # Parse metric name: "{platform}_{metric}"
        # e.g., "spotify_streams_total" → platform="spotify", metric="streams_total"

        parts = metric_name.split("_", 1)
        if len(parts) != 2:
            self.logger.warning("Invalid metric name format: %s", metric_name)
            return None

        platform_name, metric_suffix = parts

        # Map platform name to PlatformStats field name
        platform_field = PLATFORM_NAME_MAP.get(platform_name, platform_name)

        # Get platform stats
        platform_stats = getattr(track.platform_stats, platform_field, None)
        if platform_stats is None:
            return None

        # Get metric value from platform stats
        # Try to get the attribute directly
        value = getattr(platform_stats, metric_suffix, None)

        # For special cases like "popularity_peak", check if it's in a nested structure
        if value is None and "peak" in metric_suffix:
            # e.g., "popularity_peak" might be under platform_stats.popularity.peak
            base_metric = metric_suffix.replace("_peak", "")
            base_value = getattr(platform_stats, f"{base_metric}_peak", None)
            if base_value is not None:
                value = base_value

        return value if isinstance(value, (int, float)) else None

    def _compute_raw_category_sum(
            self, track: TrackWithStats, metrics: list[str]
    ) -> float:
        """Compute raw sum of metric values for a category.

        Args:
            track: Track with statistics
            metrics: List of metric names in this category

        Returns:
            Sum of all metric values in the category
        """
        # Extract metric values
        values: list[float] = []

        for metric_name in metrics:
            value = self._get_metric_value(track, metric_name)
            if value is not None and value > 0:
                values.append(float(value))
            else:
                values.append(0.0)

        # Return raw sum (will be normalized later)
        return sum(values)

    def compute_rankings(self, tracks: list[TrackWithStats]) -> PowerRankingResults:
        """Compute power rankings for all tracks.

        Args:
            tracks: List of tracks with statistics

        Returns:
            PowerRankingResults containing ranked tracks
        """
        if not tracks:
            self.logger.warning("No tracks provided for ranking")
            # Return empty results with current year
            return PowerRankingResults(rankings=[], year=self.settings.year)

        self.logger.info("Computing power rankings for %d tracks", len(tracks))

        # Step 1: Compute raw category sums for all tracks
        all_category_sums: dict[str, list[float]] = {
            category: [] for category in self.category_config
        }

        track_raw_sums: dict[str, dict[str, float]] = {}

        for track in tracks:
            track_sums = {}
            for category_name, metrics in self.category_config.items():
                raw_sum = self._compute_raw_category_sum(track, metrics)
                track_sums[category_name] = raw_sum
                all_category_sums[category_name].append(raw_sum)

            track_raw_sums[track.identifier] = track_sums

        # Step 2: Normalize sums within each category (0-1 range)
        normalized_category_scores: dict[str, list[float]] = {}

        for category_name, raw_sums in all_category_sums.items():
            normalized_values = self.normalizer.normalize(raw_sums)
            normalized_category_scores[category_name] = normalized_values

        # Step 3: Create CategoryScore objects and compute final rankings
        rankings_temp: list[tuple[Track, float, list[CategoryScore]]] = []

        for track_idx, track in enumerate(tracks):
            category_scores: list[CategoryScore] = []

            for category_name in self.category_config.keys():
                # Get normalized score for this track in this category
                normalized_score = normalized_category_scores[category_name][track_idx]

                # Get weight from constants
                try:
                    stat_category = StatCategory(category_name)
                    weight = CATEGORY_WEIGHTS[stat_category]
                except (ValueError, KeyError):
                    self.logger.warning("Unknown category %s, using weight 1", category_name)
                    weight = 1

                # Calculate weighted score
                weighted_score = normalized_score * weight

                # Create CategoryScore with correct fields
                category_score = CategoryScore(
                    category=category_name,
                    raw_score=normalized_score,  # Model expects 0-1 normalized value here
                    weight=weight,
                    weighted_score=weighted_score,
                )

                category_scores.append(category_score)

            # Compute total score (sum of all weighted category scores)
            total_score = sum(score.weighted_score for score in category_scores)

            # Store temporarily (rank will be assigned after sorting)
            rankings_temp.append((track, total_score, category_scores))

        # Step 4: Sort by total score (descending) and create PowerRanking objects
        rankings_temp.sort(key=lambda x: x[1], reverse=True)

        rankings: list[PowerRanking] = []
        for rank, (track, total_score, category_scores) in enumerate(rankings_temp, start=1):
            power_ranking = PowerRanking(
                track=track.track,  # Extract Track from TrackWithStats
                total_score=total_score,  # Correct field name
                rank=rank,
                category_scores=category_scores,  # List of CategoryScore
            )
            rankings.append(power_ranking)

        self.logger.info(
            "Computed rankings: Top track is '%s - %s' with score %.2f",
            rankings[0].track.primary_artist if rankings else "N/A",
            rankings[0].track.title if rankings else "N/A",
            rankings[0].total_score if rankings else 0.0,
        )

        return PowerRankingResults(rankings=rankings, year=self.settings.year)
