"""Sandbox script to test SongstatsClient GET methods.

This script demonstrates all GET methods using the track "Mad" by Martin Garrix and Lauv.
"""

# Standard library
import json
from datetime import datetime, timedelta

# Local
from msc.clients.songstats import SongstatsClient


def print_section(title: str) -> None:
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_json(data: dict | list, indent: int = 2) -> None:
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def main() -> None:
    """Run all GET methods on the track 'Mad' by Martin Garrix and Lauv."""
    print_section("SongstatsClient GET Methods Demo")
    print("Track: 'Mad' by Martin Garrix and Lauv")

    # Initialize client
    client = SongstatsClient()

    # 1. Health Check
    print_section("1. Health Check")
    is_healthy = client.health_check()
    print(f"API is {'healthy' if is_healthy else 'unhealthy'}: {is_healthy}")

    # 2. Get Quota
    print_section("2. API Quota Status")
    quota = client.get_quota()
    print_json(quota)

    # 3. Search Track
    print_section("3. Search Track")
    search_query = "Martin Garrix Lauv Mad"
    print(f"Searching for: {search_query}")
    search_results = client.search_track(search_query, limit=3)

    if not search_results:
        print("❌ No results found!")
        return

    print(f"\nFound {len(search_results)} result(s):")
    print_json(search_results)

    # Use the first result
    track = search_results[0]
    track_id = track.get("songstats_track_id")
    track_name = track.get("name", "Unknown")
    artist_name = track.get("artist", {}).get("name", "Unknown")

    print(f"\n✓ Using track: '{track_name}' by {artist_name}")
    print(f"  Songstats ID: {track_id}")

    if not track_id:
        print("❌ No track ID found!")
        return

    # 4. Get Platform Stats
    print_section("4. Platform Statistics")
    print("Fetching stats from all platforms...")
    stats = client.get_platform_stats(track_id)

    if stats:
        print(f"\nReceived {len(stats)} metrics:")
        # Print a sample of key metrics
        key_metrics = {
            k: v for k, v in stats.items()
            if any(term in k for term in ["streams", "followers", "popularity", "playlist"])
        }
        print_json(key_metrics)
        print(f"\n... and {len(stats) - len(key_metrics)} more metrics")

    else:
        print("No stats available")

    # 5. Get Historical Peaks
    print_section("5. Historical Peak Popularity")
    # Calculate start date (1 year ago)
    start_date = (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")
    print(f"Fetching peaks since: {start_date}")

    peaks = client.get_historical_peaks(
        track_id,
        start_date=start_date,
        sources=["spotify", "deezer", "tidal"]
    )

    if peaks:
        print("\nPeak popularity by platform:")
        print_json(peaks)

    else:
        print("No peak data available")

    # 6. Get YouTube Videos
    print_section("6. YouTube Video Data")
    print("Fetching YouTube videos...")
    youtube_data = client.get_youtube_videos(track_id)

    if youtube_data:
        most_viewed = youtube_data.get("most_viewed", {})
        most_viewed_is_topic = youtube_data.get("most_viewed_is_topic", False)
        all_sources = youtube_data.get("all_sources", [])

        print(f"\nMost viewed (non-Topic): {most_viewed.get('ytb_id', 'N/A')}")
        if most_viewed:
            print(f"  Views: {most_viewed.get('views', 0):,}")
            print(f"  Channel: {most_viewed.get('channel_name', 'N/A')}")

        print(f"\nOverall most viewed is Topic channel: {most_viewed_is_topic}")
        print(f"Total videos found: {len(all_sources)}")

        if all_sources:
            print("\nAll videos:")
            print_json(all_sources)
    else:
        print("No YouTube data available")

    # 7. Get Track Info
    print_section("7. Track Information")
    print("Fetching track info with video data...")
    track_info = client.get_track_info(track_id, with_videos=True)

    if track_info:
        print_json(track_info)

    else:
        print("No track info available")

    # Summary
    print_section("Demo Complete")
    print("✓ All GET methods executed successfully!")
    print(f"\nTrack analyzed: '{track_name}' by {artist_name}")
    print(f"Songstats ID: {track_id}")

    # Close client
    client.close()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("\n\n⚠️ Demo interrupted by user")

    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise
