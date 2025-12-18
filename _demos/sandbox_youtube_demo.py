"""Interactive demo for YouTubeClient.

This script demonstrates the full capabilities of the YouTubeClient class,
including OAuth authentication, video metadata fetching, and playlist management.

Requirements:
    - YouTube OAuth credentials in _tokens/oauth.json
    - Browser access for initial OAuth flow
    - Active internet connection

Usage:
    python _demos/sandbox_youtube_demo.py
"""

# Standard library
import sys
from pathlib import Path

# Local
from msc.clients.youtube import YouTubeClient

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


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


def demo_health_and_quota() -> None:
    """Demonstrate health check and quota methods."""
    print_separator("Health Check & Quota")

    with YouTubeClient() as client:
        # Health check
        health = client.health_check()
        print(f"✓ Health Check: {'PASS' if health else 'FAIL'}")

        # Quota information
        quota = client.get_quota()
        print(f"✓ Daily Quota Limit: {quota['daily_limit']:,} units")
        print(f"  Note: {quota['note']}")


def demo_video_details() -> None:
    """Demonstrate fetching single video details."""
    print_separator("Single Video Details")

    with YouTubeClient() as client:
        # Fetch Rick Astley - Never Gonna Give You Up
        video_id = "dQw4w9WgXcQ"
        video = client.get_video_details(video_id)

        if video:
            print(f"✓ Video ID: {video['video_id']}")
            print(f"  Title: {video['title']}")
            print(f"  Channel: {video['channel_name']}")
            print(f"  Published: {video['published_at']}")
            print(f"  Duration: {video['duration']}")
            print(f"  Views: {video['view_count']:,}")
            print(f"  Likes: {video['like_count']:,}")
            print(f"  Comments: {video['comment_count']:,}")

        else:
            print("✗ Failed to fetch video details")


def demo_batch_videos() -> None:
    """Demonstrate batch fetching of multiple videos."""
    print_separator("Batch Video Fetch")

    with YouTubeClient() as client:
        video_ids = [
            "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
            "9bZkp7q19f0",  # PSY - GANGNAM STYLE
            "kJQP7kiw5Fk",  # Luis Fonsi - Despacito
        ]

        videos = client.get_videos_details(video_ids)

        if videos:
            print(f"✓ Fetched {len(videos)} videos:\n")
            for idx, video in enumerate(videos, 1):
                print(f"  {idx}. {video['title']}")
                print(f"     Channel: {video['channel_name']}")
                print(f"     Views: {video['view_count']:,}")
                print()

        else:
            print("✗ Failed to fetch videos")


def demo_playlist_videos() -> None:
    """Demonstrate fetching videos from a playlist."""
    print_separator("Playlist Videos")

    with YouTubeClient() as client:
        # Example playlist ID (replace with a known small public playlist)
        playlist_id = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"

        print(f"Fetching playlist: {playlist_id}")
        videos = client.get_playlist_videos(playlist_id)

        if videos:
            print(f"✓ Fetched {len(videos)} videos from playlist:\n")
            for idx, video in enumerate(videos[:5], 1):  # Show first 5
                print(f"  {idx}. {video['title']}")
                print(f"     Video ID: {video['video_id']}")
                print(f"     Position: {video['position']}")
                print()

            if len(videos) > 5:
                print(f"  ... and {len(videos) - 5} more videos")
        else:
            print("✗ Playlist is empty or failed to fetch")


def demo_error_handling() -> None:
    """Demonstrate error handling for invalid inputs."""
    print_separator("Error Handling")

    with YouTubeClient() as client:
        # Invalid video ID
        print("Testing invalid video ID...")
        result = client.get_video_details("invalid_id_12345")
        print(f"✓ Invalid video ID returns: {result}")

        # Empty video ID
        print("\nTesting empty video ID...")
        result = client.get_video_details("")
        print(f"✓ Empty video ID returns: {result}")

        # Invalid playlist ID
        print("\nTesting invalid playlist ID...")
        result = client.get_playlist_videos("invalid_playlist_12345")
        print(f"✓ Invalid playlist ID returns: {result}")


def main() -> None:
    """Run all demo functions."""
    print("\n" + "=" * 80)
    print(" YouTubeClient Interactive Demo")
    print(" Demonstrates OAuth authentication, video metadata, and playlist management")
    print("=" * 80)

    try:
        # Run demo sections
        demo_health_and_quota()
        demo_video_details()
        demo_batch_videos()
        demo_playlist_videos()
        demo_error_handling()

        print_separator("Demo Complete")
        print("✓ All demonstrations completed successfully!")
        print("\nNote: First run will require browser authentication for OAuth.")
        print("      Credentials are cached in _tokens/credentials.json for future use.")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have:")
        print("  1. YouTube OAuth credentials in _tokens/oauth.json")
        print("  2. Completed initial OAuth flow (browser authentication)")
        print("\nSee project documentation for setup instructions.")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("\nPlease check your credentials and internet connection.")


if __name__ == "__main__":
    main()
