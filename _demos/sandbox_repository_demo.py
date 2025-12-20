"""Interactive demo for Repository Pattern implementation.

This script demonstrates the Repository Pattern with JSONTrackRepository and
JSONStatsRepository, showing CRUD operations, persistence, and export capabilities.

Requirements:
    - Creates temporary files in _data/demo/
    - Cleans up after execution

Usage:
    python _demos/sandbox_repository_demo.py
"""

# Standard library
from pathlib import Path

# Local
from msc.models.platforms import SpotifyStats
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track
from msc.storage.json_repository import JSONStatsRepository, JSONTrackRepository


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


def cleanup_demo_files() -> None:
    """Clean up demo files and directories."""
    demo_dir = Path("_data/demo")
    if demo_dir.exists():
        for file in demo_dir.glob("*"):
            file.unlink()
        if not any(demo_dir.iterdir()):
            demo_dir.rmdir()


def create_sample_track(title: str, artist: str, year: int = 2025) -> Track:
    """Create a sample track for testing.

    Args:
        title: Track title
        artist: Artist name
        year: Release year

    Returns:
        Track instance
    """
    return Track(
        title=title,
        artist_list=[artist],
        year=year,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id=f"id_{title.lower().replace(' ', '_')}",
            songstats_title=title,
        ),
    )


def demo_track_repository_crud() -> None:
    """Demonstrate CRUD operations with JSONTrackRepository."""
    print_separator("JSONTrackRepository - CRUD Operations")

    # Create repository
    repo_path = Path("_data/demo/tracks.json")
    repo = JSONTrackRepository(repo_path)

    print(f"Created repository at: {repo_path}")
    print()

    # CREATE: Add tracks
    track1 = create_sample_track("Levels", "Avicii", 2011)
    track2 = create_sample_track("Animals", "Martin Garrix", 2013)
    track3 = create_sample_track("Clarity", "Zedd", 2012)

    repo.add(track1)
    repo.add(track2)
    repo.add(track3)

    print("✓ Added 3 tracks to repository")
    print()

    # READ: Get single track
    retrieved = repo.get(track1.identifier)
    print(f"READ: Retrieved track '{track1.identifier}'")
    print(f"  Title: {retrieved.title if retrieved else 'Not found'}")
    print(f"  Artist: {retrieved.primary_artist if retrieved else 'N/A'}")
    print()

    # READ: Get all tracks
    all_tracks = repo.get_all()
    print(f"READ ALL: Repository contains {len(all_tracks)} tracks")
    for track in all_tracks:
        print(f"  - {track.title} by {track.primary_artist} ({track.year})")
    print()

    # UPDATE: Modify a track (using add() to overwrite)
    updated_track = track1.model_copy(
        update={"genre": ["progressive house", "edm"]}
    )
    repo.add(updated_track)

    retrieved_updated = repo.get(track1.identifier)
    print(f"UPDATE: Updated track '{track1.identifier}'")
    print(f"  New genre: {retrieved_updated.genre if retrieved_updated else []}")
    print()

    # DELETE: Remove a track
    repo.remove(track2.identifier)
    remaining = repo.get_all()
    print(f"DELETE: Removed track '{track2.identifier}'")
    print(f"  Remaining tracks: {len(remaining)}")
    print()

    # Check if exists
    print("EXISTS check:")
    print(f"  '{track1.identifier}' exists: {repo.exists(track1.identifier)}")
    print(f"  '{track2.identifier}' exists: {repo.exists(track2.identifier)}")
    print()

    print("✓ CRUD operations complete!")


def demo_stats_repository_crud() -> None:
    """Demonstrate CRUD operations with JSONStatsRepository."""
    print_separator("JSONStatsRepository - CRUD Operations")

    # Create repository
    repo_path = Path("_data/demo/stats.json")
    repo = JSONStatsRepository(repo_path)

    print(f"Created stats repository at: {repo_path}")
    print()

    # Create TrackWithStats
    track = create_sample_track("Strobe", "deadmau5", 2009)

    platform_stats = PlatformStats(
        spotify=SpotifyStats(
            streams_total=50_000_000,
            popularity_peak=85,
        )
    )

    track_with_stats = TrackWithStats(
        track=track,
        songstats_identifiers=track.songstats_identifiers,
        platform_stats=platform_stats,
    )

    # CREATE
    repo.add(track_with_stats)
    print("✓ Added track with stats")
    print(f"  Track: {track.title}")
    print(f"  Spotify streams: {platform_stats.spotify.streams_total:,}")
    print()

    # READ
    retrieved = repo.get(track.identifier)
    print("READ: Retrieved track with stats")
    if retrieved:
        print(f"  Track: {retrieved.track.title}")
        print(f"  Spotify streams: {retrieved.platform_stats.spotify.streams_total:,}")
    print()

    # UPDATE (using add() to overwrite)
    updated_stats = track_with_stats.model_copy(
        update={
            "platform_stats": platform_stats.model_copy(
                update={
                    "spotify": platform_stats.spotify.model_copy(
                        update={"streams_total": 75_000_000}
                    )
                }
            )
        }
    )

    repo.add(updated_stats)
    print("UPDATE: Updated stream count")

    retrieved_updated = repo.get(track.identifier)
    if retrieved_updated:
        print(f"  New stream count: {retrieved_updated.platform_stats.spotify.streams_total:,}")
    print()

    print("✓ Stats repository CRUD complete!")


def demo_batch_operations() -> None:
    """Demonstrate batch operations."""
    print_separator("Batch Operations")

    repo_path = Path("_data/demo/batch_tracks.json")
    repo = JSONTrackRepository(repo_path)

    # Create multiple tracks
    tracks = [
        create_sample_track("Track 1", "Artist A"),
        create_sample_track("Track 2", "Artist B"),
        create_sample_track("Track 3", "Artist C"),
        create_sample_track("Track 4", "Artist D"),
        create_sample_track("Track 5", "Artist E"),
    ]

    print(f"Adding {len(tracks)} tracks in batch...")

    # Add all at once
    for track in tracks:
        repo.add(track)

    print(f"✓ Added {len(tracks)} tracks")
    print()

    # Get all
    all_tracks = repo.get_all()
    print(f"Repository now contains {len(all_tracks)} tracks")

    # Clear all
    repo.clear()
    remaining = repo.get_all()
    print(f"After clear: {len(remaining)} tracks remaining")
    print()

    print("✓ Batch operations complete!")


def demo_persistence() -> None:
    """Demonstrate persistence across sessions."""
    print_separator("Persistence Across Sessions")

    repo_path = Path("_data/demo/persistent_tracks.json")

    # Session 1: Create and save
    print("Session 1: Creating repository and adding tracks...")
    repo1 = JSONTrackRepository(repo_path)
    repo1.add(create_sample_track("Session 1 Track", "Artist X"))
    count1 = len(repo1.get_all())
    print(f"  Added tracks, count: {count1}")
    print()

    # Session 2: Load existing data
    print("Session 2: Loading repository from existing file...")
    repo2 = JSONTrackRepository(repo_path)
    count2 = len(repo2.get_all())
    print(f"  Loaded tracks, count: {count2}")
    print()

    if count1 == count2:
        print("✓ Data persisted correctly!")
    else:
        print("✗ Data mismatch!")


def demo_export_formats() -> None:
    """Demonstrate export to different formats."""
    print_separator("Export to Multiple Formats")

    # Create repository with stats
    repo = JSONStatsRepository(Path("_data/demo/export_source.json"))

    # Add sample data
    tracks_with_stats = []
    for i in range(3):
        track = create_sample_track(f"Track {i+1}", f"Artist {i+1}")
        platform_stats = PlatformStats(
            spotify=SpotifyStats(
                streams_total=(i + 1) * 1_000_000,
                popularity_peak=70 + (i * 5),
            )
        )
        tracks_with_stats.append(
            TrackWithStats(
                track=track,
                songstats_identifiers=track.songstats_identifiers,
                platform_stats=platform_stats,
            )
        )
        repo.add(tracks_with_stats[-1])

    print(f"Created repository with {len(tracks_with_stats)} enriched tracks")
    print()

    # Export to different formats
    output_dir = Path("_data/demo")

    # 1. JSON (nested)
    json_path = output_dir / "export_nested.json"
    repo.export_to_json(json_path, flat=False)
    print(f"✓ Exported to JSON (nested): {json_path}")

    # 2. JSON (flat)
    json_flat_path = output_dir / "export_flat.json"
    repo.export_to_json(json_flat_path, flat=True)
    print(f"✓ Exported to JSON (flat): {json_flat_path}")

    # 3. CSV
    csv_path = output_dir / "export.csv"
    repo.export_to_csv(csv_path)
    print(f"✓ Exported to CSV: {csv_path}")
    print()

    # Show file sizes
    print("File sizes:")
    for path in [json_path, json_flat_path, csv_path]:
        if path.exists():
            size = path.stat().st_size
            print(f"  {path.name}: {size:,} bytes")

    print()
    print("Export formats:")
    print("  • Nested JSON: Full model hierarchy (for APIs, backups)")
    print("  • Flat JSON: Flattened structure (legacy compatibility)")
    print("  • CSV: Tabular format (for Excel, data analysis)")


def demo_error_handling() -> None:
    """Demonstrate error handling."""
    print_separator("Error Handling")

    repo_path = Path("_data/demo/error_test.json")
    repo = JSONTrackRepository(repo_path)

    # Try to get non-existent track
    result = repo.get("non_existent_id")
    print(f"GET non-existent track: {result}")
    print("  → Returns None (defensive coding)")
    print()

    # Try to remove non-existent track
    repo.remove("non_existent_id")
    print("REMOVE non-existent track: No error raised")
    print("  → Silently skips (defensive coding)")
    print()

    # Try to add non-existent track (add creates if doesn't exist)
    fake_track = create_sample_track("Fake", "Artist")
    repo.add(fake_track)
    exists = repo.exists(fake_track.identifier)
    print(f"ADD non-existent track: exists={exists}")
    print("  → Creates new entry (add() method)")
    print()

    print("✓ Repository handles errors gracefully!")


def demo_repository_pattern_benefits() -> None:
    """Demonstrate Repository Pattern benefits."""
    print_separator("Repository Pattern Benefits")

    print("Benefits of Repository Pattern:")
    print()

    print("1. Abstraction:")
    print("   - Business logic doesn't depend on JSON implementation")
    print("   - Can swap JSON → SQLite → PostgreSQL without changing client code")
    print()

    print("2. Testability:")
    print("   - Easy to mock repositories for unit tests")
    print("   - No need for real files in tests")
    print()

    print("3. Centralized Data Access:")
    print("   - All CRUD operations in one place")
    print("   - Consistent error handling and logging")
    print()

    print("4. Type Safety:")
    print("   - Generic Repository[T] ensures type consistency")
    print("   - Pydantic models validate data automatically")
    print()

    print("5. Flexibility:")
    print("   - Multiple export formats (JSON, CSV)")
    print("   - Easy to add new formats or storage backends")


def main() -> None:
    """Run all repository demos."""
    print("=" * 80)
    print(" Repository Pattern - Interactive Demo")
    print("=" * 80)

    # Clean up any existing demo files first
    cleanup_demo_files()

    try:
        demo_track_repository_crud()
        demo_stats_repository_crud()
        demo_batch_operations()
        demo_persistence()
        demo_export_formats()
        demo_error_handling()
        demo_repository_pattern_benefits()

        print_separator()
        print("✓ All demos completed successfully!")
        print()
        print("Key Takeaways:")
        print("1. Repository Pattern abstracts data access from business logic")
        print("2. JSONTrackRepository: Stores Track objects")
        print("3. JSONStatsRepository: Stores TrackWithStats objects")
        print("4. Full CRUD operations: Create, Read, Update, Delete")
        print("5. Multiple export formats: JSON (nested/flat), CSV")
        print("6. Defensive error handling throughout")
        print()

    finally:
        # Clean up demo files
        cleanup_demo_files()
        print("✓ Demo files cleaned up")


if __name__ == "__main__":
    main()
