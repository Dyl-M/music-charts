"""Integration demo showing client → model data flow.

This script demonstrates how the API clients (MusicBee, Songstats)
integrate with the data models (Track, PlatformStats, YouTubeVideoData) to
create the complete data pipeline.

Note: YouTube data comes from Songstats API (no YouTube API quota used).
      YouTubeClient is available separately for deeper analysis if needed.

Requirements:
    - Valid MusicBee library path in settings
    - Songstats API key in _tokens/songstats_key.txt
    - Internet connection for Songstats API calls

Usage:
    python _demos/sandbox_integration_demo.py
"""

# Standard library
import json
from pathlib import Path

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.config.settings import PROJECT_ROOT, get_settings
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track
from msc.models.youtube import YouTubeVideo, YouTubeVideoData


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


def demo_musicbee_to_track_models() -> list[Track]:
    """Demonstrate MusicBeeClient → Track models conversion.

    Returns:
        List of Track models extracted from MusicBee library.
    """
    print_separator("MusicBee Client → Track Models")

    settings = get_settings()
    library_path = settings.musicbee_library

    if not library_path or not Path(library_path).exists():
        print("⚠ MusicBee library not found")
        print(f"  Expected: {library_path}")
        print("  Set MSC_MUSICBEE_LIBRARY environment variable")
        print("  Skipping MusicBee demo\n")
        return []

    print(f"Reading MusicBee library: {library_path}")
    client = MusicBeeClient(library_path=library_path)

    # Find playlist by name (more reliable than hardcoded ID)
    # Try year-based playlist first (e.g., "✅ 2025 Selection" for 2025)
    playlist_name = f"✅ {settings.year} Selection"

    print(f"Searching for playlist: {playlist_name}")
    playlist_id = client.find_playlist_by_name(playlist_name, exact_match=True)

    if not playlist_id:
        # Fallback: try configured playlist_id
        print(f"  Not found, trying configured ID {settings.playlist_id}...")
        playlist_id = settings.playlist_id
    else:
        print(f"  ✓ Found playlist with ID {playlist_id}\n")

    # Get tracks from playlist
    print(f"Extracting tracks from playlist {playlist_id}...")
    raw_tracks = client.get_playlist_tracks(playlist_id)

    if not raw_tracks:
        print(f"⚠ No tracks found in playlist {playlist_id}")
        print(f"  Available playlists: {list(client.get_all_playlists().keys())[:5]}...\n")
        return []

    print(f"✓ Found {len(raw_tracks)} tracks\n")

    # Convert first 3 tracks to Track models
    tracks = []
    print("Converting to Track models (first 3):")
    for idx, raw_track in enumerate(raw_tracks[:3], 1):
        # Handle grouping (might be list or string from libpybee)
        grouping = getattr(raw_track, "grouping", None)
        if isinstance(grouping, list) and grouping:
            grouping = grouping[0]  # Take first item if list

        track = Track(
            title=raw_track.title,
            artist_list=raw_track.artist_list,
            year=raw_track.year,
            genre=getattr(raw_track, "genre", []),
            label=getattr(raw_track, "label", []),
            grouping=grouping,
            search_query=getattr(raw_track, "request", None)  # Using alias
        )
        tracks.append(track)

        print(f"  {idx}. {track.title}")
        print(f"     Artists: {track.all_artists_string}")
        print(f"     Year: {track.year}")
        print(f"     Search query: {track.search_query}\n")

    print(f"✓ Converted {len(tracks)} tracks to Track models")
    print(f"  Models provide: validation, properties, serialization")
    print(f"  Access: track.primary_artist, track.has_genre('techno'), etc.\n")

    return tracks


def demo_songstats_to_trackwithstats() -> TrackWithStats | None:
    """Demonstrate SongstatsClient → TrackWithStats model conversion.

    Returns:
        TrackWithStats model with platform statistics.
    """
    print_separator("Songstats Client → TrackWithStats Model")

    # Check API key using settings
    settings = get_settings()
    api_key_file = settings.tokens_dir / "songstats_key.txt"
    if not api_key_file.exists():
        print("⚠ Songstats API key not found")
        print(f"  Expected: {api_key_file}")
        print("  Skipping Songstats demo\n")
        return None

    print("Initializing SongstatsClient...")
    client = SongstatsClient()

    # Search for a well-known track
    query = "blasterjaxx hardwell maddix 16"
    print(f"Searching Songstats for: '{query}'\n")

    search_results = client.search_track(query)

    if not search_results:
        print("⚠ No results found")
        return None

    first_result = search_results[0]
    track_id = first_result.get('songstats_track_id', first_result.get('id', ''))
    print(f"✓ Found: {first_result.get('title', 'Unknown')}")
    print(f"  Songstats ID: {track_id}\n")

    # Get platform stats and historical peaks
    print("Fetching platform statistics...")
    stats_data = client.get_platform_stats(track_id)

    if not stats_data:
        print("⚠ No stats available")
        return None

    print(f"✓ Retrieved {len(stats_data)} metrics\n")

    print("Fetching historical peaks...")
    try:
        # Get peaks from last year
        peaks_data = client.get_historical_peaks(track_id, start_date="2024-01-01")
        if peaks_data:
            print(f"✓ Retrieved {len(peaks_data)} peak values\n")
            # Merge peaks into stats
            stats_data.update(peaks_data)
        else:
            print("  No historical peaks available\n")
    except Exception as e:
        print(f"  Historical peaks not available: {e}\n")

    # Build Track model
    track = Track(
        title=first_result["title"],
        artist_list=first_result.get("artist_list", ["unknown"]),
        year=2024,  # Would come from MusicBee in real pipeline
        search_query=query
    )

    # Build SongstatsIdentifiers
    identifiers = SongstatsIdentifiers(
        songstats_id=track_id,
        songstats_title=first_result.get("title", "Unknown")
    )

    # Convert flat stats to nested PlatformStats model
    platform_stats = PlatformStats.from_flat_dict(stats_data)

    # Create TrackWithStats (combines all components)
    track_with_stats = TrackWithStats(
        track=track,
        songstats_identifiers=identifiers,
        platform_stats=platform_stats
    )

    # Display the integrated model
    print("TrackWithStats model created:")
    print(f"  Track: {track_with_stats.track.title}")
    print(f"  Artists: {track_with_stats.track.all_artists_string}")
    print(f"  Songstats ID: {track_with_stats.songstats_identifiers.songstats_id}\n")

    print("  Platform statistics (nested access):")
    if track_with_stats.platform_stats.spotify.streams_total:
        print(f"    Spotify streams: {track_with_stats.platform_stats.spotify.streams_total:,}")
    if track_with_stats.platform_stats.spotify.popularity_peak:
        print(f"    Spotify popularity: {track_with_stats.platform_stats.spotify.popularity_peak}")
    if track_with_stats.platform_stats.deezer.popularity_peak:
        print(f"    Deezer popularity: {track_with_stats.platform_stats.deezer.popularity_peak}")

    # Show flat export capability
    print("\n  Can export back to flat format:")
    flat_stats = track_with_stats.platform_stats.to_flat_dict()
    print(f"    {len(flat_stats)} fields available")
    print(f"    Sample: {list(flat_stats.keys())[:3]}\n")

    print("✓ TrackWithStats model demonstrates:")
    print("  - Nested data access (platform_stats.spotify.streams_total)")
    print("  - Flat ↔ nested conversion (from_flat_dict, to_flat_dict)")
    print("  - Type safety and validation")
    print("  - JSON serialization\n")

    return track_with_stats


def demo_youtube_to_videodata() -> YouTubeVideoData | None:
    """Demonstrate SongstatsClient → YouTubeVideoData model conversion.

    Note: YouTube video data comes from Songstats API, which already
    aggregates videos across all channels. This avoids using YouTube API
    quota. YouTubeClient is available for deeper analysis (likes, comments,
    duration) if needed, but not required for basic video tracking.

    Returns:
        YouTubeVideoData model with video information.
    """
    print_separator("Songstats → YouTubeVideoData Model")

    # Check API key using settings
    settings = get_settings()
    api_key_file = settings.tokens_dir / "songstats_key.txt"
    if not api_key_file.exists():
        print("⚠ Songstats API key not found")
        print(f"  Expected: {api_key_file}")
        print("  Skipping YouTube demo\n")
        return None

    print("Initializing SongstatsClient...")
    client = SongstatsClient()

    # Use known track ID from previous demo
    track_id = "qmr6e0bx"  # "16" by Blasterjaxx, Hardwell, Maddix
    print(f"Fetching YouTube videos for track: {track_id}\n")

    videos_data = client.get_youtube_videos(track_id)

    if not videos_data or not videos_data.get("all_sources"):
        print("⚠ No videos found")
        return None

    all_sources_data = videos_data["all_sources"]
    most_viewed_data = videos_data.get("most_viewed", all_sources_data[0] if all_sources_data else {})

    print(f"✓ Found {len(all_sources_data)} videos\n")

    # Create YouTubeVideo model for most viewed
    most_viewed = YouTubeVideo(
        video_id=most_viewed_data.get("ytb_id", most_viewed_data.get("video_id", "")),
        views=most_viewed_data.get("views", 0),
        channel_name=most_viewed_data.get("channel_name", "Unknown")
    )

    # Extract all video IDs
    video_ids = [v.get("ytb_id", v.get("video_id", "")) for v in all_sources_data]

    # Create YouTubeVideoData model
    video_data_model = YouTubeVideoData(
        most_viewed=most_viewed,
        all_sources=video_ids,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="qmr6e0bx",  # Would come from Songstats search
            songstats_title="16"
        )
    )

    # Display the model
    print("YouTubeVideoData model created:")
    print(f"  Track: {video_data_model.songstats_identifiers.songstats_title}")
    print(f"  Total videos found: {video_data_model.video_count}\n")

    print("  Most viewed video:")
    print(f"    Video ID: {video_data_model.most_viewed.video_id}")
    print(f"    Views: {video_data_model.most_viewed.views:,}")
    print(f"    Channel: {video_data_model.most_viewed.channel_name}")
    print(f"    Topic channel: {video_data_model.most_viewed.is_topic_channel}\n")

    print("  All video sources:")
    for idx, vid_id in enumerate(video_data_model.all_sources[:3], 1):
        print(f"    {idx}. {vid_id}")
    if video_data_model.video_count > 3:
        print(f"    ... and {video_data_model.video_count - 3} more\n")

    print("✓ YouTubeVideoData model demonstrates:")
    print("  - Video aggregation (most_viewed, all_sources)")
    print("  - Topic channel detection")
    print("  - View count tracking\n")

    return video_data_model


def demo_complete_pipeline_flow() -> None:
    """Demonstrate complete data flow: extract → enrich → integrate."""
    print_separator("Complete Pipeline Flow")

    print("Pipeline stages:")
    print("  1. Extract: MusicBeeClient → Track models")
    print("  2. Enrich: SongstatsClient → PlatformStats")
    print("  3. Enhance: SongstatsClient → YouTubeVideoData (quota-free)")
    print("  4. Integrate: Combine into TrackWithStats\n")

    print("Simulating pipeline with one track...\n")

    # Stage 1: Extract
    print("[Stage 1] Extracting track from MusicBee...")
    track = Track(
        title="16",
        artist_list=["blasterjaxx", "hardwell", "maddix"],
        year=2024,
        genre=["hard techno"],
        label=["revealed"],
        search_query="blasterjaxx hardwell maddix 16"
    )
    print(f"✓ Track: {track.title} by {track.all_artists_string}\n")

    # Stage 2: Enrich (would use SongstatsClient in production)
    print("[Stage 2] Enriching with Songstats data...")
    print("  (In production: SongstatsClient.search_track() → get_comprehensive_stats())")

    # Simulate stats data
    platform_stats = PlatformStats.from_flat_dict({
        "spotify_streams_total": 3805083,
        "spotify_popularity_peak": 62,
        "deezer_popularity_peak": 80,
        "youtube_video_views_total": 527735
    })
    print(f"✓ Platform stats loaded: {len(platform_stats.to_flat_dict())} fields\n")

    # Stage 3: Build integrated model
    print("[Stage 3] Creating TrackWithStats...")
    track_with_stats = TrackWithStats(
        track=track,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        ),
        platform_stats=platform_stats
    )
    print(f"✓ TrackWithStats created\n")

    # Stage 4: Add YouTube data (from Songstats, quota-free)
    print("[Stage 4] Adding YouTube data...")
    print("  (In production: SongstatsClient.get_youtube_videos())")
    youtube_data = YouTubeVideoData(
        most_viewed=YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        ),
        all_sources=["s0UcVIcQ8B4", "ekZ06PHmxAw", "cf7E_u0jATs"],
        songstats_identifiers=track_with_stats.songstats_identifiers
    )
    print(f"✓ YouTube data: {youtube_data.video_count} videos, {youtube_data.most_viewed.views:,} views\n")

    # Final output
    print("=" * 60)
    print("Pipeline Output (ready for ranking/export):")
    print("=" * 60)
    print(f"\nTrack: {track_with_stats.track.title}")
    print(f"Artists: {track_with_stats.track.all_artists_string}")
    print(f"Year: {track_with_stats.track.year}")
    print(f"Songstats ID: {track_with_stats.songstats_identifiers.songstats_id}")
    print(f"\nSpotify:")
    print(f"  Streams: {track_with_stats.platform_stats.spotify.streams_total:,}")
    print(f"  Popularity: {track_with_stats.platform_stats.spotify.popularity_peak}")
    print(f"\nDeezer:")
    print(f"  Popularity: {track_with_stats.platform_stats.deezer.popularity_peak}")
    print(f"\nYouTube:")
    print(f"  Videos: {youtube_data.video_count}")
    print(f"  Most viewed: {youtube_data.most_viewed.views:,} views")
    print(f"  Channel: {youtube_data.most_viewed.channel_name}")
    print()

    print("✓ Complete pipeline demonstrates:")
    print("  - Client → Model integration")
    print("  - Multi-source data enrichment")
    print("  - Type-safe data structures")
    print("  - Ready for analysis/ranking stage\n")


def demo_legacy_data_migration() -> None:
    """Demonstrate loading legacy JSON into new models."""
    print_separator("Legacy Data Migration")

    # Use PROJECT_ROOT for legacy data path
    legacy_file = PROJECT_ROOT / "_legacy" / "data" / "data_2024.json"

    if not legacy_file.exists():
        print("⚠ Legacy data file not found")
        print(f"  Expected: {legacy_file}")
        print("  Skipping migration demo\n")
        return

    print(f"Loading legacy data: {legacy_file}")
    with open(legacy_file, encoding="utf-8") as f:
        legacy_data = json.load(f)

    print(f"✓ Loaded {len(legacy_data)} tracks\n")

    # Convert first track
    print("Converting first track to new model format...")
    first_item = legacy_data[0].copy()

    # Patch year (legacy data has year in filename, not records)
    if first_item.get("year") is None:
        first_item["year"] = 2024

    # Use TrackWithStats.from_legacy_json() helper
    track = TrackWithStats.from_legacy_json(first_item)

    print(f"✓ Converted: {track.track.title}")
    print(f"  Artists: {track.track.all_artists_string}")
    print(f"  Songstats ID: {track.songstats_identifiers.songstats_id}\n")

    # Show nested access (new) vs flat access (old)
    print("Data access comparison:")
    print("\n  Legacy (flat dict):")
    print(f"    data['spotify_streams_total'] = {first_item['data'].get('spotify_streams_total', 'N/A')}")

    print("\n  New models (nested):")
    print(f"    track.platform_stats.spotify.streams_total = {track.platform_stats.spotify.streams_total}")

    print("\n  Benefits of new approach:")
    print("    - Type safety (Pydantic validation)")
    print("    - IDE autocomplete (platform_stats.spotify.)")
    print("    - Organized structure (by platform)")
    print("    - Can convert back to flat for pandas/export\n")

    # Show export capability
    print("Exporting back to flat format:")
    flat_stats = track.platform_stats.to_flat_dict()
    print(f"✓ {len(flat_stats)} fields exported")
    print(f"  Sample: {json.dumps(dict(list(flat_stats.items())[:3]), indent=2)}\n")

    print("✓ Legacy migration demonstrates:")
    print("  - Backward compatibility (from_legacy_json)")
    print("  - Lossless conversion (roundtrip tested)")
    print("  - Gradual migration path (both formats coexist)\n")


def main() -> None:
    """Run all integration demos."""
    print("=" * 80)
    print(" Client → Model Integration Demos")
    print("=" * 80)
    print("\nThese demos show how API clients feed data into Pydantic models")
    print("to create the complete data pipeline.\n")

    # Demo 1: MusicBee → Track models
    demo_musicbee_to_track_models()

    # Demo 2: Songstats → TrackWithStats
    demo_songstats_to_trackwithstats()

    # Demo 3: YouTube → YouTubeVideoData
    demo_youtube_to_videodata()

    # Demo 4: Complete pipeline flow
    demo_complete_pipeline_flow()

    # Demo 5: Legacy data migration
    demo_legacy_data_migration()

    print_separator()
    print("✓ All integration demos completed!")
    print()


if __name__ == "__main__":
    main()
