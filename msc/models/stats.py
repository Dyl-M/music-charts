"""Platform statistics container and combined track models.

This module provides the PlatformStats container that aggregates all
platform-specific statistics, and the TrackWithStats model that combines
track metadata with platform statistics.
"""

# Standard library
from typing import Annotated, Any, Self

# Third-party
from pydantic import ConfigDict, Field

# Local
from msc.models.base import MSCBaseModel
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
from msc.models.track import SongstatsIdentifiers, Track


class PlatformStats(MSCBaseModel):
    """Container for all platform-specific statistics.

    Aggregates statistics from all 10 supported streaming platforms
    into a single model. Each platform's stats are represented by their
    own dedicated model (SpotifyStats, DeezerStats, etc.).

    All platform fields default to empty instances (all values None)
    to handle missing platform data gracefully.

    Attributes:
        spotify: Spotify streaming statistics.
        deezer: Deezer streaming statistics.
        apple_music: Apple Music streaming statistics.
        youtube: YouTube streaming statistics.
        tiktok: TikTok streaming statistics.
        soundcloud: SoundCloud streaming statistics.
        tidal: Tidal streaming statistics.
        amazon_music: Amazon Music streaming statistics.
        beatport: Beatport statistics.
        tracklists: 1001Tracklists statistics.

    Examples:
        >>> stats = PlatformStats(
        ...     spotify=SpotifyStats(streams_total=1000000),
        ...     deezer=DeezerStats(popularity_peak=80)
        ... )
        >>> stats.spotify.streams_total
        1000000
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    spotify: Annotated[
        SpotifyStats,
        Field(
            default_factory=SpotifyStats,
            description="Spotify statistics"
        )
    ]
    deezer: Annotated[
        DeezerStats,
        Field(
            default_factory=DeezerStats,
            description="Deezer statistics"
        )
    ]
    apple_music: Annotated[
        AppleMusicStats,
        Field(
            default_factory=AppleMusicStats,
            description="Apple Music statistics"
        )
    ]
    youtube: Annotated[
        YouTubeStats,
        Field(
            default_factory=YouTubeStats,
            description="YouTube statistics"
        )
    ]
    tiktok: Annotated[
        TikTokStats,
        Field(
            default_factory=TikTokStats,
            description="TikTok statistics"
        )
    ]
    soundcloud: Annotated[
        SoundCloudStats,
        Field(
            default_factory=SoundCloudStats,
            description="SoundCloud statistics"
        )
    ]
    tidal: Annotated[
        TidalStats,
        Field(
            default_factory=TidalStats,
            description="Tidal statistics"
        )
    ]
    amazon_music: Annotated[
        AmazonMusicStats,
        Field(
            default_factory=AmazonMusicStats,
            description="Amazon Music statistics"
        )
    ]
    beatport: Annotated[
        BeatportStats,
        Field(
            default_factory=BeatportStats,
            description="Beatport statistics"
        )
    ]
    tracklists: Annotated[
        TracklistsStats,
        Field(
            default_factory=TracklistsStats,
            description="1001Tracklists statistics"
        )
    ]

    @classmethod
    def from_flat_dict(cls, data: dict[str, Any]) -> Self:
        """Load from legacy flat dictionary format.

        Takes a flat dictionary with platform-prefixed keys
        (e.g., "spotify_streams_total") and groups them by platform
        to create nested platform statistics models.

        Args:
            data: Flat dictionary with platform-prefixed keys.

        Returns:
            PlatformStats instance with nested platform models.

        Examples:
            >>> flat_data = {
            ...     "spotify_streams_total": 1000000,
            ...     "deezer_popularity_peak": 80
            ... }
            >>> stats = PlatformStats.from_flat_dict(flat_data)
            >>> stats.spotify.streams_total
            1000000
        """
        # Group fields by platform prefix
        spotify_data = {k: v for k, v in data.items() if k.startswith("spotify_")}
        deezer_data = {k: v for k, v in data.items() if k.startswith("deezer_")}
        apple_music_data = {k: v for k, v in data.items() if k.startswith("apple_music_")}
        youtube_data = {k: v for k, v in data.items() if k.startswith("youtube_")}
        tiktok_data = {k: v for k, v in data.items() if k.startswith("tiktok_")}
        soundcloud_data = {k: v for k, v in data.items() if k.startswith("soundcloud_")}
        tidal_data = {k: v for k, v in data.items() if k.startswith("tidal_")}
        amazon_data = {k: v for k, v in data.items() if k.startswith("amazon_")}
        beatport_data = {k: v for k, v in data.items() if k.startswith("beatport_")}
        tracklists_data = {k: v for k, v in data.items() if k.startswith("1001tracklists_")}

        # Create platform models using aliases (populate_by_name=True handles this)
        return cls(
            spotify=SpotifyStats(**spotify_data) if spotify_data else SpotifyStats(),
            deezer=DeezerStats(**deezer_data) if deezer_data else DeezerStats(),
            apple_music=AppleMusicStats(**apple_music_data) if apple_music_data else AppleMusicStats(),
            youtube=YouTubeStats(**youtube_data) if youtube_data else YouTubeStats(),
            tiktok=TikTokStats(**tiktok_data) if tiktok_data else TikTokStats(),
            soundcloud=SoundCloudStats(**soundcloud_data) if soundcloud_data else SoundCloudStats(),
            tidal=TidalStats(**tidal_data) if tidal_data else TidalStats(),
            amazon_music=AmazonMusicStats(**amazon_data) if amazon_data else AmazonMusicStats(),
            beatport=BeatportStats(**beatport_data) if beatport_data else BeatportStats(),
            tracklists=TracklistsStats(**tracklists_data) if tracklists_data else TracklistsStats(),
        )

    def to_flat_dict(self) -> dict[str, Any]:
        """Convert to legacy flat dictionary format.

        Flattens nested platform statistics into a single dictionary
        with platform-prefixed keys (e.g., "spotify_streams_total").
        Excludes None values to match legacy behavior.

        Returns:
            Flat dictionary with platform-prefixed keys.

        Examples:
            >>> stats = PlatformStats(
            ...     spotify=SpotifyStats(streams_total=1000000)
            ... )
            >>> flat = stats.to_flat_dict()
            >>> flat["spotify_streams_total"]
            1000000
        """
        # Collect all platform stats using aliases
        result = {}

        # Each platform model's to_flat_dict() uses aliases
        result.update(self.spotify.to_flat_dict())
        result.update(self.deezer.to_flat_dict())
        result.update(self.apple_music.to_flat_dict())
        result.update(self.youtube.to_flat_dict())
        result.update(self.tiktok.to_flat_dict())
        result.update(self.soundcloud.to_flat_dict())
        result.update(self.tidal.to_flat_dict())
        result.update(self.amazon_music.to_flat_dict())
        result.update(self.beatport.to_flat_dict())
        result.update(self.tracklists.to_flat_dict())

        return result


class TrackWithStats(MSCBaseModel):
    """Track metadata combined with platform statistics.

    Combines track metadata (title, artists, year), Songstats identifiers,
    and comprehensive platform statistics into a single model. This is the
    primary data structure for enriched tracks in the pipeline.

    Attributes:
        track: Track metadata (title, artists, year, etc.).
        songstats_identifiers: Songstats track identifiers (s_id, s_title).
        platform_stats: All platform statistics.

    Examples:
        >>> track_with_stats = TrackWithStats(
        ...     track=Track(
        ...         title="16",
        ...         artist_list=["blasterjaxx", "hardwell", "maddix"],
        ...         year=2024
        ...     ),
        ...     songstats_identifiers=SongstatsIdentifiers(
        ...         songstats_id="qmr6e0bx",
        ...         songstats_title="16"
        ...     ),
        ...     platform_stats=PlatformStats(
        ...         spotify=SpotifyStats(streams_total=3805083)
        ...     )
        ... )
        >>> track_with_stats.track.title
        '16'
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    track: Annotated[
        Track,
        Field(description="Track metadata")
    ]
    songstats_identifiers: Annotated[
        SongstatsIdentifiers,
        Field(description="Songstats track identifiers")
    ]
    platform_stats: Annotated[
        PlatformStats,
        Field(
            default_factory=PlatformStats,
            description="Platform statistics"
        )
    ]

    @classmethod
    def from_legacy_json(cls, data: dict[str, Any]) -> Self:
        """Load from legacy data_2024.json format.

        Converts legacy JSON structure to TrackWithStats model:
        - Top-level fields: title, artist_list, year, genre, label, request
        - "songstats_identifiers" nested dict with s_id, s_title
        - "data" nested dict with flat platform-prefixed stats

        Args:
            data: Legacy JSON item from data_2024.json.

        Returns:
            TrackWithStats instance.

        Examples:
            >>> legacy_item = {
            ...     "title": "16",
            ...     "artist_list": ["blasterjaxx", "hardwell", "maddix"],
            ...     "year": 2024,
            ...     "genre": ["hard techno"],
            ...     "label": ["revealed"],
            ...     "request": "blasterjaxx, hardwell, maddix 16",
            ...     "songstats_identifiers": {
            ...         "s_id": "qmr6e0bx",
            ...         "s_title": "16"
            ...     },
            ...     "data": {
            ...         "spotify_streams_total": 3805083,
            ...         "deezer_popularity_peak": 80
            ...     }
            ... }
            >>> track = TrackWithStats.from_legacy_json(legacy_item)
            >>> track.track.title
            '16'
        """
        # Extract track fields (top-level)
        track_data = {
            "title": data["title"],
            "artist_list": data["artist_list"],
            "year": data.get("year"),
            "genre": data.get("genre", []),
            "label": data.get("label", []),
            "grouping": data.get("grouping"),
            "search_query": data.get("request"),  # Legacy uses "request" key
        }

        # Extract Songstats identifiers
        identifiers_data = data.get("songstats_identifiers", {})

        # Extract platform stats from "data" field
        stats_data = data.get("data", {})

        return cls(
            track=Track(**track_data),
            songstats_identifiers=SongstatsIdentifiers(**identifiers_data),
            platform_stats=PlatformStats.from_flat_dict(stats_data),
        )
