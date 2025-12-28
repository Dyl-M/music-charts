"""Platform statistics container and combined track models.

This module provides the PlatformStats container that aggregates all
platform-specific statistics, and the TrackWithStats model that combines
track metadata with platform statistics.
"""

# Standard library
from typing import Annotated, Any, Self

# Third-party
from pydantic import ConfigDict, Field, computed_field

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
from msc.models.youtube import YouTubeVideoData


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

    @staticmethod
    def _group_by_platform(data: dict[str, Any], prefix: str) -> dict[str, Any]:
        """Extract fields for a specific platform by prefix.

        Args:
            data: Flat dictionary with platform-prefixed keys.
            prefix: Platform prefix to filter (e.g., "spotify_").

        Returns:
            Dictionary with fields matching the prefix.
        """
        return {k: v for k, v in data.items() if k.startswith(prefix)}

    @classmethod
    def from_flat_dict(
            cls,
            data: dict[str, Any],
            available_platforms: set[str] | None = None
    ) -> Self:
        """Load from legacy flat dictionary format.

        Takes a flat dictionary with platform-prefixed keys
        (e.g., "spotify_streams_total") and groups them by platform
        to create nested platform statistics models.

        Args:
            data: Flat dictionary with platform-prefixed keys.
            available_platforms: Optional set of platform names where track exists.
                If provided, only creates platform instances for these platforms.
                Platforms not in this set will use default_factory (all None values).

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

            >>> # With platform filtering
            >>> stats = PlatformStats.from_flat_dict(
            ...     flat_data,
            ...     available_platforms={"spotify"}
            ... )
            >>> stats.spotify.streams_total  # Has data
            1000000
            >>> stats.deezer.popularity_peak  # Not available, uses default
            None
        """
        # Define platform configurations
        platforms = [
            ("spotify", "spotify_", SpotifyStats),
            ("deezer", "deezer_", DeezerStats),
            ("apple_music", "apple_music_", AppleMusicStats),
            ("youtube", "youtube_", YouTubeStats),
            ("tiktok", "tiktok_", TikTokStats),
            ("soundcloud", "soundcloud_", SoundCloudStats),
            ("tidal", "tidal_", TidalStats),
            ("amazon_music", "amazon_", AmazonMusicStats),
            ("beatport", "beatport_", BeatportStats),
            ("tracklists", "1001tracklists_", TracklistsStats),
        ]

        # Group and create platform models
        platform_kwargs = {}
        for field_name, prefix, model_class in platforms:
            platform_data = cls._group_by_platform(data, prefix)

            # Only create platform instance if platform is available (track exists there)
            # If available_platforms is None, create for all platforms with data (backward compat)
            if available_platforms is None:
                # Legacy behavior: create if has any data
                has_data = any(value is not None for value in platform_data.values())
                if has_data:
                    platform_kwargs[field_name] = model_class(**platform_data)

            else:
                # New behavior: only create if platform is in available list
                # This correctly distinguishes "not on platform" (None) from "on platform with 0 stats" (0)

                # Normalize model field names to match available_platforms set
                field_to_source = {
                    "tracklists": "1001tracklists",
                }

                normalized_name = field_to_source.get(field_name, field_name)
                if normalized_name in available_platforms:
                    platform_kwargs[field_name] = model_class(**platform_data)

        return cls(**platform_kwargs)

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
        youtube_data: Optional YouTube video data (aggregated from Songstats API).

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
    youtube_data: Annotated[
        YouTubeVideoData | None,
        Field(
            default=None,
            description="YouTube video data aggregated from Songstats API"
        )
    ]

    @computed_field(alias="track_id")  # Serialize as "track_id"
    @property
    def identifier(self) -> str:
        """Unique identifier for this track.

        Delegates to the nested track's identifier for consistency.
        Used as the unique key for storage and retrieval.

        Returns:
            8-character hexadecimal identifier (e.g., "a1b2c3d4")

        Examples:
            >>> track_with_stats = TrackWithStats(
            ...     track=Track(
            ...         title="16",
            ...         artist_list=["blasterjaxx"],
            ...         year=2024
            ...     ),
            ...     songstats_identifiers=SongstatsIdentifiers(
            ...         songstats_id="qmr6e0bx",
            ...         songstats_title="16"
            ...     )
            ... )
            >>> track_with_stats.identifier
            'a1b2c3d4'
        """
        return self.track.identifier

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
        # Legacy format uses "label" key, Track model uses "grouping"
        track_data = {
            "title": data["title"],
            "artist_list": data["artist_list"],
            "year": data.get("year"),
            "genre": data.get("genre", []),
            "grouping": data.get("label", []) or data.get("grouping", []),
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

    @classmethod
    def from_flat_dict(cls, data: dict[str, Any]) -> Self:
        """Load from fully flat dictionary format.

        Converts a completely flat structure where track, identifier, and
        platform stats fields are all at the top level.

        Args:
            data: Flat dictionary with all fields at top level.

        Returns:
            TrackWithStats instance.

        Examples:
            >>> flat_data = {
            ...     "title": "16",
            ...     "artist_list": ["Test Artist"],
            ...     "year": 2024,
            ...     "songstats_id": "qmr6e0bx",
            ...     "songstats_title": "16",
            ...     "spotify_streams_total": 3805083,
            ... }
            >>> track = TrackWithStats.from_flat_dict(flat_data)
            >>> track.track.title
            '16'
        """
        # Extract track fields
        track_data = {
            "title": data.get("title"),
            "artist_list": data.get("artist_list", []),
            "year": data.get("year"),
            "genre": data.get("genre", []),
            "grouping": data.get("label", []) or data.get("grouping", []),
            "search_query": data.get("search_query") or data.get("request"),
        }

        # Extract identifier fields
        identifiers_data = {
            "songstats_id": data.get("songstats_id"),
            "songstats_title": data.get("songstats_title"),
            "isrc": data.get("isrc"),
            "spotify_id": data.get("spotify_id"),
        }

        # Extract platform stats (all fields with platform prefixes)
        # PlatformStats.from_flat_dict will handle extracting these
        return cls(
            track=Track(**track_data),
            songstats_identifiers=SongstatsIdentifiers(**identifiers_data),
            platform_stats=PlatformStats.from_flat_dict(data),
        )

    def to_flat_dict(self) -> dict[str, Any]:
        """Convert to fully flat dictionary format for CSV export.

        Flattens nested track, identifier, and platform stats into a single
        dictionary with only scalar values at the top level. Lists and nested
        dicts are excluded for clean CSV output.

        Returns:
            Flat dictionary with scalar fields only.

        Examples:
            >>> track_with_stats = TrackWithStats(
            ...     track=Track(
            ...         title="16",
            ...         artist_list=["blasterjaxx"],
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
            >>> flat = track_with_stats.to_flat_dict()
            >>> flat["track_id"]
            '3e4f5a6b'
            >>> flat["songstats_id"]
            'qmr6e0bx'
            >>> flat["spotify_streams_total"]
            3805083
        """
        result: dict[str, Any] = {"track_id": self.track.identifier,
                                  "songstats_id": self.songstats_identifiers.songstats_id}

        # Flatten platform stats (uses aliases and excludes None values)
        platform_dict = self.platform_stats.to_flat_dict()
        result.update(platform_dict)
        return result
