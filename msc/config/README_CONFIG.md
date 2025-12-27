# Config Module

Runtime configuration and static constants for the Music Charts pipeline.

## Modules

| Module         | Purpose                                             |
|----------------|-----------------------------------------------------|
| `settings.py`  | Pydantic settings with environment variable support |
| `constants.py` | Enumerations, weights, API endpoints, and patterns  |

## Settings

The `Settings` class uses Pydantic's `BaseSettings` to load configuration from environment variables (prefixed with
`MSC_`) or a `.env` file.

```python
from msc.config.settings import get_settings

# Get singleton settings instance
settings = get_settings()

# Access configuration values
print(settings.year)  # 2025
print(settings.musicbee_library)  # Path to MusicBee library
print(settings.songstats_rate_limit)  # 10 requests/second

# Get API credentials
api_key = settings.get_songstats_key()  # From file or env var

# Computed paths
print(settings.output_dir)  # _data/output
print(settings.year_output_dir)  # _data/output/2025
print(settings.cache_dir)  # _data/cache

# Ensure all directories exist
settings.ensure_directories()
```

### Environment Variables

| Variable                   | Default          | Description             |
|----------------------------|------------------|-------------------------|
| `MSC_YEAR`                 | 2025             | Target analysis year    |
| `MSC_PLAYLIST_ID`          | "4361"           | MusicBee playlist ID    |
| `MSC_MUSICBEE_LIBRARY`     | `E:/Musique/...` | Path to library XML     |
| `MSC_SONGSTATS_RATE_LIMIT` | 10               | API requests per second |
| `MSC_SONGSTATS_API_KEY`    | None             | Songstats API key       |

## Constants

Static values used throughout the pipeline.

```python
from msc.config.constants import (
    Platform,
    StatCategory,
    WeightLevel,
    CATEGORY_WEIGHTS,
    SONGSTATS_ENDPOINTS,
    REJECT_KEYWORDS,
)

# Platform enumeration
for platform in Platform:
    print(platform.value)  # spotify, appleMusic, youtube, ...

# Songstats API sources
sources = Platform.songstats_sources()
# ('spotify', 'apple_music', 'amazon', 'deezer', ...)

# Category weights for power ranking
weights = CATEGORY_WEIGHTS
# {StatCategory.CHARTS: 1, StatCategory.STREAMS: 4, ...}

# API endpoints
search_url = SONGSTATS_ENDPOINTS["search"]
# https://api.songstats.com/enterprise/v1/tracks/search

# False positive detection keywords
if any(kw in title.lower() for kw in REJECT_KEYWORDS):
    print("Likely a karaoke/cover version")
```

### Weight Levels

| Level        | Multiplier | Categories                             |
|--------------|------------|----------------------------------------|
| `NEGLIGIBLE` | 1x         | Charts, Engagement, Shorts             |
| `LOW`        | 2x         | Reach, Playlists, Professional Support |
| `HIGH`       | 4x         | Popularity, Streams                    |
