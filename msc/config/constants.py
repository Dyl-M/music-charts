"""Static constants and enumerations for the Music Charts pipeline."""

# Third-party
from enum import Enum


class Platform(str, Enum):
    """Streaming platforms supported by the pipeline."""

    SPOTIFY = "spotify"
    APPLE_MUSIC = "appleMusic"
    YOUTUBE = "youtube"
    DEEZER = "deezer"
    TIKTOK = "tiktok"
    BEATPORT = "beatport"
    TIDAL = "tidal"
    SOUNDCLOUD = "soundcloud"
    AMAZON = "amazonMusic"
    TRACKLISTS = "1001tracklists"

    @classmethod
    def songstats_sources(cls) -> tuple[str, ...]:
        """Return platform names as used in Songstats API."""
        return (
            "spotify",
            "apple_music",
            "amazon",
            "deezer",
            "tiktok",
            "youtube",
            "tracklist",
            "beatport",
            "tidal",
            "soundcloud",
        )


class StatCategory(str, Enum):
    """Categories of statistics for power ranking calculation."""

    CHARTS = "charts"
    ENGAGEMENT = "engagement"
    PLAYLISTS = "playlists"
    POPULARITY = "popularity"
    PROFESSIONAL = "professional_support"
    REACH = "reach"
    SHORTS = "shorts"
    STREAMS = "streams"


class WeightLevel(int, Enum):
    """Weight multiplier levels for power ranking."""

    NEGLIGIBLE = 1  # No boost
    LOW = 2  # 2x weight
    HIGH = 4  # 4x weight


# Category weight assignments
CATEGORY_WEIGHTS: dict[StatCategory, int] = {
    # Negligible importance
    StatCategory.CHARTS: WeightLevel.NEGLIGIBLE,
    StatCategory.ENGAGEMENT: WeightLevel.NEGLIGIBLE,
    StatCategory.SHORTS: WeightLevel.NEGLIGIBLE,
    # Low importance
    StatCategory.REACH: WeightLevel.LOW,
    StatCategory.PLAYLISTS: WeightLevel.LOW,
    StatCategory.PROFESSIONAL: WeightLevel.LOW,
    # High importance
    StatCategory.POPULARITY: WeightLevel.HIGH,
    StatCategory.STREAMS: WeightLevel.HIGH,
}

# Title formatting patterns for API search
TITLE_PATTERNS_TO_REMOVE: tuple[str, ...] = (
    "[Extended Mix]",
    "[Original Mix]",
    "[Remix]",
    "[Extended Version]",
    "[Club Edit]",
    "[",
    "]",
    "?",
    "(",
    ")",
)

TITLE_PATTERNS_TO_SPACE: tuple[str, ...] = (
    " × ",
    ", ",
)

# API endpoints
SONGSTATS_BASE_URL = "https://api.songstats.com/enterprise/v1"
SONGSTATS_ENDPOINTS = {
    "status": f"{SONGSTATS_BASE_URL}/status",
    "search": f"{SONGSTATS_BASE_URL}/tracks/search",
    "stats": f"{SONGSTATS_BASE_URL}/tracks/stats",
    "historic": f"{SONGSTATS_BASE_URL}/tracks/historic_stats",
    "info": f"{SONGSTATS_BASE_URL}/tracks/info",
}

# Default headers for API requests
DEFAULT_HEADERS = {
    "Accept-Encoding": "",
    "Accept": "application/json",
}
