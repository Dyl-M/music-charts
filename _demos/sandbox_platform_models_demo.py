"""Interactive demo for platform statistics models.

This script demonstrates all 10 platform statistics models (SpotifyStats,
DeezerStats, AppleMusicStats, YouTubeStats, TikTokStats, SoundCloudStats,
TidalStats, AmazonMusicStats, BeatportStats, TracklistsStats).

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples and demonstrates validation

Usage:
    python _demos/sandbox_platform_models_demo.py
"""

# Standard library
import json

# Third-party
from pydantic import ValidationError

# Local
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


def print_separator(title: str = "") -> None:
    """Print a formatted separator line.

    Args:
        title: Optional title to display in separator.
    """
    if title:
        print(f"\n{'=' * 80}")
        print(f" {title}")
        print(f"{'=' * 80}\n")
    else:
        print(f"{'=' * 80}\n")


def demo_spotify_comprehensive() -> None:
    """Demonstrate SpotifyStats comprehensively."""
    print_separator("SpotifyStats - Comprehensive Demo")

    # Full stats with all fields
    print("Creating comprehensive SpotifyStats...")
    stats = SpotifyStats(
        streams_total=3805083,
        popularity_peak=62,
        playlist_reach_total=8493255,
        playlists_editorial_total=6,
        charts_total=0
    )

    print(f"✓ Streams (high weight=4): {stats.streams_total:,}")
    print(f"  Popularity (high weight=4): {stats.popularity_peak}/100")
    print(f"  Playlist Reach (low weight=2): {stats.playlist_reach_total:,}")
    print(f"  Editorial Playlists (low weight=2): {stats.playlists_editorial_total}")
    print(f"  Charts (negligible weight=1): {stats.charts_total}\n")

    # Using aliases (legacy format)
    print("Creating with aliases (legacy flat format)...")
    stats_aliased = SpotifyStats(
        spotify_streams_total=1000000,
        spotify_popularity_peak=75
    )
    print(f"✓ streams_total: {stats_aliased.streams_total:,}")
    print(f"  popularity_peak: {stats_aliased.popularity_peak}\n")

    # None vs zero distinction
    print("Demonstrating None vs zero distinction...")
    stats_none = SpotifyStats(streams_total=None)
    stats_zero = SpotifyStats(streams_total=0)
    print(f"  streams_total=None: {stats_none.streams_total} (data not available)")
    print(f"  streams_total=0: {stats_zero.streams_total} (actually zero)")
    print("  This distinction is critical for data availability calculations\n")

    # Validation examples
    print("Testing validation...")
    try:
        SpotifyStats(popularity_peak=101)  # Invalid: > 100
    except ValidationError:
        print("✗ popularity_peak=101 rejected (must be 0-100)")

    try:
        SpotifyStats(streams_total=-1000)  # Invalid: negative
    except ValidationError:
        print("✗ streams_total=-1000 rejected (must be >= 0)")

    print("\n✓ SpotifyStats working correctly\n")


def demo_all_platforms_overview() -> None:
    """Demonstrate all other platform models."""
    print_separator("All Platform Models Overview")

    # DeezerStats
    print("1. DeezerStats:")
    deezer = DeezerStats(
        popularity_peak=80,
        playlist_reach_total=650437
    )
    print(f"   ✓ Popularity: {deezer.popularity_peak}, Reach: {deezer.playlist_reach_total:,}\n")

    # AppleMusicStats
    print("2. AppleMusicStats:")
    apple = AppleMusicStats(
        playlists_editorial_total=6,
        charts_total=15
    )
    print(f"   ✓ Editorial playlists: {apple.playlists_editorial_total}, Charts: {apple.charts_total}\n")

    # YouTubeStats
    print("3. YouTubeStats:")
    youtube = YouTubeStats(
        video_views_total=527735,
        short_views_total=2573,
        engagement_rate_total=3.0
    )
    print(f"   ✓ Video views: {youtube.video_views_total:,}, Shorts: {youtube.short_views_total:,}")
    print(f"     Engagement: {youtube.engagement_rate_total}%\n")

    # TikTokStats
    print("4. TikTokStats:")
    tiktok = TikTokStats(
        views_total=583273,
        engagement_rate_total=5.7
    )
    print(f"   ✓ Views: {tiktok.views_total:,}, Engagement: {tiktok.engagement_rate_total}%\n")

    # SoundCloudStats
    print("5. SoundCloudStats:")
    soundcloud = SoundCloudStats(
        streams_total=88503,
        engagement_rate_total=3.0
    )
    print(f"   ✓ Streams: {soundcloud.streams_total:,}, Engagement: {soundcloud.engagement_rate_total}%\n")

    # TidalStats
    print("6. TidalStats:")
    tidal = TidalStats(
        popularity_peak=32,
        playlists_editorial_total=0
    )
    print(f"   ✓ Popularity: {tidal.popularity_peak}, Editorial playlists: {tidal.playlists_editorial_total}\n")

    # AmazonMusicStats
    print("7. AmazonMusicStats:")
    amazon = AmazonMusicStats(
        playlists_editorial_total=26,
        charts_total=0
    )
    print(f"   ✓ Editorial playlists: {amazon.playlists_editorial_total}, Charts: {amazon.charts_total}\n")

    # BeatportStats
    print("8. BeatportStats:")
    beatport = BeatportStats(dj_charts_total=35)
    print(f"   ✓ DJ charts (professional support): {beatport.dj_charts_total}\n")

    # TracklistsStats
    print("9. TracklistsStats (1001Tracklists):")
    tracklists = TracklistsStats(unique_support=40)
    print(f"   ✓ Unique DJ support (professional support): {tracklists.unique_support}\n")

    print("✓ All 10 platform models demonstrated\n")


def demo_field_aliases() -> None:
    """Demonstrate field alias usage."""
    print_separator("Field Aliases for Backward Compatibility")

    print("Legacy format uses flat naming with platform prefixes:")
    print("  spotify_streams_total, deezer_popularity_peak, etc.\n")

    # Loading from dict with aliases
    print("Loading SpotifyStats from flat dict (legacy format)...")
    flat_data = {
        "spotify_streams_total": 1500000,
        "spotify_popularity_peak": 85,
        "spotify_playlist_reach_total": 5000000
    }
    stats = SpotifyStats(**flat_data)
    print(f"✓ Loaded successfully!")
    print(f"  streams_total: {stats.streams_total:,}")
    print(f"  popularity_peak: {stats.popularity_peak}")
    print(f"  playlist_reach_total: {stats.playlist_reach_total:,}\n")

    # Exporting with aliases
    print("Exporting with aliases (model_dump(by_alias=True))...")
    exported = stats.model_dump(by_alias=True, exclude_none=True)
    print(f"✓ Exported keys: {list(exported.keys())}")
    print(f"  (Uses prefixed names for backward compatibility)\n")

    print("✓ Field aliases working correctly\n")


def demo_validation_examples() -> None:
    """Demonstrate validation rules."""
    print_separator("Validation Examples")

    # Popularity range validation (0-100)
    print("Testing popularity range validation (0-100)...")
    valid_min = SpotifyStats(popularity_peak=0)
    valid_max = SpotifyStats(popularity_peak=100)
    print(f"✓ popularity_peak=0: {valid_min.popularity_peak}")
    print(f"✓ popularity_peak=100: {valid_max.popularity_peak}")

    try:
        SpotifyStats(popularity_peak=150)
    except ValidationError:
        print("✗ popularity_peak=150 rejected (exceeds maximum)\n")

    # Negative values rejected
    print("Testing negative value rejection...")
    try:
        DeezerStats(playlist_reach_total=-5000)
    except ValidationError:
        print("✗ playlist_reach_total=-5000 rejected (must be >= 0)\n")

    # Float vs int fields
    print("Testing float vs int field types...")
    youtube_stats = YouTubeStats(
        video_views_total=100000,  # int
        engagement_rate_total=5.7  # float
    )
    print(f"✓ video_views_total (int): {youtube_stats.video_views_total}")
    print(f"✓ engagement_rate_total (float): {youtube_stats.engagement_rate_total}\n")

    print("✓ All validation rules enforced correctly\n")


def demo_json_serialization() -> None:
    """Demonstrate JSON serialization with aliases."""
    print_separator("JSON Serialization with Aliases")

    stats = SpotifyStats(
        streams_total=2000000,
        popularity_peak=70
    )

    # Standard serialization (field names)
    print("Standard serialization (field names)...")
    standard_json = stats.model_dump_json()
    print(json.loads(standard_json))
    print()

    # Serialization with aliases (legacy format)
    print("Serialization with aliases (by_alias=True)...")
    aliased_dict = stats.model_dump(by_alias=True, exclude_none=True)
    print(json.dumps(aliased_dict, indent=2))
    print()

    # Loading from aliased JSON
    print("Loading from aliased JSON...")
    json_str = '{"spotify_streams_total": 3000000, "spotify_popularity_peak": 90}'
    loaded_stats = SpotifyStats.model_validate_json(json_str)
    print(f"✓ Loaded: streams={loaded_stats.streams_total:,}, popularity={loaded_stats.popularity_peak}\n")

    print("✓ JSON serialization with aliases working correctly\n")


def demo_empty_vs_populated() -> None:
    """Demonstrate empty vs populated stats."""
    print_separator("Empty vs Populated Stats")

    # Empty stats (all None)
    print("Empty stats (all fields default to None)...")
    empty = SpotifyStats()
    print(f"  streams_total: {empty.streams_total}")
    print(f"  popularity_peak: {empty.popularity_peak}")
    print(f"  (All fields are None by default)\n")

    # Partially populated
    print("Partially populated stats...")
    partial = SpotifyStats(streams_total=500000)
    print(f"  streams_total: {partial.streams_total:,}")
    print(f"  popularity_peak: {partial.popularity_peak} (still None)")
    print()

    # Checking for data availability
    print("Checking data availability...")
    populated = SpotifyStats(
        streams_total=1000000,
        popularity_peak=75
    )
    data_dict = populated.model_dump(exclude_none=True)
    print(f"  Non-None fields: {list(data_dict.keys())}")
    print(f"  Data availability: {len(data_dict)}/5 fields populated\n")

    print("✓ Empty vs populated stats handled correctly\n")


def main() -> None:
    """Run all platform model demos."""
    print("=" * 80)
    print(" Platform Statistics Models - Interactive Demo")
    print("=" * 80)

    demo_spotify_comprehensive()
    demo_all_platforms_overview()
    demo_field_aliases()
    demo_validation_examples()
    demo_json_serialization()
    demo_empty_vs_populated()

    print_separator()
    print("✓ All demos completed successfully!")
    print()


if __name__ == "__main__":
    main()
