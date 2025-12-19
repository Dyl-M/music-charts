"""Platform-specific statistics models.

This module provides Pydantic models for streaming platform statistics
from Spotify, Deezer, Apple Music, YouTube, TikTok, SoundCloud, Tidal,
Amazon Music, Beatport, and 1001Tracklists.

All fields use Optional types (int | None, float | None) to distinguish
between "data not available" (None) and "actually zero" (0), which is
critical for the scoring algorithm's data availability calculations.

Field aliases match the flat naming convention from legacy JSON files
(e.g., "spotify_streams_total") for backward compatibility.
"""

# Standard library
from typing import Annotated

# Third-party
from pydantic import ConfigDict, Field

# Local
from msc.models.base import MSCBaseModel


class SpotifyStats(MSCBaseModel):
    """Spotify streaming statistics.

    Includes streams, popularity, playlists, reach, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        streams_total: Total stream count (STREAMS category, weight=4).
        popularity_peak: Peak popularity score 0-100 (POPULARITY, weight=4).
        playlist_reach_total: Total playlist reach (REACH category, weight=2).
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = SpotifyStats(
        ...     streams_total=3805083,
        ...     popularity_peak=62,
        ...     playlist_reach_total=8493255
        ... )
        >>> stats.streams_total
        3805083
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # STREAMS (high weight=4)
    streams_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="spotify_streams_total",
            description="Total stream count"
        )
    ]

    # POPULARITY (high weight=4)
    popularity_peak: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            le=100,
            alias="spotify_popularity_peak",
            description="Peak popularity score (0-100)"
        )
    ]

    # REACH (low weight=2)
    playlist_reach_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="spotify_playlist_reach_total",
            description="Total playlist reach (listener count)"
        )
    ]

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="spotify_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="spotify_charts_total",
            description="Total chart appearances"
        )
    ]


class DeezerStats(MSCBaseModel):
    """Deezer streaming statistics.

    Includes popularity, reach, playlists, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        popularity_peak: Peak popularity score 0-100 (POPULARITY, weight=4).
        playlist_reach_total: Total playlist reach (REACH category, weight=2).
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = DeezerStats(
        ...     popularity_peak=80,
        ...     playlist_reach_total=650437
        ... )
        >>> stats.popularity_peak
        80
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # POPULARITY (high weight=4)
    popularity_peak: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            le=100,
            alias="deezer_popularity_peak",
            description="Peak popularity score (0-100)"
        )
    ]

    # REACH (low weight=2)
    playlist_reach_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="deezer_playlist_reach_total",
            description="Total playlist reach (listener count)"
        )
    ]

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="deezer_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="deezer_charts_total",
            description="Total chart appearances"
        )
    ]


class AppleMusicStats(MSCBaseModel):
    """Apple Music streaming statistics.

    Includes playlists and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = AppleMusicStats(
        ...     playlists_editorial_total=6,
        ...     charts_total=15
        ... )
        >>> stats.playlists_editorial_total
        6
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="apple_music_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="apple_music_charts_total",
            description="Total chart appearances"
        )
    ]


class YouTubeStats(MSCBaseModel):
    """YouTube streaming statistics.

    Includes video views, shorts views, engagement, playlists, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        video_views_total: Total video views (STREAMS category, weight=4).
        short_views_total: Total shorts views (SHORTS category, weight=1).
        engagement_rate_total: Engagement rate percentage (ENGAGEMENT, weight=1).
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = YouTubeStats(
        ...     video_views_total=527735,
        ...     short_views_total=2573,
        ...     engagement_rate_total=3.0
        ... )
        >>> stats.video_views_total
        527735
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # STREAMS (high weight=4)
    video_views_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="youtube_video_views_total",
            description="Total video views"
        )
    ]

    # SHORTS (negligible weight=1)
    short_views_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="youtube_short_views_total",
            description="Total shorts views"
        )
    ]

    # ENGAGEMENT (negligible weight=1)
    engagement_rate_total: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            alias="youtube_engagement_rate_total",
            description="Engagement rate percentage"
        )
    ]

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="youtube_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="youtube_charts_total",
            description="Total chart appearances"
        )
    ]


class TikTokStats(MSCBaseModel):
    """TikTok streaming statistics.

    Includes video views, engagement, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        views_total: Total video views (SHORTS category, weight=1).
        engagement_rate_total: Engagement rate percentage (ENGAGEMENT, weight=1).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = TikTokStats(
        ...     views_total=583273,
        ...     engagement_rate_total=5.7
        ... )
        >>> stats.views_total
        583273
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # SHORTS (negligible weight=1)
    views_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="tiktok_views_total",
            description="Total video views"
        )
    ]

    # ENGAGEMENT (negligible weight=1)
    engagement_rate_total: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            alias="tiktok_engagement_rate_total",
            description="Engagement rate percentage"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="tiktok_charts_total",
            description="Total chart appearances"
        )
    ]


class SoundCloudStats(MSCBaseModel):
    """SoundCloud streaming statistics.

    Includes streams, engagement, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        streams_total: Total stream count (STREAMS category, weight=4).
        engagement_rate_total: Engagement rate percentage (ENGAGEMENT, weight=1).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = SoundCloudStats(
        ...     streams_total=88503,
        ...     engagement_rate_total=3.0
        ... )
        >>> stats.streams_total
        88503
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # STREAMS (high weight=4)
    streams_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="soundcloud_streams_total",
            description="Total stream count"
        )
    ]

    # ENGAGEMENT (negligible weight=1)
    engagement_rate_total: Annotated[
        float | None,
        Field(
            default=None,
            ge=0.0,
            alias="soundcloud_engagement_rate_total",
            description="Engagement rate percentage"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="soundcloud_charts_total",
            description="Total chart appearances"
        )
    ]


class TidalStats(MSCBaseModel):
    """Tidal streaming statistics.

    Includes popularity, playlists, and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        popularity_peak: Peak popularity score 0-100 (POPULARITY, weight=4).
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = TidalStats(
        ...     popularity_peak=32,
        ...     playlists_editorial_total=0
        ... )
        >>> stats.popularity_peak
        32
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # POPULARITY (high weight=4)
    popularity_peak: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            le=100,
            alias="tidal_popularity_peak",
            description="Peak popularity score (0-100)"
        )
    ]

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="tidal_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="tidal_charts_total",
            description="Total chart appearances"
        )
    ]


class AmazonMusicStats(MSCBaseModel):
    """Amazon Music streaming statistics.

    Includes playlists and charts data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        playlists_editorial_total: Editorial playlist count (PLAYLISTS, weight=2).
        charts_total: Total chart appearances (CHARTS category, weight=1).

    Examples:
        >>> stats = AmazonMusicStats(
        ...     playlists_editorial_total=26,
        ...     charts_total=0
        ... )
        >>> stats.playlists_editorial_total
        26
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # PLAYLISTS (low weight=2)
    playlists_editorial_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="amazon_playlists_editorial_total",
            description="Editorial playlist appearances"
        )
    ]

    # CHARTS (negligible weight=1)
    charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="amazon_charts_total",
            description="Total chart appearances"
        )
    ]


class BeatportStats(MSCBaseModel):
    """Beatport statistics.

    Includes DJ chart support data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        dj_charts_total: DJ chart appearances (PROFESSIONAL_SUPPORT, weight=2).

    Examples:
        >>> stats = BeatportStats(dj_charts_total=35)
        >>> stats.dj_charts_total
        35
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # PROFESSIONAL_SUPPORT (low weight=2)
    dj_charts_total: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="beatport_dj_charts_total",
            description="DJ chart appearances"
        )
    ]


class TracklistsStats(MSCBaseModel):
    """1001Tracklists statistics.

    Includes unique DJ support data.
    All fields are optional to handle missing data gracefully.

    Attributes:
        unique_support: Unique DJ support count (PROFESSIONAL_SUPPORT, weight=2).

    Examples:
        >>> stats = TracklistsStats(unique_support=40)
        >>> stats.unique_support
        40
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # PROFESSIONAL_SUPPORT (low weight=2)
    unique_support: Annotated[
        int | None,
        Field(
            default=None,
            ge=0,
            alias="1001tracklists_unique_support",
            description="Unique DJ support count"
        )
    ]
