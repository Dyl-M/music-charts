"""Standalone utility for managing YouTube video source coverage.

Tracks with fewer than 5 YouTube video sources are identified and can be
enhanced with manual additions. Also compares a curated YouTube playlist
against enriched track sources to find unmatched videos.

Usage:
    # Show coverage summary (default):
    python _scripts/manual_youtube_coverage.py

    # Generate/update coverage report:
    python _scripts/manual_youtube_coverage.py --generate

    # Submit new YouTube links to Songstats API:
    python _scripts/manual_youtube_coverage.py --submit

    # Interactively whitelist tracks (no more sources to add):
    python _scripts/manual_youtube_coverage.py --whitelist-tracks

    # Interactively whitelist playlist videos (not relevant):
    python _scripts/manual_youtube_coverage.py --whitelist-videos

    # Enable debug logging:
    python _scripts/manual_youtube_coverage.py --generate --debug

Input:
    - Enriched tracks: _data/output/enriched_tracks.json
    - Existing whitelist (optional): _data/input/youtube_whitelist.json

Output:
    - Coverage report: _data/input/youtube_coverage.json
    - Whitelist file: _data/input/youtube_whitelist.json
    - Log file: _data/logs/youtube_coverage.log
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
    display_submission_results,
    get_display_artist,
    load_enriched_tracks,
    resolve_input_path,
    setup_script_context,
    submit_links_to_songstats,
)

from msc.clients.songstats import SongstatsClient
from msc.clients.youtube import YouTubeClient
from msc.models.stats import TrackWithStats

# YouTube playlist ID to compare against enriched tracks
PLAYLIST_ID = "PLOMUdQFdS-XMfbJk0XdreFpdm2CRCGC-e"

# Minimum number of YouTube sources for a track to be "fully covered"
MIN_SOURCES = 5

# Default file names
COVERAGE_FILE = "youtube_coverage.json"
WHITELIST_FILE = "youtube_whitelist.json"
LOG_FILE = "youtube_coverage.log"


def create_empty_whitelist() -> dict[str, list[str]]:
    """Create empty whitelist structure.

    Returns:
        Dictionary with empty tracks and playlist_videos lists.
    """
    return {
        "tracks": [],
        "playlist_videos": [],
    }


def load_whitelist(whitelist_path: Path) -> dict[str, list[str]]:
    """Load YouTube whitelist from JSON file.

    Creates empty whitelist structure if file doesn't exist.

    Args:
        whitelist_path: Path to whitelist JSON file.

    Returns:
        Dictionary with 'tracks' and 'playlist_videos' lists.
    """
    if not whitelist_path.exists():
        return create_empty_whitelist()

    with open(whitelist_path, encoding="utf-8") as f:
        data = json.load(f)

    # Ensure required keys exist and deduplicate
    whitelist = create_empty_whitelist()

    if "tracks" in data and isinstance(data["tracks"], list):
        whitelist["tracks"] = list(set(data["tracks"]))

    if "playlist_videos" in data and isinstance(data["playlist_videos"], list):
        whitelist["playlist_videos"] = list(set(data["playlist_videos"]))

    return whitelist


def save_whitelist(whitelist: dict[str, list[str]], whitelist_path: Path) -> None:
    """Save whitelist to JSON file atomically.

    Args:
        whitelist: Whitelist dictionary to save.
        whitelist_path: Path to write whitelist file.
    """
    whitelist_path.parent.mkdir(parents=True, exist_ok=True)

    # Sort entries for consistent output
    sorted_whitelist = {
        "tracks": sorted(whitelist.get("tracks", [])),
        "playlist_videos": sorted(whitelist.get("playlist_videos", [])),
    }

    # Write atomically
    temp_file = whitelist_path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(sorted_whitelist, f, indent=2, ensure_ascii=False)

    temp_file.replace(whitelist_path)


def find_tracks_needing_sources(
        tracks: list[TrackWithStats],
        whitelist: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Find tracks with fewer than MIN_SOURCES YouTube video sources.

    Args:
        tracks: List of enriched tracks.
        whitelist: Current whitelist.

    Returns:
        List of track entries needing more sources.
    """
    needing_sources = []

    for track in tracks:
        track_id = track.identifier

        # Skip whitelisted tracks
        if track_id in whitelist.get("tracks", []):
            continue

        # Check if track has YouTube data
        if track.youtube_data is None:
            # No YouTube data at all - needs sources
            needing_sources.append({
                "track_id": track_id,
                "artist": get_display_artist(track),
                "title": track.track.title,
                "songstats_id": track.songstats_identifiers.songstats_id,
                "current_sources": [],
                "source_count": 0,
                "new_links": [],
            })
            continue

        # Check source count
        source_count = track.youtube_data.video_count

        if source_count < MIN_SOURCES:
            needing_sources.append({
                "track_id": track_id,
                "artist": get_display_artist(track),
                "title": track.track.title,
                "songstats_id": track.songstats_identifiers.songstats_id,
                "current_sources": list(track.youtube_data.all_sources),
                "source_count": source_count,
                "new_links": [],
            })

    # Sort by source count (ascending), then by artist/title
    needing_sources.sort(key=lambda x: (x["source_count"], x["artist"].lower(), x["title"].lower()))

    return needing_sources


def collect_all_track_video_ids(tracks: list[TrackWithStats]) -> set[str]:
    """Collect all YouTube video IDs from all enriched tracks.

    Args:
        tracks: List of enriched tracks.

    Returns:
        Set of all video IDs found in track sources.
    """
    all_ids = set()

    for track in tracks:
        if track.youtube_data is not None:
            all_ids.update(track.youtube_data.all_sources)

    return all_ids


def fetch_playlist_videos(
        logger: logging.Logger,
) -> list[dict[str, Any]]:
    """Fetch all videos from the curated YouTube playlist.

    Uses YouTube API to get video metadata including title, channel, and views.

    Args:
        logger: Logger instance.

    Returns:
        List of video dictionaries with metadata.
    """
    logger.info("Fetching playlist videos from YouTube API...")
    logger.info("Playlist ID: %s", PLAYLIST_ID)

    with YouTubeClient() as client:
        playlist_items = client.get_playlist_videos(PLAYLIST_ID)

    if not playlist_items:
        logger.warning("No videos found in playlist (or API error)")
        return []

    logger.info("Fetched %d videos from playlist", len(playlist_items))

    # Convert to our format
    videos = []

    for item in playlist_items:
        video_id = item.get("video_id")

        if not video_id:
            continue

        videos.append({
            "video_id": video_id,
            "title": item.get("title", "Unknown"),
            "channel_name": item.get("channel_name", "Unknown"),
            "position": item.get("position", 0),
        })

    return videos


def find_unmatched_playlist_videos(
        playlist_videos: list[dict[str, Any]],
        track_video_ids: set[str],
        whitelist: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Find playlist videos not present in any track's sources.

    Args:
        playlist_videos: Videos from the curated playlist.
        track_video_ids: Set of all video IDs from enriched tracks.
        whitelist: Current whitelist.

    Returns:
        List of unmatched video entries.
    """
    unmatched = []

    for video in playlist_videos:
        video_id = video["video_id"]

        # Skip if already in track sources
        if video_id in track_video_ids:
            continue

        # Skip if whitelisted
        if video_id in whitelist.get("playlist_videos", []):
            continue

        unmatched.append(video)

    # Sort by position in playlist
    unmatched.sort(key=lambda x: x.get("position", 0))

    return unmatched


def generate_coverage_report(
        tracks: list[TrackWithStats],
        whitelist: dict[str, list[str]],
        logger: logging.Logger,
) -> dict[str, Any]:
    """Generate YouTube coverage report.

    Args:
        tracks: List of enriched tracks.
        whitelist: Current whitelist.
        logger: Logger instance.

    Returns:
        Coverage report dictionary.
    """
    logger.info("Analyzing tracks for YouTube source coverage...")

    # Find tracks needing more sources
    tracks_needing = find_tracks_needing_sources(tracks, whitelist)
    logger.info("Found %d tracks with fewer than %d sources", len(tracks_needing), MIN_SOURCES)

    # Collect all video IDs from tracks
    track_video_ids = collect_all_track_video_ids(tracks)
    logger.info("Total unique video IDs across all tracks: %d", len(track_video_ids))

    # Fetch and compare playlist
    playlist_videos = fetch_playlist_videos(logger)
    unmatched_videos = find_unmatched_playlist_videos(playlist_videos, track_video_ids, whitelist)
    logger.info("Found %d unmatched playlist videos", len(unmatched_videos))

    return {
        "tracks_needing_sources": tracks_needing,
        "unmatched_playlist_videos": unmatched_videos,
    }


def save_coverage_report(
        coverage: dict[str, Any],
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


def load_coverage_report(coverage_path: Path) -> dict[str, Any]:
    """Load existing coverage report.

    Args:
        coverage_path: Path to coverage JSON file.

    Returns:
        Coverage report dictionary.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not coverage_path.exists():
        raise FileNotFoundError(f"Coverage file not found: {coverage_path}")

    with open(coverage_path, encoding="utf-8") as f:
        return json.load(f)


def display_coverage_summary(
        coverage: dict[str, Any],
        whitelist: dict[str, list[str]],
        logger: logging.Logger,
) -> None:
    """Display coverage status summary.

    Args:
        coverage: Coverage report.
        whitelist: Current whitelist.
        logger: Logger instance.
    """
    tracks_needing = coverage.get("tracks_needing_sources", [])
    unmatched_videos = coverage.get("unmatched_playlist_videos", [])

    logger.info("")
    logger.info("YouTube Coverage Status:")
    logger.info("-" * 50)
    logger.info("%-30s %10s", "Category", "Count")
    logger.info("-" * 50)
    logger.info("%-30s %10d", "Tracks needing sources (<5)", len(tracks_needing))
    logger.info("%-30s %10d", "Unmatched playlist videos", len(unmatched_videos))
    logger.info("%-30s %10d", "Whitelisted tracks", len(whitelist.get("tracks", [])))
    logger.info("%-30s %10d", "Whitelisted playlist videos", len(whitelist.get("playlist_videos", [])))
    logger.info("-" * 50)


def display_tracks_needing_sources(
        coverage: dict[str, Any],
        logger: logging.Logger,
        max_tracks: int = 10,
) -> None:
    """Display tracks that need more YouTube sources.

    Args:
        coverage: Coverage report.
        logger: Logger instance.
        max_tracks: Maximum tracks to show.
    """
    tracks = coverage.get("tracks_needing_sources", [])

    if not tracks:
        logger.info("")
        logger.info("All tracks have at least %d YouTube sources!", MIN_SOURCES)
        return

    logger.info("")
    logger.info("Tracks Needing More Sources (first %d):", max_tracks)

    for track in tracks[:max_tracks]:
        logger.info(
            "  [%d sources] %s - %s",
            track["source_count"],
            track["artist"],
            track["title"],
        )

    if len(tracks) > max_tracks:
        logger.info("  ... and %d more", len(tracks) - max_tracks)


def display_unmatched_videos(
        coverage: dict[str, Any],
        logger: logging.Logger,
        max_videos: int = 10,
) -> None:
    """Display unmatched playlist videos.

    Args:
        coverage: Coverage report.
        logger: Logger instance.
        max_videos: Maximum videos to show.
    """
    videos = coverage.get("unmatched_playlist_videos", [])

    if not videos:
        logger.info("")
        logger.info("All playlist videos are matched to tracks!")
        return

    logger.info("")
    logger.info("Unmatched Playlist Videos (first %d):", max_videos)

    for video in videos[:max_videos]:
        logger.info(
            "  [%s] %s",
            video["channel_name"],
            video["title"],
        )

    if len(videos) > max_videos:
        logger.info("  ... and %d more", len(videos) - max_videos)


def get_pending_link_submissions(
        coverage: dict[str, Any],
) -> list[dict[str, Any]]:
    """Get tracks with new_links filled in ready for submission.

    Args:
        coverage: Coverage report dictionary.

    Returns:
        List of submission entries.
    """
    pending = []

    for track in coverage.get("tracks_needing_sources", []):
        links = track.get("new_links", [])

        # Handle both list and string format
        if isinstance(links, str):
            links = [links] if links else []

        # Skip if no links filled
        if not links:
            continue

        for link in links:
            if link and link.strip():
                pending.append({
                    "track_id": track.get("track_id", ""),
                    "artist": track.get("artist", "Unknown"),
                    "title": track.get("title", "Unknown"),
                    "songstats_id": track.get("songstats_id", ""),
                    "link": link.strip(),
                })

    return pending


def whitelist_tracks_interactive(
        whitelist: dict[str, list[str]],
        coverage: dict[str, Any],
        logger: logging.Logger,
) -> dict[str, list[str]]:
    """Interactively add tracks to whitelist.

    Shows tracks needing sources and allows user to mark them
    as whitelisted (no more sources can be added).

    Args:
        whitelist: Current whitelist.
        coverage: Current coverage report.
        logger: Logger instance.

    Returns:
        Updated whitelist.
    """
    tracks = coverage.get("tracks_needing_sources", [])

    if not tracks:
        logger.info("No tracks needing sources to whitelist.")
        return whitelist

    logger.info("")
    logger.info("Interactive Track Whitelist Mode")
    logger.info("Mark tracks as 'no more sources available' to exclude from reports.")
    logger.info("")
    logger.info("Commands:")
    logger.info("  [number]  - Add track by number to whitelist")
    logger.info("  a         - Add all displayed tracks to whitelist")
    logger.info("  q         - Quit and save")
    logger.info("")

    updated_whitelist = {
        "tracks": list(whitelist.get("tracks", [])),
        "playlist_videos": list(whitelist.get("playlist_videos", [])),
    }
    added_count = 0

    logger.info("=" * 60)
    logger.info("Tracks Needing Sources (%d total)", len(tracks))
    logger.info("=" * 60)

    # Display tracks with numbers
    for idx, track in enumerate(tracks, 1):
        logger.info(
            "%3d. [%d sources] %s - %s",
            idx,
            track["source_count"],
            track["artist"],
            track["title"],
        )

    logger.info("")

    while True:
        try:
            user_input = input("Enter command: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            logger.info("")
            logger.info("Interrupted. Saving progress...")
            return updated_whitelist

        if user_input == "q":
            logger.info("Quitting. Saving progress...")
            return updated_whitelist

        if user_input == "a":
            # Add all tracks
            for track in tracks:
                if track["track_id"] not in updated_whitelist["tracks"]:
                    updated_whitelist["tracks"].append(track["track_id"])
                    added_count += 1

            logger.info("Added all %d tracks to whitelist", len(tracks))
            break

        # Try to parse as number
        try:
            num = int(user_input)

            if 1 <= num <= len(tracks):
                track = tracks[num - 1]

                if track["track_id"] not in updated_whitelist["tracks"]:
                    updated_whitelist["tracks"].append(track["track_id"])
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


def whitelist_videos_interactive(
        whitelist: dict[str, list[str]],
        coverage: dict[str, Any],
        logger: logging.Logger,
) -> dict[str, list[str]]:
    """Interactively add playlist videos to whitelist.

    Shows unmatched playlist videos and allows user to mark them
    as whitelisted (not relevant to power ranking).

    Args:
        whitelist: Current whitelist.
        coverage: Current coverage report.
        logger: Logger instance.

    Returns:
        Updated whitelist.
    """
    videos = coverage.get("unmatched_playlist_videos", [])

    if not videos:
        logger.info("No unmatched playlist videos to whitelist.")
        return whitelist

    logger.info("")
    logger.info("Interactive Playlist Video Whitelist Mode")
    logger.info("Mark videos as 'not relevant to power ranking' to exclude from reports.")
    logger.info("")
    logger.info("Commands:")
    logger.info("  [number]  - Add video by number to whitelist")
    logger.info("  a         - Add all displayed videos to whitelist")
    logger.info("  q         - Quit and save")
    logger.info("")

    updated_whitelist = {
        "tracks": list(whitelist.get("tracks", [])),
        "playlist_videos": list(whitelist.get("playlist_videos", [])),
    }
    added_count = 0

    logger.info("=" * 60)
    logger.info("Unmatched Playlist Videos (%d total)", len(videos))
    logger.info("=" * 60)

    # Display videos with numbers
    for idx, video in enumerate(videos, 1):
        logger.info(
            "%3d. [%s] %s",
            idx,
            video["channel_name"],
            video["title"],
        )
        logger.info("     https://youtube.com/watch?v=%s", video["video_id"])

    logger.info("")

    while True:
        try:
            user_input = input("Enter command: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            logger.info("")
            logger.info("Interrupted. Saving progress...")
            return updated_whitelist

        if user_input == "q":
            logger.info("Quitting. Saving progress...")
            return updated_whitelist

        if user_input == "a":
            # Add all videos
            for video in videos:
                if video["video_id"] not in updated_whitelist["playlist_videos"]:
                    updated_whitelist["playlist_videos"].append(video["video_id"])
                    added_count += 1

            logger.info("Added all %d videos to whitelist", len(videos))
            break

        # Try to parse as number
        try:
            num = int(user_input)

            if 1 <= num <= len(videos):
                video = videos[num - 1]

                if video["video_id"] not in updated_whitelist["playlist_videos"]:
                    updated_whitelist["playlist_videos"].append(video["video_id"])
                    added_count += 1
                    logger.info("Added: %s", video["title"])
                else:
                    logger.info("Already whitelisted: %s", video["title"])

            else:
                logger.warning("Invalid number. Enter 1-%d", len(videos))

        except ValueError:
            logger.warning("Unknown command: %s", user_input)

    logger.info("")
    logger.info("Total videos added to whitelist: %d", added_count)

    return updated_whitelist


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Manage YouTube video source coverage for enriched tracks.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)             Show coverage summary
  --generate            Create/update youtube_coverage.json from enriched tracks
  --submit              Submit new YouTube links to Songstats API
  --whitelist-tracks    Interactively whitelist tracks (no more sources)
  --whitelist-videos    Interactively whitelist playlist videos (not relevant)

Examples:
  python _scripts/manual_youtube_coverage.py
  python _scripts/manual_youtube_coverage.py --generate
  python _scripts/manual_youtube_coverage.py --submit
  python _scripts/manual_youtube_coverage.py --whitelist-tracks
  python _scripts/manual_youtube_coverage.py --whitelist-videos
  python _scripts/manual_youtube_coverage.py --generate --debug
""",
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate/update coverage report from enriched tracks",
    )

    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit new YouTube links to Songstats API",
    )

    parser.add_argument(
        "--whitelist-tracks",
        action="store_true",
        help="Interactively add tracks to whitelist",
    )

    parser.add_argument(
        "--whitelist-videos",
        action="store_true",
        help="Interactively add playlist videos to whitelist",
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
    """Main entry point for YouTube coverage utility."""
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
            logger.info("Generate YouTube Coverage Report Mode")
            logger.info("=" * 60)

            logger.info("Loading enriched tracks from: %s", stats_path)
            tracks = load_enriched_tracks(stats_path, logger)

            if not tracks:
                logger.warning("No enriched tracks found")
                sys.exit(0)

            logger.info("Loaded %d enriched tracks", len(tracks))
            logger.info("")

            coverage = generate_coverage_report(tracks, whitelist, logger)

            save_coverage_report(coverage, coverage_path)
            logger.info("")
            logger.info("Coverage report saved to: %s", coverage_path)

            display_coverage_summary(coverage, whitelist, logger)
            display_tracks_needing_sources(coverage, logger)
            display_unmatched_videos(coverage, logger)

            logger.info("")
            logger.info("Next steps:")
            logger.info("  1. Open %s", coverage_path.name)
            logger.info("  2. Fill in 'new_links' field for tracks needing sources")
            logger.info("  3. Run --submit to submit links to Songstats API")
            logger.info("  4. Run --whitelist-tracks to mark tracks as fully covered")
            logger.info("  5. Run --whitelist-videos to mark irrelevant playlist videos")

        elif args.submit:
            # Submit mode
            logger.info("=" * 60)
            logger.info("YouTube Link Submission Mode")
            logger.info("=" * 60)

            coverage = load_coverage_report(coverage_path)
            pending = get_pending_link_submissions(coverage)

            if not pending:
                logger.info("")
                logger.info("No pending YouTube link submissions found.")
                logger.info("")
                logger.info("To add links:")
                logger.info("  1. Open %s", coverage_path.name)
                logger.info("  2. Fill in 'new_links' field for tracks")
                logger.info("  3. Run this script again with --submit")
                sys.exit(0)

            logger.info("Found %d pending submissions", len(pending))
            logger.info("")

            with SongstatsClient() as client:
                results = submit_links_to_songstats(client, pending, logger, "YouTube")

            display_submission_results(results, logger)

        elif args.whitelist_tracks:
            # Whitelist tracks mode
            logger.info("=" * 60)
            logger.info("Whitelist Tracks Mode")
            logger.info("=" * 60)

            # Load existing coverage or generate fresh
            if coverage_path.exists():
                logger.info("Loading existing coverage from: %s", coverage_path)
                coverage = load_coverage_report(coverage_path)

            else:
                logger.info("No coverage report found. Generating from enriched tracks...")
                tracks = load_enriched_tracks(stats_path, logger)

                if not tracks:
                    logger.warning("No enriched tracks found")
                    sys.exit(0)

                coverage = generate_coverage_report(tracks, whitelist, logger)

            updated_whitelist = whitelist_tracks_interactive(whitelist, coverage, logger)
            save_whitelist(updated_whitelist, whitelist_path)

            logger.info("")
            logger.info("Whitelist saved to: %s", whitelist_path)
            logger.info("Run --generate to update coverage report with new whitelist")

        elif args.whitelist_videos:
            # Whitelist videos mode
            logger.info("=" * 60)
            logger.info("Whitelist Playlist Videos Mode")
            logger.info("=" * 60)

            # Load existing coverage or generate fresh
            if coverage_path.exists():
                logger.info("Loading existing coverage from: %s", coverage_path)
                coverage = load_coverage_report(coverage_path)

            else:
                logger.info("No coverage report found. Generating from enriched tracks...")
                tracks = load_enriched_tracks(stats_path, logger)

                if not tracks:
                    logger.warning("No enriched tracks found")
                    sys.exit(0)

                coverage = generate_coverage_report(tracks, whitelist, logger)

            updated_whitelist = whitelist_videos_interactive(whitelist, coverage, logger)
            save_whitelist(updated_whitelist, whitelist_path)

            logger.info("")
            logger.info("Whitelist saved to: %s", whitelist_path)
            logger.info("Run --generate to update coverage report with new whitelist")

        else:
            # Default: show summary
            logger.info("=" * 60)
            logger.info("YouTube Coverage Summary")
            logger.info("=" * 60)

            if coverage_path.exists():
                coverage = load_coverage_report(coverage_path)

                display_coverage_summary(coverage, whitelist, logger)
                display_tracks_needing_sources(coverage, logger)
                display_unmatched_videos(coverage, logger)

            else:
                logger.warning("No coverage report found.")
                logger.info("Run with --generate first to create the coverage report:")
                logger.info("  python _scripts/manual_youtube_coverage.py --generate")

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
