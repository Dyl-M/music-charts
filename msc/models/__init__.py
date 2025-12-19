"""Data models for music-charts pipeline.

This module provides Pydantic models for tracks, platform statistics,
YouTube videos, and power rankings. All models support JSON serialization
and backward compatibility with legacy data formats.
"""

# Base model
from msc.models.base import MSCBaseModel

# Track models
from msc.models.track import SongstatsIdentifiers, Track

# Platform statistics models
from msc.models.platforms import (
    AmazonMusicStats,
    AppleMusicStats,
    BeatportStats,
    DeezerStats,
    SoundCloudStats,
    SpotifyStats,
    TidalStats,
    TikTokStats,
    TracklistsStats,
    YouTubeStats,
)

# Stats container models
from msc.models.stats import PlatformStats, TrackWithStats

# YouTube models
from msc.models.youtube import YouTubeVideo, YouTubeVideoData

# Ranking models
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults

__all__ = [
    # Base
    "MSCBaseModel",
    # Track
    "Track",
    "SongstatsIdentifiers",
    # Platform stats
    "SpotifyStats",
    "DeezerStats",
    "AppleMusicStats",
    "YouTubeStats",
    "TikTokStats",
    "SoundCloudStats",
    "TidalStats",
    "AmazonMusicStats",
    "BeatportStats",
    "TracklistsStats",
    # Stats containers
    "PlatformStats",
    "TrackWithStats",
    # YouTube
    "YouTubeVideo",
    "YouTubeVideoData",
    # Rankings
    "CategoryScore",
    "PowerRanking",
    "PowerRankingResults",
]
