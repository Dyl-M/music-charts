# Models Module

Pydantic data models for tracks, platform statistics, and power rankings.

## Modules

| Module         | Purpose                                                |
|----------------|--------------------------------------------------------|
| `base.py`      | Base model class with frozen (immutable) configuration |
| `track.py`     | Track metadata and Songstats identifiers               |
| `platforms.py` | Per-platform statistics (10 platforms)                 |
| `stats.py`     | Aggregated platform stats and enriched tracks          |
| `youtube.py`   | YouTube video data models                              |
| `ranking.py`   | Power ranking scores and results                       |

## Track Models

Core track representation from MusicBee library.

```python
from msc.models.track import Track, SongstatsIdentifiers

# Create a track
track = Track(
    title="16",
    artist_list=["blasterjaxx", "hardwell", "maddix"],
    artist="Blasterjaxx & Hardwell & Maddix",  # MusicBee "Artist Displayed" tag
    year=2024,
    genre=["hard techno"],
    grouping=["revealed"],
)

# Access properties
print(track.primary_artist)  # "blasterjaxx"
print(track.all_artists_string)  # "blasterjaxx, hardwell, maddix"
print(track.identifier)  # "a1b2c3d4" (8-char UUID5-based, serialized as "track_id")
print(track.legacy_identifier)  # "blasterjaxx_16_2024"
print(track.artist)  # "Blasterjaxx & Hardwell & Maddix" (clean display format)

# Check genre
if track.has_genre("hard techno"):
    print("It's hard techno!")

# Songstats identifiers (populated during extraction)
ids = SongstatsIdentifiers(
    songstats_id="qmr6e0bx",
    songstats_title="16",
    isrc="NL2GV2400041",
    songstats_artists=["Blasterjaxx", "Hardwell", "Maddix"],
    songstats_labels=["Revealed Recordings"],
)
```

## Platform Statistics

Each platform has its own stats model with platform-specific metrics.

```python
from msc.models.platforms import (
    SpotifyStats,
    AppleMusicStats,
    YouTubeStats,
    DeezerStats,
    TikTokStats,
    BeatportStats,
    TidalStats,
    SoundCloudStats,
    AmazonMusicStats,
    TracklistsStats,
)

# Spotify stats example
spotify = SpotifyStats(
    streams_total=1_000_000,
    streams_current=50_000,
    popularity_current=75,
    playlist_reach_total=500_000,
    charts_total=5,
)

# YouTube stats example
youtube = YouTubeStats(
    views_total=2_000_000,
    likes_total=50_000,
    comments_total=1_000,
    shorts_views_total=100_000,
)

# Each model has a to_flat_dict() for DataFrame export
flat = spotify.to_flat_dict()
# {"spotify_streams_total": 1000000, "spotify_popularity_current": 75, ...}
```

## Aggregated Stats

Combine all platform statistics into a single model.

```python
from msc.models.stats import PlatformStats, TrackWithStats

# Aggregate all platform stats
platform_stats = PlatformStats(
    spotify=spotify,
    youtube=youtube,
    apple_music=apple_music,
    # ... other platforms
)

# Access individual platforms
print(platform_stats.spotify.streams_total)

# Enriched track with full statistics
enriched = TrackWithStats(
    track=track,
    stats=platform_stats,
)

# Export to flat dictionary (for pandas/CSV)
flat_dict = enriched.to_flat_dict()
```

## YouTube Video Data

Detailed video information from Songstats.

```python
from msc.models.youtube import YouTubeVideo, YouTubeVideoData

# Individual video
video = YouTubeVideo(
    video_id="dQw4w9WgXcQ",
    title="Official Music Video",
    channel_name="Artist Channel",
    view_count=1_000_000,
    is_topic_channel=False,
)

# Aggregated YouTube data for a track
yt_data = YouTubeVideoData(
    videos=[video],
    total_views=1_000_000,
    video_count=1,
)
```

## Power Rankings

Scoring results with category breakdowns.

```python
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults

# Category score with weight info
category = CategoryScore(
    category="streams",
    raw_score=85.5,
    weighted_score=342.0,  # 85.5 * 4 (HIGH weight)
    weight=4.0,
    data_availability=0.92,
)

# Full power ranking for a track
ranking = PowerRanking(
    track=track,
    final_score=78.5,
    rank=1,
    category_scores=[category, ...],
)

# Collection of all rankings
results = PowerRankingResults(
    rankings=[ranking, ...],
    total_tracks=100,
    timestamp="2025-01-01T00:00:00",
)

# Export to list of dicts
rankings_list = results.to_list()
```

## Model Features

All models share these characteristics:

- **Immutable** (`frozen=True`): Data doesn't change after creation
- **Validated**: Pydantic validates all inputs
- **Serializable**: `model_dump(by_alias=True)` for export with proper field names
- **Track IDs**: `identifier` property serializes as `track_id` in JSON output
- **Legacy Support**: `from_legacy_json()` for old data formats
- **Flat Export**: `to_flat_dict()` for DataFrame compatibility
