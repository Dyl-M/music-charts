"""Interactive demo for MusicBeeClient.

This script demonstrates the full capabilities of the MusicBeeClient class,
including library loading, playlist discovery, track filtering, and error handling.

Requirements:
    - Test fixture XML at _tests/fixtures/test_library.xml
    - No external dependencies or setup required

Usage:
    python _demos/sandbox_musicbee_demo.py
"""

# Standard library
from pathlib import Path

# Third-party
import libpybee

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.config.settings import Settings

# Test fixture path
FIXTURE_PATH = Path("_tests/fixtures/test_library.xml")


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


def clear_libpybee_state() -> None:
    """Clear libpybee global state to allow re-parsing."""
    if hasattr(libpybee.Track, "all_tracks"):
        libpybee.Track.all_tracks.clear()
    if hasattr(libpybee.Playlist, "all_playlists"):
        libpybee.Playlist.all_playlists.clear()


def demo_library_loading() -> None:
    """Demonstrate library loading and caching behavior."""
    print_separator("Library Loading & Caching")

    clear_libpybee_state()
    settings = Settings(musicbee_library=FIXTURE_PATH)

    with MusicBeeClient(settings=settings) as client:
        # First load
        print("Loading library for the first time...")
        library = client.get_library()

        print(f"✓ Library loaded successfully")
        print(f"  Total playlists: {len(library.playlists)}")
        print(f"  Total tracks: {len(library.tracks)}")

        # Second load (from cache)
        print("\nLoading library again (should use cache)...")
        library2 = client.get_library()

        if library is library2:
            print("✓ Library loaded from cache (same object)")
        else:
            print("✗ Library was re-parsed (unexpected)")

        print("\n✓ Context manager will clean up cached files on exit")


def demo_playlist_discovery() -> None:
    """Demonstrate playlist discovery and listing."""
    print_separator("Playlist Discovery")

    clear_libpybee_state()
    settings = Settings(musicbee_library=FIXTURE_PATH)

    with MusicBeeClient(settings=settings) as client:
        playlists = client.get_all_playlists()

        print(f"✓ Found {len(playlists)} playlist(s):\n")

        # Display playlists in a formatted table
        print(f"{'Playlist ID':<15} {'Name':<30} {'Tracks':<10}")
        print("-" * 80)

        for pid, info in playlists.items():
            name = info['name']
            track_count = info['track_count']
            print(f"{pid:<15} {name:<30} {track_count:<10}")

        print()


def demo_track_filtering() -> None:
    """Demonstrate track filtering by year."""
    print_separator("Track Filtering by Year")

    clear_libpybee_state()
    settings = Settings(musicbee_library=FIXTURE_PATH)

    with MusicBeeClient(settings=settings) as client:
        # Get all tracks from test playlist
        playlist_id = "4361"
        print(f"Working with playlist: {playlist_id}")

        all_tracks = client.get_playlist_tracks(playlist_id)
        print(f"✓ Total tracks in playlist: {len(all_tracks)}")

        # Filter by 2024
        print("\nFiltering by year 2024...")
        tracks_2024 = client.get_playlist_tracks(playlist_id, year=2024)
        print(f"✓ Found {len(tracks_2024)} track(s) from 2024")

        for track in tracks_2024:
            print(f"  - {track.title} by {', '.join(track.artist_list)}")

        # Filter by 2025
        print("\nFiltering by year 2025...")
        tracks_2025 = client.get_playlist_tracks(playlist_id, year=2025)
        print(f"✓ Found {len(tracks_2025)} track(s) from 2025")

        for track in tracks_2025:
            print(f"  - {track.title} by {', '.join(track.artist_list)}")

        # Filter by year with no matches
        print("\nFiltering by year 2026 (no matches expected)...")
        tracks_2026 = client.get_playlist_tracks(playlist_id, year=2026)
        print(f"✓ Found {len(tracks_2026)} track(s) from 2026 (empty list)")

        print()


def demo_track_details() -> None:
    """Demonstrate accessing track attributes."""
    print_separator("Track Details")

    clear_libpybee_state()
    settings = Settings(musicbee_library=FIXTURE_PATH)

    with MusicBeeClient(settings=settings) as client:
        # Get first track from playlist
        playlist_id = "4361"
        tracks = client.get_playlist_tracks(playlist_id)

        if tracks:
            track = tracks[0]
            print(f"✓ Displaying details for first track:\n")
            print(f"  Title:        {track.title}")
            print(f"  Artist(s):    {', '.join(track.artist_list)}")
            print(f"  Album:        {track.album}")
            print(f"  Year:         {track.year}")
            print(f"  Genre:        {track.genre}")
            print(f"  Label:        {track.grouping}")
            print(f"  Play Count:   {track.play_count}")

            print("\n✓ All track attributes accessible")

        else:
            print("✗ No tracks found")

        print()


def demo_error_handling() -> None:
    """Demonstrate error handling for invalid inputs."""
    print_separator("Error Handling")

    clear_libpybee_state()
    settings = Settings(musicbee_library=FIXTURE_PATH)

    with MusicBeeClient(settings=settings) as client:
        # Test 1: Non-existent playlist
        print("Testing non-existent playlist ID...")
        result = client.get_playlist_tracks("invalid_99999")
        print(f"✓ Non-existent playlist returns: {result} (empty list)")

        # Test 2: Empty playlist
        print("\nTesting empty playlist (ID: 9999)...")
        result = client.get_playlist_tracks("9999")
        print(f"✓ Empty playlist returns: {result} (empty list)")

        # Test 3: Valid playlist exists
        print("\nTesting valid playlist (ID: 4361)...")
        result = client.get_playlist_tracks("4361")
        print(f"✓ Valid playlist returns: {len(result)} track(s)")

        print("\n✓ Client handles all error cases gracefully (defensive coding)")
        print()


def main() -> None:
    """Run all demo functions."""
    print("\n" + "=" * 80)
    print(" MusicBeeClient Interactive Demo")
    print(" Demonstrates library parsing, playlist management, and track filtering")
    print("=" * 80)

    # Check fixture exists
    if not FIXTURE_PATH.exists():
        print(f"\n✗ Error: Test fixture not found at {FIXTURE_PATH}")
        print("\nPlease ensure _tests/fixtures/test_library.xml exists.")
        return

    try:
        # Run demo sections
        demo_library_loading()
        demo_playlist_discovery()
        demo_track_filtering()
        demo_track_details()
        demo_error_handling()

        print_separator("Demo Complete")
        print("✓ All demonstrations completed successfully!")
        print(f"\nTest fixture used: {FIXTURE_PATH}")
        print("Note: MusicBeeClient uses local XML parsing (no API calls required).")

    except FileNotFoundError as e:
        print(f"\n✗ Error: {e}")
        print("\nMake sure you have:")
        print(f"  1. Test fixture at {FIXTURE_PATH}")
        print("  2. Write permissions in the data directory")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        print("\nPlease check the test fixture and file permissions.")


if __name__ == "__main__":
    main()
