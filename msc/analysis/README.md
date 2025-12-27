# Analysis Module

Power ranking computation with pluggable normalization strategies.

## Modules

| Module           | Purpose                                               |
|------------------|-------------------------------------------------------|
| `strategy.py`    | Abstract normalization strategy interface             |
| `normalizers.py` | MinMax, ZScore, and Robust normalizer implementations |
| `scorer.py`      | Power ranking scorer with weighted category scoring   |

## Normalization Strategies

The module uses the Strategy Pattern to allow different normalization approaches.

```python
from msc.analysis.normalizers import (
    MinMaxNormalizer,
    ZScoreNormalizer,
    RobustNormalizer,
)

# MinMax: Scales values to 0-100 range (default)
normalizer = MinMaxNormalizer()
values = [10, 20, 30, 40, 50]
normalized = normalizer.normalize(values)
# → [0.0, 25.0, 50.0, 75.0, 100.0]

# ZScore: Standardizes to mean=0, std=1, then scales to 0-100
zscore = ZScoreNormalizer()
normalized = zscore.normalize(values)

# Robust: Uses median and IQR (resistant to outliers)
robust = RobustNormalizer()
normalized = robust.normalize(values)

# All normalizers share the same interface
print(normalizer.get_name())  # "minmax"
print(normalizer.get_description())  # "Min-Max normalization..."
```

## Power Ranking Scorer

Computes weighted scores across multiple statistical categories.

```python
from msc.analysis.scorer import PowerRankingScorer
from msc.models.stats import TrackWithStats

# Initialize scorer (loads category config from _config/categories.json)
scorer = PowerRankingScorer()

# Or with custom normalizer
from msc.analysis.normalizers import RobustNormalizer

scorer = PowerRankingScorer(normalizer=RobustNormalizer())

# Score a collection of enriched tracks
tracks: list[TrackWithStats] = [...]  # From enrichment stage
results = scorer.score(tracks)

# Access results
for ranking in results.rankings:
    print(f"#{ranking.rank}: {ranking.track.title} - Score: {ranking.final_score:.1f}")

    # Category breakdown
    for cat in ranking.category_scores:
        print(f"  {cat.category}: {cat.raw_score:.1f} (weight: {cat.weight}x)")
```

## Scoring Algorithm

The two-level weighting system:

1. **Data Availability Weight**: `non_zero_count / total_tracks` per metric
2. **Category Importance**: Predefined multipliers (1x, 2x, 4x)

```
Category Score = Σ(normalized_metric × availability_weight) / Σ(availability_weight)
Final Score = Σ(category_score × importance × avg_availability) / Σ(importance × avg_availability)
```

### Category Configuration

Categories are defined in `_config/categories.json`:

```json
{
  "streams": [
    "spotify_streams_total",
    "apple_music_plays_total",
    "youtube_views_total"
  ],
  "popularity": [
    "spotify_popularity_current",
    "tiktok_popularity_total"
  ],
  "charts": [
    "spotify_charts_total",
    "apple_music_charts_total"
  ]
}
```

### Weight Levels

| Level      | Multiplier | Categories                             |
|------------|------------|----------------------------------------|
| NEGLIGIBLE | 1x         | Charts, Engagement, Shorts             |
| LOW        | 2x         | Reach, Playlists, Professional Support |
| HIGH       | 4x         | Popularity, Streams                    |

## Custom Normalizer

Implement your own normalization strategy:

```python
from msc.analysis.strategy import NormalizationStrategy


class LogNormalizer(NormalizationStrategy):
    """Logarithmic normalization for highly skewed data."""

    def normalize(self, values: list[float]) -> list[float]:
        import math
        log_values = [math.log1p(v) for v in values]
        min_v, max_v = min(log_values), max(log_values)
        if max_v == min_v:
            return [50.0] * len(values)
        return [(v - min_v) / (max_v - min_v) * 100 for v in log_values]

    def get_name(self) -> str:
        return "log"

    def get_description(self) -> str:
        return "Logarithmic normalization for skewed distributions"


# Use custom normalizer
scorer = PowerRankingScorer(normalizer=LogNormalizer())
```
