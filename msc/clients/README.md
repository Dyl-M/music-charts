# Clients Module

API clients for external data sources with built-in rate limiting, retry logic, and session management.

## Modules

| Module         | Purpose                                              |
|----------------|------------------------------------------------------|
| `base.py`      | Abstract base class with common client functionality |
| `musicbee.py`  | MusicBee library XML parser                          |
| `songstats.py` | Songstats Enterprise API client                      |
| `youtube.py`   | YouTube Data API client (OAuth 2.0)                  |

## Base Client

All clients inherit from `BaseClient`, which provides:

- Session management with connection pooling
- Rate limiting via `RateLimiter`
- Automatic retry with exponential backoff
- Structured logging

```python
from msc.clients.base import BaseClient

# All clients support context manager pattern
with SongstatsClient() as client:
    result = client.search_track("artist song")
# Session automatically closed
```

## MusicBee Client

Parse MusicBee's iTunes-format XML library.

```python
from msc.clients.musicbee import MusicBeeClient
from pathlib import Path

# Initialize with library path
client = MusicBeeClient(library_path=Path("path/to/library.xml"))

# Get all playlists
playlists = client.get_playlists()
for p in playlists:
    print(f"{p['name']} (ID: {p['id']}, {p['track_count']} tracks)")

# Find playlist by name
playlist = client.find_playlist_by_name("DJ Selection 2025")

# Get tracks from playlist (returns Track models)
tracks = client.get_playlist_tracks(playlist_id="4361")
for track in tracks:
    print(f"{track.primary_artist} - {track.title}")
```

## Songstats Client

Fetch track data and cross-platform statistics from Songstats API.

```python
from msc.clients.songstats import SongstatsClient

# Initialize (API key loaded from settings or env)
client = SongstatsClient()

# Check API quota
quota = client.get_quota()
print(f"Used: {quota['requests_used']}/{quota['requests_limit']}")

# Search for a track
results = client.search_track("hardwell blasterjaxx 16", limit=3)
for r in results:
    print(f"{r['title']} by {r['artists']} (ID: {r['songstats_id']})")

# Get track info (links, platform availability)
info = client.get_track_info(songstats_id="qmr6e0bx")

# Get track metadata (title, artists, labels, ISRC)
# Useful for repopulating manually-added Songstats IDs
metadata = client.get_track_metadata(songstats_id="qmr6e0bx")
print(f"Title: {metadata['title']}")
print(f"Artists: {metadata['artists']}")
print(f"Labels: {metadata['labels']}")
print(f"ISRC: {metadata['isrc']}")

# Get platform statistics
stats = client.get_platform_stats(songstats_id="qmr6e0bx")
# Returns stats for all platforms: spotify, apple_music, youtube, etc.

# Get YouTube videos for a track
videos = client.get_youtube_videos(songstats_id="qmr6e0bx")
print(f"Most viewed: {videos['most_viewed']['ytb_id']}")
```

## YouTube Client

Direct YouTube Data API access (requires OAuth 2.0).

```python
from msc.clients.youtube import YouTubeClient

# Initialize (handles OAuth flow automatically)
client = YouTubeClient()

# Check remaining quota
quota = client.get_quota()
print(f"Remaining: {quota['remaining']}/{quota['daily_limit']}")

# Get video details (uses 1 quota unit per video)
video = client.get_video_details(video_id="dQw4w9WgXcQ")
print(f"Title: {video['title']}")
print(f"Views: {video['view_count']}")
print(f"Likes: {video['like_count']}")
print(f"Duration: {video['duration']}")

# Search for videos
results = client.search_videos(query="hardwell ultra 2024", max_results=5)
```

## Client Comparison

| Client    | Data Source | Auth      | Rate Limit | Quota   |
|-----------|-------------|-----------|------------|---------|
| MusicBee  | Local XML   | None      | N/A        | N/A     |
| Songstats | REST API    | API Key   | 10 req/s   | Monthly |
| YouTube   | REST API    | OAuth 2.0 | 10 req/s   | 10K/day |

> **Note:** YouTube data is typically fetched via Songstats API (quota-free). The YouTube client is available for deeper
> analysis (likes, comments, duration) when needed.
