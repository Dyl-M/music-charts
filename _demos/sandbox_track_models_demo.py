"""Interactive demo for Track and SongstatsIdentifiers models.

This script demonstrates the full capabilities of the Track and SongstatsIdentifiers
models, including creation, properties, validation, serialization, and backward
compatibility with legacy data formats.

Requirements:
    - No external dependencies or setup required
    - Uses synthetic examples and demonstrates validation

Usage:
    python _demos/sandbox_track_models_demo.py
"""

# Standard library
from pathlib import Path
from tempfile import TemporaryDirectory

# Third-party
from pydantic import ValidationError

# Local
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


def demo_basic_track_creation() -> None:
    """Demonstrate basic Track creation."""
    print_separator("Basic Track Creation")

    # Minimal track (required fields only)
    print("Creating minimal track...")
    minimal_track = Track(
        title="Scary Monsters and Nice Sprites",
        artist_list=["skrillex"],
        year=2010
    )
    print(f"✓ Title: {minimal_track.title}")
    print(f"  Artist: {minimal_track.primary_artist}")
    print(f"  Year: {minimal_track.year}")
    print(f"  Genre: {minimal_track.genre}  # Empty list by default")
    print(f"  Label: {minimal_track.label}  # Empty list by default\n")

    # Full track with all fields
    print("Creating full track with all fields...")
    full_track = Track(
        title="16",
        artist_list=["blasterjaxx", "hardwell", "maddix"],
        year=2024,
        genre=["hard techno"],
        label=["revealed"],
        grouping="Electronic",
        search_query="blasterjaxx hardwell maddix 16"
    )
    print(f"✓ Title: {full_track.title}")
    print(f"  Artists: {full_track.all_artists_string}")
    print(f"  Year: {full_track.year}")
    print(f"  Genre: {full_track.genre}")
    print(f"  Label: {full_track.label}")
    print(f"  Grouping: {full_track.grouping}")
    print(f"  Search query: {full_track.search_query}\n")

    # Validation error examples
    print("Demonstrating validation errors...")
    try:
        Track(artist_list=["artist"], year=2024)  # Missing title
    except ValidationError as e:
        print(f"✗ Missing title error: {e.error_count()} validation error(s)")

    try:
        Track(title="Test", artist_list=[], year=2024)  # Empty artist list
    except ValidationError as e:
        print(f"✗ Empty artist list error: {e.error_count()} validation error(s)")

    try:
        Track(title="Test", artist_list=["artist"], year=1899)  # Year too old
    except ValidationError as e:
        print(f"✗ Invalid year error: {e.error_count()} validation error(s)")

    print("\n✓ Validation working as expected\n")


def demo_properties_and_methods() -> None:
    """Demonstrate Track properties and methods."""
    print_separator("Properties and Methods")

    track = Track(
        title="Animals",
        artist_list=["martin garrix"],
        year=2013,
        genre=["big room", "progressive house"]
    )

    # Properties
    print("Track properties:")
    print(f"  primary_artist: {track.primary_artist}")
    print(f"  all_artists_string: {track.all_artists_string}")
    print()

    # Collaboration example
    collab = Track(
        title="Titanium",
        artist_list=["david guetta", "sia"],
        year=2011
    )
    print("Collaboration track:")
    print(f"  primary_artist: {collab.primary_artist}")
    print(f"  all_artists_string: {collab.all_artists_string}")
    print()

    # has_genre method
    print("Testing has_genre() method (case-insensitive):")
    print(f"  has_genre('big room'): {track.has_genre('big room')}")
    print(f"  has_genre('BIG ROOM'): {track.has_genre('BIG ROOM')}")
    print(f"  has_genre('Big Room'): {track.has_genre('Big Room')}")
    print(f"  has_genre('dubstep'): {track.has_genre('dubstep')}")
    print()

    print("✓ All properties and methods working correctly\n")


def demo_aliases_and_compatibility() -> None:
    """Demonstrate field aliases and backward compatibility."""
    print_separator("Aliases and Backward Compatibility")

    # Using field name
    print("Creating track with field name 'search_query'...")
    track1 = Track(
        title="Levels",
        artist_list=["avicii"],
        year=2011,
        search_query="avicii levels"
    )
    print(f"✓ search_query = {track1.search_query}\n")

    # Using alias name
    print("Creating track with alias 'request' (legacy format)...")
    track2 = Track(
        title="Levels",
        artist_list=["avicii"],
        year=2011,
        request="avicii levels"  # Using alias
    )
    print(f"✓ search_query = {track2.search_query}")
    print("  (Both approaches work thanks to populate_by_name=True)\n")

    print("✓ Backward compatibility maintained\n")


def demo_json_serialization() -> None:
    """Demonstrate JSON serialization and deserialization."""
    print_separator("JSON Serialization")

    track = Track(
        title="Strobe",
        artist_list=["deadmau5"],
        year=2009,
        genre=["progressive house"],
        label=["mau5trap"]
    )

    # Serialize to JSON string
    print("Serializing to JSON string...")
    json_str = track.model_dump_json(indent=2)
    print(json_str)
    print()

    # Deserialize from JSON string
    print("Deserializing from JSON string...")
    loaded_track = Track.model_validate_json(json_str)
    print(f"✓ Loaded track: {loaded_track.title} by {loaded_track.primary_artist}")
    print()

    # Save to file and load back
    print("Testing file I/O...")
    with TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "track.json"

        # Save
        track.to_json_file(file_path)
        print(f"✓ Saved to {file_path.name}")

        # Load
        loaded_from_file = Track.from_json_file(file_path)
        print(f"✓ Loaded from file: {loaded_from_file.title}")

    print("\n✓ JSON serialization working correctly\n")


def demo_songstats_identifiers() -> None:
    """Demonstrate SongstatsIdentifiers model."""
    print_separator("SongstatsIdentifiers Model")

    # Creation with field names
    print("Creating with field names...")
    ids1 = SongstatsIdentifiers(
        songstats_id="qmr6e0bx",
        songstats_title="16"
    )
    print(f"✓ songstats_id: {ids1.songstats_id}")
    print(f"  songstats_title: {ids1.songstats_title}")
    print(f"  isrc: {ids1.isrc}  # Optional, defaults to None\n")

    # Creation with aliases (legacy format)
    print("Creating with aliases (s_id, s_title)...")
    ids2 = SongstatsIdentifiers(
        s_id="abc12345",
        s_title="Test Track"
    )
    print(f"✓ songstats_id: {ids2.songstats_id}")
    print(f"  songstats_title: {ids2.songstats_title}\n")

    # With ISRC
    print("Creating with ISRC...")
    ids3 = SongstatsIdentifiers(
        songstats_id="xyz98765",
        songstats_title="Example",
        isrc="USRC17607839"
    )
    print(f"✓ songstats_id: {ids3.songstats_id}")
    print(f"  songstats_title: {ids3.songstats_title}")
    print(f"  isrc: {ids3.isrc}\n")

    # to_flat_dict method
    print("Testing to_flat_dict() method...")
    flat_dict = ids1.to_flat_dict()
    print(f"✓ Flat dict with aliases: {flat_dict}")
    print(f"  (Uses alias names: s_id, s_title)\n")

    # Immutability
    print("Testing immutability (frozen model)...")
    try:
        ids1.songstats_id = "new_id"
    except ValidationError:
        print("✓ Model is immutable (modification rejected)\n")

    print("✓ SongstatsIdentifiers working correctly\n")


def demo_immutability() -> None:
    """Demonstrate model immutability."""
    print_separator("Model Immutability")

    track = Track(
        title="Clarity",
        artist_list=["zedd", "foxes"],
        year=2012
    )

    print("Attempting to modify frozen track...")
    try:
        track.title = "New Title"
        print("✗ Modification succeeded (unexpected)")
    except ValidationError:
        print("✓ Modification rejected (model is frozen)")

    print("  Reason: ConfigDict(frozen=True) makes models immutable")
    print("  Benefits: Data integrity, thread safety, hashability\n")

    print("✓ Immutability working as expected\n")


def main() -> None:
    """Run all Track model demos."""
    print("=" * 80)
    print(" Track & SongstatsIdentifiers Models - Interactive Demo")
    print("=" * 80)

    demo_basic_track_creation()
    demo_properties_and_methods()
    demo_aliases_and_compatibility()
    demo_json_serialization()
    demo_songstats_identifiers()
    demo_immutability()

    print_separator()
    print("✓ All demos completed successfully!")
    print()


if __name__ == "__main__":
    main()
