"""External API clients."""

# Standard library
from unittest.mock import MagicMock

# Local
from msc.clients.base import BaseClient
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.clients.youtube import YouTubeClient


def create_mock_songstats_client() -> MagicMock:
    """Create a mock SongstatsClient with predefined responses for test mode.

    Returns:
        MagicMock configured to behave like SongstatsClient with test data.
    """
    mock = MagicMock(spec=SongstatsClient)

    # Search track returns a valid result
    mock.search_track.return_value = [{
        "songstats_track_id": "test_track_123",
        "title": "Test Track",
        "artists": [{"name": "Test Artist"}],
        "isrc": "TEST00000001",
    }]

    # Track info with links
    mock.get_track_info.return_value = {
        "title": "Test Track",
        "artists": [{"name": "Test Artist"}],
        "links": [
            {"source": "spotify", "url": "https://open.spotify.com/track/test"},
            {"source": "apple_music", "url": "https://music.apple.com/track/test"},
        ],
    }

    # Available platforms
    mock.get_available_platforms.return_value = {"spotify", "apple_music", "youtube"}

    # Platform stats with realistic test data
    mock.get_platform_stats.return_value = {
        "spotify": {
            "streams_total": 1_000_000,
            "streams_current": 50_000,
            "popularity": 75,
            "listeners_monthly": 100_000,
            "playlist_count": 150,
            "playlist_reach": 500_000,
        },
        "apple_music": {
            "streams_total": 500_000,
            "streams_current": 25_000,
        },
    }

    # Historical peaks
    mock.get_historical_peaks.return_value = {
        "spotify": {"peak_position": 15, "peak_date": "2024-06-01"},
        "apple_music": {"peak_position": 25, "peak_date": "2024-05-15"},
    }

    # YouTube videos
    mock.get_youtube_videos.return_value = {
        "most_viewed": {
            "video_id": "test_video_123",
            "title": "Test Track (Official Video)",
            "views": 5_000_000,
            "likes": 100_000,
        },
        "all_sources": [
            {"video_id": "test_video_123", "views": 5_000_000},
            {"video_id": "test_video_456", "views": 1_000_000},
        ],
    }

    # Close method
    mock.close.return_value = None

    return mock


__all__ = [
    "BaseClient",
    "MusicBeeClient",
    "SongstatsClient",
    "YouTubeClient",
    "create_mock_songstats_client",
]
