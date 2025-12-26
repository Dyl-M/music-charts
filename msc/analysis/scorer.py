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
from msc.utils.path_utils import validate_path_within_base

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
            validate_path = True
        else:
            validate_path = False

        self.category_config = self._load_category_config(category_config_path, validate_path)

        # Set normalization strategy
        self.normalizer = normalizer or MinMaxNormalizer()

        self.logger.info(
            "Initialized PowerRankingScorer with %s normalization",
            self.normalizer.get_name(),
        )

    def _load_category_config(
            self, config_path: Path, validate: bool = True
    ) -> dict[str, list[str]]:
        """Load category configuration from JSON file.

        Args:
            config_path: Path to categories.json
            validate: If True, validate path is within config directory

        Returns:
            Dictionary mapping category names to metric lists
        """
        try:
            # Validate path if using default location
            if validate:
                config_path = validate_path_within_base(
                    config_path, self.settings.config_dir, "config load"
                )

            else:
                # Just resolve the path for security without base validation
                config_path = config_path.resolve()

            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)

            self.logger.info("Loaded category config from %s", config_path)
            return config

        except (OSError, json.JSONDecodeError) as error:
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

    def _collect_metric_values(
            self, tracks: list[TrackWithStats], metrics: list[str]
    ) -> dict[str, list[float]]:
        """Collect raw metric values for all tracks.

        Args:
            tracks: List of tracks with statistics
            metrics: List of metric names to collect

        Returns:
            Dictionary mapping metric name to list of values (one per track)
        """
        metric_values: dict[str, list[float]] = {metric: [] for metric in metrics}

        for track in tracks:
            for metric_name in metrics:
                value = self._get_metric_value(track, metric_name)
                # Use 0.0 for missing/None values
                metric_values[metric_name].append(float(value) if value is not None else 0.0)

        return metric_values

    @staticmethod
    def _compute_availability_weights(
            metric_values: dict[str, list[float]]
    ) -> dict[str, float]:
        """Compute data availability weight for each metric.

        Availability = proportion of tracks with non-zero value for this metric.

        Args:
            metric_values: Dictionary of metric name to list of values

        Returns:
            Dictionary mapping metric name to availability weight (0.0 to 1.0)
        """
        availability: dict[str, float] = {}
        for metric_name, values in metric_values.items():
            if not values:
                availability[metric_name] = 0.0
            else:
                non_zero_count = sum(1 for v in values if v > 0)
                availability[metric_name] = non_zero_count / len(values)

        return availability

    def _compute_category_scores(
            self,
            tracks: list[TrackWithStats],
            category_name: str,
            metrics: list[str],
    ) -> tuple[list[float], float]:
        """Compute power ranking scores for a single category.

        Uses the legacy algorithm:
        1. Normalize each metric to 0-100 range
        2. Weight by data availability (proportion of non-zero values)
        3. Category score = weighted average of normalized metrics

        Args:
            tracks: List of tracks
            category_name: Name of the category
            metrics: List of metrics in this category

        Returns:
            Tuple of (list of scores per track, category_weight)
        """
        if not metrics:
            return [0.0] * len(tracks), 0.0

        # Step 1: Collect raw metric values
        metric_values = self._collect_metric_values(tracks, metrics)

        # Step 2: Normalize each metric to 0-100 range
        normalized_metrics: dict[str, list[float]] = {}
        for metric_name, values in metric_values.items():
            normalized_metrics[metric_name] = self.normalizer.normalize(values)

        # Step 3: Compute availability weights
        availability_weights = self._compute_availability_weights(metric_values)

        # Step 4: Compute weighted average score per track
        # Formula: score = sum(normalized_stat × availability) / sum(availability)
        track_scores: list[float] = []
        total_availability = sum(availability_weights.values())

        for track_idx in range(len(tracks)):
            if total_availability == 0:
                track_scores.append(0.0)
                continue

            weighted_sum = 0.0
            for metric_name in metrics:
                norm_value = normalized_metrics[metric_name][track_idx]
                avail_weight = availability_weights[metric_name]
                weighted_sum += norm_value * avail_weight

            score = weighted_sum / total_availability
            track_scores.append(score)

        # Step 5: Compute category weight = avg_availability
        avg_availability = total_availability / len(metrics) if metrics else 0.0

        self.logger.debug(
            "Category '%s': avg_availability=%.3f, metrics=%d",
            category_name,
            avg_availability,
            len(metrics),
        )

        return track_scores, avg_availability

    def compute_rankings(self, tracks: list[TrackWithStats]) -> PowerRankingResults:
        """Compute power rankings for all tracks.

        Uses the legacy algorithm:
        1. Per category: normalize metrics to 0-100, weight by data availability
        2. Category weight = avg_availability × importance_multiplier
        3. Final score = weighted average of category scores (0-100 range)

        Args:
            tracks: List of tracks with statistics

        Returns:
            PowerRankingResults containing ranked tracks
        """
        if not tracks:
            self.logger.warning("No tracks provided for ranking")
            return PowerRankingResults(rankings=[], year=self.settings.year)

        self.logger.info("Computing power rankings for %d tracks", len(tracks))

        # Step 1: Compute category scores and weights
        category_data: dict[str, tuple[list[float], float]] = {}

        for category_name, metrics in self.category_config.items():
            scores, avg_availability = self._compute_category_scores(
                tracks, category_name, metrics
            )
            category_data[category_name] = (scores, avg_availability)

        # Step 2: Apply importance multipliers to get effective weights
        category_weights: dict[str, float] = {}
        for category_name, (_, avg_availability) in category_data.items():
            try:
                stat_category = StatCategory(category_name)
                importance = CATEGORY_WEIGHTS[stat_category]
            except (ValueError, KeyError):
                self.logger.warning("Unknown category %s, using importance 1", category_name)
                importance = 1

            # Effective weight = availability × importance
            category_weights[category_name] = avg_availability * importance

        total_weight = sum(category_weights.values())

        # Step 3: Compute final scores per track (weighted average)
        rankings_temp: list[tuple[TrackWithStats, float, list[CategoryScore]]] = []

        for track_idx, track in enumerate(tracks):
            category_scores: list[CategoryScore] = []
            weighted_score_sum = 0.0

            for category_name in self.category_config.keys():
                raw_score = category_data[category_name][0][track_idx]
                weight = category_weights[category_name]
                weighted_score = raw_score * weight

                category_score = CategoryScore(
                    category=category_name,
                    raw_score=raw_score,  # 0-100 normalized
                    weight=weight,  # availability × importance
                    weighted_score=weighted_score,
                )
                category_scores.append(category_score)
                weighted_score_sum += weighted_score

            # Final score = weighted average (0-100 range)
            total_score = weighted_score_sum / total_weight if total_weight > 0 else 0.0

            rankings_temp.append((track, total_score, category_scores))

        # Step 4: Sort by total score (descending) and assign ranks
        rankings_temp.sort(key=lambda x: x[1], reverse=True)

        rankings: list[PowerRanking] = []
        for rank, (track, total_score, category_scores) in enumerate(rankings_temp, start=1):
            power_ranking = PowerRanking(
                track=track.track,
                total_score=total_score,
                rank=rank,
                category_scores=category_scores,
            )
            rankings.append(power_ranking)

        self.logger.info(
            "Computed rankings: Top track is '%s - %s' with score %.2f",
            rankings[0].track.primary_artist if rankings else "N/A",
            rankings[0].track.title if rankings else "N/A",
            rankings[0].total_score if rankings else 0.0,
        )

        return PowerRankingResults(rankings=rankings, year=self.settings.year)
