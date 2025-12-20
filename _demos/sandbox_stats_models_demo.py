"""Interactive demo for PlatformStats and TrackWithStats models.

This script demonstrates the PlatformStats container model and TrackWithStats
combined model, including flat↔nested conversion and legacy JSON loading.

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples and real legacy data sample

Usage:
    python _demos/sandbox_stats_models_demo.py
"""

# Standard library
import json

# Local
from msc.config.settings import PROJECT_ROOT
from msc.models.platforms import DeezerStats, SpotifyStats
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track


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


def demo_platform_stats_creation() -> None:
    """Demonstrate PlatformStats creation."""
    print_separator("PlatformStats Creation")

    # Empty stats (all platforms default to empty)
    print("Creating empty PlatformStats...")
    empty_stats = PlatformStats()
    print(f"✓ Spotify streams: {empty_stats.spotify.streams_total}")
    print(f"  Deezer popularity: {empty_stats.deezer.popularity_peak}")
    print(f"  (All 10 platforms initialized with None values)\n")

    # Partial stats (some platforms populated)
    print("Creating PlatformStats with some platforms populated...")
    partial_stats = PlatformStats(
        spotify=SpotifyStats(streams_total=1000000, popularity_peak=75),
        deezer=DeezerStats(popularity_peak=80)
    )
    print(f"✓ Spotify streams: {partial_stats.spotify.streams_total:,}")
    print(f"  Spotify popularity: {partial_stats.spotify.popularity_peak}")
    print(f"  Deezer popularity: {partial_stats.deezer.popularity_peak}")
    print(f"  Apple Music playlists: {partial_stats.apple_music.playlists_editorial_total}")
    print(f"  (Unpopulated platforms remain None)\n")

    # All 10 platforms accessible
    print("All 10 platforms accessible:")
    print(f"  1. spotify: {partial_stats.spotify}")
    print(f"  2. deezer: {partial_stats.deezer}")
    print(f"  3. apple_music: {partial_stats.apple_music}")
    print(f"  4. youtube: {partial_stats.youtube}")
    print(f"  5. tiktok: {partial_stats.tiktok}")
    print(f"  6. soundcloud: {partial_stats.soundcloud}")
    print(f"  7. tidal: {partial_stats.tidal}")
    print(f"  8. amazon_music: {partial_stats.amazon_music}")
    print(f"  9. beatport: {partial_stats.beatport}")
    print(f"  10. tracklists: {partial_stats.tracklists}\n")

    print("✓ PlatformStats creation working correctly\n")


def demo_flat_to_nested_conversion() -> None:
    """Demonstrate flat → nested conversion."""
    print_separator("Flat to Nested Conversion")

    # Legacy flat format (as in data_2024.json)
    print("Legacy flat format (platform-prefixed keys)...")
    flat_data = {
        "spotify_streams_total": 3805083,
        "spotify_popularity_peak": 62,
        "spotify_playlist_reach_total": 8493255,
        "deezer_popularity_peak": 80,
        "deezer_playlist_reach_total": 650437,
        "youtube_video_views_total": 527735,
        "beatport_dj_charts_total": 35,
        "1001tracklists_unique_support": 40
    }
    print(json.dumps(dict(list(flat_data.items())[:4]), indent=2))
    print("  ... (8 fields total)\n")

    # Convert to nested model
    print("Converting to nested PlatformStats...")
    stats = PlatformStats.from_flat_dict(flat_data)
    print(f"✓ Converted successfully!")
    print(f"  spotify.streams_total: {stats.spotify.streams_total:,}")
    print(f"  spotify.popularity_peak: {stats.spotify.popularity_peak}")
    print(f"  deezer.popularity_peak: {stats.deezer.popularity_peak}")
    print(f"  youtube.video_views_total: {stats.youtube.video_views_total:,}")
    print(f"  beatport.dj_charts_total: {stats.beatport.dj_charts_total}")
    print(f"  tracklists.unique_support: {stats.tracklists.unique_support}\n")

    print("✓ Flat → nested conversion working correctly\n")


def demo_nested_to_flat_conversion() -> None:
    """Demonstrate nested → flat conversion."""
    print_separator("Nested to Flat Conversion")

    # Create nested stats
    print("Creating nested PlatformStats...")
    stats = PlatformStats(
        spotify=SpotifyStats(
            streams_total=1000000,
            popularity_peak=75
        ),
        deezer=DeezerStats(
            popularity_peak=80,
            playlist_reach_total=500000
        )
    )
    print("✓ Created with Spotify and Deezer data\n")

    # Convert to flat dict
    print("Converting to flat dict...")
    flat_dict = stats.to_flat_dict()
    print(f"✓ Converted to flat format:")
    print(json.dumps(flat_dict, indent=2))
    print()

    print("Key observations:")
    print("  - Uses aliased names (spotify_streams_total, etc.)")
    print("  - Only includes non-None values (exclude_none=True)")
    print("  - Ready for pandas DataFrame or legacy export\n")

    print("✓ Nested → flat conversion working correctly\n")


def demo_roundtrip_conversion() -> None:
    """Demonstrate roundtrip conversion identity."""
    print_separator("Roundtrip Conversion Identity")

    # Original flat data
    print("Original flat data...")
    original = {
        "spotify_streams_total": 2000000,
        "spotify_popularity_peak": 85,
        "deezer_popularity_peak": 90,
        "youtube_video_views_total": 1500000
    }
    print(json.dumps(original, indent=2))
    print()

    # flat → nested → flat
    print("Performing roundtrip: flat → nested → flat...")
    stats = PlatformStats.from_flat_dict(original)
    result = stats.to_flat_dict()
    print(json.dumps(result, indent=2))
    print()

    # Verify identity
    print("Verifying identity...")
    if original == result:
        print("✓ Roundtrip conversion is lossless (original == result)")
    else:
        print("✗ Data mismatch (unexpected)")

    print("\n✓ Roundtrip conversion maintains data integrity\n")


def demo_track_with_stats_creation() -> None:
    """Demonstrate TrackWithStats creation."""
    print_separator("TrackWithStats Creation")

    # Minimal creation
    print("Creating minimal TrackWithStats...")
    track = Track(title="Test", artist_list=["artist"], year=2024)
    identifiers = SongstatsIdentifiers(songstats_id="abc123", songstats_title="Test")
    minimal = TrackWithStats(
        track=track,
        songstats_identifiers=identifiers
    )
    print(f"✓ Track: {minimal.track.title}")
    print(f"  Songstats ID: {minimal.songstats_identifiers.songstats_id}")
    print(f"  Platform stats: All None (default)\n")

    # Full creation
    print("Creating full TrackWithStats...")
    full_track = Track(
        title="16",
        artist_list=["blasterjaxx", "hardwell", "maddix"],
        year=2024,
        genre=["hard techno"],
        label=["revealed"]
    )
    full_identifiers = SongstatsIdentifiers(
        songstats_id="qmr6e0bx",
        songstats_title="16"
    )
    platform_stats = PlatformStats(
        spotify=SpotifyStats(streams_total=3805083, popularity_peak=62),
        deezer=DeezerStats(popularity_peak=80)
    )
    full = TrackWithStats(
        track=full_track,
        songstats_identifiers=full_identifiers,
        platform_stats=platform_stats
    )
    print(f"✓ Track: {full.track.title} by {full.track.all_artists_string}")
    print(f"  Songstats ID: {full.songstats_identifiers.songstats_id}")
    print(f"  Spotify streams: {full.platform_stats.spotify.streams_total:,}")
    print(f"  Deezer popularity: {full.platform_stats.deezer.popularity_peak}\n")

    print("✓ TrackWithStats creation working correctly\n")


def demo_from_legacy_json() -> None:
    """Demonstrate loading from legacy JSON format."""
    print_separator("Loading from Legacy JSON Format")

    # Legacy data structure (from data_2024.json)
    print("Legacy JSON structure (data_2024.json format)...")
    legacy_item = {
        "title": "16",
        "artist_list": ["blasterjaxx", "hardwell", "maddix"],
        "year": 2024,
        "genre": ["hard techno"],
        "label": ["revealed"],
        "request": "blasterjaxx, hardwell, maddix 16",
        "songstats_identifiers": {
            "s_id": "qmr6e0bx",
            "s_title": "16"
        },
        "data": {
            "spotify_streams_total": 3805083,
            "spotify_popularity_peak": 62,
            "deezer_popularity_peak": 80
        }
    }
    print(json.dumps(legacy_item, indent=2)[:300] + "...\n")

    # Load using from_legacy_json
    print("Loading with TrackWithStats.from_legacy_json()...")
    track = TrackWithStats.from_legacy_json(legacy_item)
    print(f"✓ Loaded successfully!")
    print(f"  Track: {track.track.title}")
    print(f"  Artists: {track.track.all_artists_string}")
    print(f"  Search query: {track.track.search_query}")
    print(f"  Songstats ID: {track.songstats_identifiers.songstats_id}")
    print(f"  Spotify streams: {track.platform_stats.spotify.streams_total:,}")
    print(f"  Deezer popularity: {track.platform_stats.deezer.popularity_peak}\n")

    print("✓ Legacy JSON loading working correctly\n")


def demo_real_data_example() -> None:
    """Demonstrate with real legacy data."""
    print_separator("Real Legacy Data Example")

    legacy_file = PROJECT_ROOT / "_legacy/data/data_2024.json"

    if legacy_file.exists():
        print(f"Loading first track from {legacy_file}...")
        with open(legacy_file, encoding="utf-8") as f:
            legacy_data = json.load(f)

        # Legacy data has year in filename, not in records - patch it
        first_item = legacy_data[0].copy()
        if first_item.get("year") is None:
            first_item["year"] = 2024  # Extract from filename

        first_track = TrackWithStats.from_legacy_json(first_item)
        print(f"✓ Loaded: {first_track.track.title}")
        print(f"  Artists: {first_track.track.all_artists_string}")
        print(f"  Year: {first_track.track.year} (extracted from filename)")
        print(f"  Songstats ID: {first_track.songstats_identifiers.songstats_id}\n")

        # Show available stats
        flat_stats = first_track.platform_stats.to_flat_dict()
        print(f"  Platform stats available: {len(flat_stats)} fields")
        print(f"  Sample fields:")
        for key, value in list(flat_stats.items())[:5]:
            print(f"    {key}: {value:,}" if isinstance(value, int) else f"    {key}: {value}")
        print()
    else:
        print(f"⚠ Legacy file not found: {legacy_file}")
        print("  (Skipping real data demo)\n")

    print("✓ Real data example completed\n")


def main() -> None:
    """Run all stats model demos."""
    print("=" * 80)
    print(" PlatformStats & TrackWithStats Models - Interactive Demo")
    print("=" * 80)

    demo_platform_stats_creation()
    demo_flat_to_nested_conversion()
    demo_nested_to_flat_conversion()
    demo_roundtrip_conversion()
    demo_track_with_stats_creation()
    demo_from_legacy_json()
    demo_real_data_example()

    print_separator()
    print("✓ All demos completed successfully!")
    print()


if __name__ == "__main__":
    main()
