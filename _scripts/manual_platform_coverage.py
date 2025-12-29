"""Standalone utility for managing platform coverage of enriched tracks.

Generates coverage reports showing which tracks are missing from which platforms,
and maintains a whitelist for tracks confirmed as genuinely unavailable.

Usage:
    # Show coverage summary (default):
    python _scripts/manual_platform_coverage.py

    # Generate/update platform coverage from enriched tracks:
    python _scripts/manual_platform_coverage.py --generate

    # Add tracks to whitelist interactively:
    python _scripts/manual_platform_coverage.py --add-to-whitelist

    # With debug logging:
    python _scripts/manual_platform_coverage.py --generate --debug

Input:
    - Enriched tracks: _data/output/enriched_tracks.json
    - Existing whitelist (optional): _data/input/platform_whitelist.json

Output:
    - Coverage report: _data/input/platform_coverage.json
    - Whitelist file: _data/input/platform_whitelist.json
    - Log file: _data/logs/platform_coverage.log
"""

# Standard library
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local imports (reuse existing components)
# ruff: noqa: E402
from _shared import (
    get_display_artist,
    load_enriched_tracks,
    resolve_input_path,
    setup_script_context,
)

from msc.models.stats import TrackWithStats

# Platform names matching PlatformStats model field names
# Note: TikTok excluded - too difficult for manual additions
PLATFORMS: tuple[str, ...] = (
    "spotify",
    "apple_music",
    "deezer",
    "youtube",
    "soundcloud",
    "tidal",
    "amazon_music",
    "beatport",
    "tracklists",
)

# Display names for better readability
PLATFORM_DISPLAY_NAMES: dict[str, str] = {
    "spotify": "Spotify",
    "apple_music": "Apple Music",
    "deezer": "Deezer",
    "youtube": "YouTube",
    "soundcloud": "SoundCloud",
    "tidal": "Tidal",
    "amazon_music": "Amazon Music",
    "beatport": "Beatport",
    "tracklists": "1001Tracklists",
}

# Default file names
COVERAGE_FILE = "platform_coverage.json"
WHITELIST_FILE = "platform_whitelist.json"
LOG_FILE = "platform_coverage.log"


def is_platform_missing(track: TrackWithStats, platform: str) -> bool:
    """Check if a track is missing from a specific platform.

    A platform is considered "missing" if ALL fields in that platform's
    stats model are None. This distinguishes between:
    - Track not on platform (all None) -> True (missing)
    - Track on platform with 0 stats (has values, even if 0) -> False (present)

    Args:
        track: TrackWithStats instance to check.
        platform: Platform name (e.g., "spotify", "apple_music").

    Returns:
        True if track is missing from platform, False if present.

    Raises:
        ValueError: If platform name is invalid.
    """
    if platform not in PLATFORMS:
        raise ValueError(f"Invalid platform: {platform}")

    platform_stats = getattr(track.platform_stats, platform)
    non_none_fields = platform_stats.model_dump(exclude_none=True)
    return len(non_none_fields) == 0


def create_empty_whitelist() -> dict[str, list[str]]:
    """Create empty whitelist structure with all platforms.

    Returns:
        Dictionary mapping platform names to empty lists.
    """
    return {platform: [] for platform in PLATFORMS}


def load_whitelist(whitelist_path: Path) -> dict[str, list[str]]:
    """Load platform whitelist from JSON file.

    Creates empty whitelist structure if file doesn't exist.

    Args:
        whitelist_path: Path to whitelist JSON file.

    Returns:
        Dictionary mapping platform names to lists of whitelisted track IDs.
    """
    if not whitelist_path.exists():
        return create_empty_whitelist()

    with open(whitelist_path, encoding="utf-8") as f:
        data = json.load(f)

    # Ensure all platforms exist in loaded data
    whitelist = create_empty_whitelist()

    for platform in PLATFORMS:
        if platform in data and isinstance(data[platform], list):
            # Deduplicate entries
            whitelist[platform] = list(set(data[platform]))

    return whitelist


def save_whitelist(whitelist: dict[str, list[str]], whitelist_path: Path) -> None:
    """Save whitelist to JSON file atomically.

    Args:
        whitelist: Whitelist dictionary to save.
        whitelist_path: Path to write whitelist file.
    """
    whitelist_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort entries for consistent output
    sorted_whitelist = {platform: sorted(ids) for platform, ids in whitelist.items()}

    # Write atomically
    temp_file = whitelist_path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(sorted_whitelist, f, indent=2, ensure_ascii=False)

    temp_file.replace(whitelist_path)


def generate_coverage_report(
        tracks: list[TrackWithStats],
        whitelist: dict[str, list[str]],
) -> dict[str, list[dict[str, Any]]]:
    """Generate platform coverage report.

    For each platform, finds tracks where:
    1. All platform stats fields are None (track missing from platform)
    2. Track is NOT in the platform's whitelist

    Args:
        tracks: List of enriched tracks.
        whitelist: Platform whitelist.

    Returns:
        Coverage report dictionary with structure:
        {"platform": [{"track_id": "...", "artist": "...", ...}]}

    Note:
        All platforms use a list for "link" field to support multiple sources per track.
    """
    coverage: dict[str, list[dict[str, Any]]] = {platform: [] for platform in PLATFORMS}

    for track in tracks:
        track_id = track.identifier

        for platform in PLATFORMS:
            # Skip if track is whitelisted for this platform
            if track_id in whitelist.get(platform, []):
                continue

            # Check if track is missing from this platform
            if is_platform_missing(track, platform):
                coverage[platform].append({
                    "track_id": track_id,
                    "artist": get_display_artist(track),
                    "title": track.track.title,
                    "songstats_id": track.songstats_identifiers.songstats_id,
                    "link": [],  # List to support multiple sources per track
                })

    # Sort each platform's tracks by artist then title
    for platform in PLATFORMS:
        coverage[platform].sort(key=lambda x: (x["artist"].lower(), x["title"].lower()))

    return coverage


def save_coverage_report(
        coverage: dict[str, list[dict[str, str]]],
        output_path: Path,
) -> None:
    """Save coverage report to JSON file.

    Args:
        coverage: Coverage report dictionary.
        output_path: Path to write coverage file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically
    temp_file = output_path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(coverage, f, indent=2, ensure_ascii=False)

    temp_file.replace(output_path)


def display_coverage_summary(
        coverage: dict[str, list[dict[str, str]]],
        whitelist: dict[str, list[str]],
        logger: logging.Logger,
) -> None:
    """Display coverage status summary.

    Shows for each platform:
    - Number of tracks missing
    - Number of tracks whitelisted

    Args:
        coverage: Coverage report.
        whitelist: Platform whitelist.
        logger: Logger instance.
    """
    logger.info("")
    logger.info("Platform Coverage Status:")
    logger.info("-" * 50)
    logger.info("%-15s %10s %12s", "Platform", "Missing", "Whitelisted")
    logger.info("-" * 50)

    total_missing = 0
    total_whitelisted = 0

    for platform in PLATFORMS:
        missing_count = len(coverage.get(platform, []))
        whitelisted_count = len(whitelist.get(platform, []))

        total_missing += missing_count
        total_whitelisted += whitelisted_count

        display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
        logger.info("%-15s %10d %12d", display_name, missing_count, whitelisted_count)

    logger.info("-" * 50)
    logger.info("%-15s %10d %12d", "TOTAL", total_missing, total_whitelisted)


def display_platform_details(
        coverage: dict[str, list[dict[str, str]]],
        logger: logging.Logger,
        max_tracks: int = 5,
) -> None:
    """Display detailed missing tracks per platform.

    Args:
        coverage: Coverage report.
        logger: Logger instance.
        max_tracks: Maximum tracks to show per platform.
    """
    logger.info("")
    logger.info("Missing Tracks by Platform (first %d per platform):", max_tracks)

    for platform in PLATFORMS:
        tracks = coverage.get(platform, [])

        if not tracks:
            continue

        display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
        logger.info("")
        logger.info("%s (%d missing):", display_name, len(tracks))

        for track in tracks[:max_tracks]:
            logger.info("  - %s - %s", track["artist"], track["title"])

        if len(tracks) > max_tracks:
            logger.info("  ... and %d more", len(tracks) - max_tracks)


def add_to_whitelist_interactive(
        whitelist: dict[str, list[str]],
        coverage: dict[str, list[dict[str, str]]],
        logger: logging.Logger,
) -> dict[str, list[str]]:
    """Interactively add tracks to whitelist.

    Shows tracks missing from each platform and allows user to mark them
    as whitelisted (confirmed not available on that platform).

    Args:
        whitelist: Current whitelist.
        coverage: Current coverage report.
        logger: Logger instance.

    Returns:
        Updated whitelist.
    """
    logger.info("")
    logger.info("Interactive Whitelist Mode")
    logger.info("Mark tracks as 'confirmed not on platform' to exclude from future reports.")
    logger.info("")
    logger.info("Commands:")
    logger.info("  [number]  - Add track by number to whitelist")
    logger.info("  a         - Add all displayed tracks to whitelist")
    logger.info("  s         - Skip to next platform")
    logger.info("  q         - Quit and save")
    logger.info("")

    updated_whitelist = {p: list(ids) for p, ids in whitelist.items()}
    added_count = 0

    for platform in PLATFORMS:
        tracks = coverage.get(platform, [])

        if not tracks:
            continue

        display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)
        logger.info("")
        logger.info("=" * 60)
        logger.info("%s - %d tracks missing", display_name, len(tracks))
        logger.info("=" * 60)

        # Display tracks with numbers
        for idx, track in enumerate(tracks, 1):
            logger.info("%3d. %s - %s", idx, track["artist"], track["title"])

        logger.info("")

        while True:
            try:
                user_input = input(f"[{display_name}] Enter command: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                logger.info("")
                logger.info("Interrupted. Saving progress...")
                return updated_whitelist

            if user_input == "q":
                logger.info("Quitting. Saving progress...")
                return updated_whitelist

            if user_input == "s":
                logger.info("Skipping %s", display_name)
                break

            if user_input == "a":
                # Add all tracks
                for track in tracks:
                    if track["track_id"] not in updated_whitelist[platform]:
                        updated_whitelist[platform].append(track["track_id"])
                        added_count += 1

                logger.info("Added all %d tracks to %s whitelist", len(tracks), display_name)
                break

            # Try to parse as number
            try:
                num = int(user_input)

                if 1 <= num <= len(tracks):
                    track = tracks[num - 1]

                    if track["track_id"] not in updated_whitelist[platform]:
                        updated_whitelist[platform].append(track["track_id"])
                        added_count += 1
                        logger.info("Added: %s - %s", track["artist"], track["title"])
                    else:
                        logger.info("Already whitelisted: %s - %s", track["artist"], track["title"])

                else:
                    logger.warning("Invalid number. Enter 1-%d", len(tracks))

            except ValueError:
                logger.warning("Unknown command: %s", user_input)

    logger.info("")
    logger.info("Total tracks added to whitelist: %d", added_count)

    return updated_whitelist


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Manage platform coverage for enriched tracks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)           Show coverage summary
  --generate          Create/update platform_coverage.json from enriched tracks
  --add-to-whitelist  Interactively add tracks to platform whitelist

Examples:
  python _scripts/manual_platform_coverage.py
  python _scripts/manual_platform_coverage.py --generate
  python _scripts/manual_platform_coverage.py --add-to-whitelist
  python _scripts/manual_platform_coverage.py --generate --debug
""",
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate/update coverage report from enriched tracks",
    )

    parser.add_argument(
        "--add-to-whitelist",
        action="store_true",
        help="Interactively add tracks to platform whitelist",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to enriched_tracks.json (default: _data/output/enriched_tracks.json)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for platform coverage utility."""
    args = parse_args()

    # Initialize common context
    ctx = setup_script_context(args, LOG_FILE)
    logger = ctx.logger

    # Paths
    coverage_path = ctx.input_dir / COVERAGE_FILE
    whitelist_path = ctx.input_dir / WHITELIST_FILE
    stats_path = resolve_input_path(args, ctx.settings)

    # Load whitelist
    whitelist = load_whitelist(whitelist_path)

    try:
        if args.generate:
            # Generate mode
            logger.info("=" * 60)
            logger.info("Generate Coverage Report Mode")
            logger.info("=" * 60)

            logger.info("Loading enriched tracks from: %s", stats_path)
            tracks = load_enriched_tracks(stats_path, logger)

            if not tracks:
                logger.warning("No enriched tracks found")
                sys.exit(0)

            logger.info("Loaded %d enriched tracks", len(tracks))
            logger.info("")

            logger.info("Generating coverage report...")
            coverage = generate_coverage_report(tracks, whitelist)

            save_coverage_report(coverage, coverage_path)
            logger.info("Coverage report saved to: %s", coverage_path)

            display_coverage_summary(coverage, whitelist, logger)
            display_platform_details(coverage, logger)

            logger.info("")
            logger.info("Next steps:")
            logger.info("  1. Open %s", coverage_path.name)
            logger.info("  2. Fill in 'link' field for tracks you find on each platform")
            logger.info("  3. Run --add-to-whitelist to mark tracks as 'not on platform'")

        elif args.add_to_whitelist:
            # Whitelist mode
            logger.info("=" * 60)
            logger.info("Add to Whitelist Mode")
            logger.info("=" * 60)

            # Load existing coverage or generate fresh
            if coverage_path.exists():
                logger.info("Loading existing coverage from: %s", coverage_path)

                with open(coverage_path, encoding="utf-8") as f:
                    coverage = json.load(f)

            else:
                logger.info("No coverage report found. Generating from enriched tracks...")
                tracks = load_enriched_tracks(stats_path, logger)

                if not tracks:
                    logger.warning("No enriched tracks found")
                    sys.exit(0)

                coverage = generate_coverage_report(tracks, whitelist)

            updated_whitelist = add_to_whitelist_interactive(whitelist, coverage, logger)
            save_whitelist(updated_whitelist, whitelist_path)

            logger.info("")
            logger.info("Whitelist saved to: %s", whitelist_path)
            logger.info("Run --generate to update coverage report with new whitelist")

        else:
            # Default: show summary
            logger.info("=" * 60)
            logger.info("Platform Coverage Summary")
            logger.info("=" * 60)

            if coverage_path.exists():
                with open(coverage_path, encoding="utf-8") as f:
                    coverage = json.load(f)

                display_coverage_summary(coverage, whitelist, logger)
                display_platform_details(coverage, logger)

            else:
                logger.warning("No coverage report found.")
                logger.info("Run with --generate first to create the coverage report:")
                logger.info("  python _scripts/manual_platform_coverage.py --generate")

        logger.info("")
        logger.info("Log file: %s", ctx.log_file)

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        logger.info("Run the pipeline first: msc run --year 2025")
        sys.exit(1)

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", e)
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
