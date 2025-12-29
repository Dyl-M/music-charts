"""Standalone utility for submitting platform links to Songstats API.

Reads filled links from platform_coverage.json and submits them to the
Songstats track_link_request endpoint.

Usage:
    # Show pending submissions (default):
    python _scripts/manual_link_submission.py

    # Submit all pending links:
    python _scripts/manual_link_submission.py --submit

    # Submit links for specific platform only:
    python _scripts/manual_link_submission.py --submit --platform soundcloud

    # Enable debug logging:
    python _scripts/manual_link_submission.py --submit --debug

Input:
    - Coverage file: _data/input/platform_coverage.json

Output:
    - Log file: _data/logs/link_submissions.log
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
from _shared import display_submission_results, submit_links_to_songstats

from msc.clients.songstats import SongstatsClient
from msc.config.settings import get_settings
from msc.utils.logging import LogLevel, get_logger, setup_logging

# Platforms supported for link submission
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
LOG_FILE = "link_submissions.log"


def load_coverage(coverage_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Load platform coverage from JSON file.

    Args:
        coverage_path: Path to platform_coverage.json.

    Returns:
        Coverage dictionary with platform keys.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not coverage_path.exists():
        raise FileNotFoundError(f"Coverage file not found: {coverage_path}")

    with open(coverage_path, encoding="utf-8") as f:
        return json.load(f)


def get_pending_submissions(
        coverage: dict[str, list[dict[str, Any]]],
        platform_filter: str | None = None,
) -> list[dict[str, Any]]:
    """Get tracks with filled links ready for submission.

    Args:
        coverage: Coverage dictionary from platform_coverage.json.
        platform_filter: Optional platform to filter by.

    Returns:
        List of submission entries with platform, track info, and links.
    """
    pending = []

    platforms = [platform_filter] if platform_filter else PLATFORMS

    for platform in platforms:
        if platform not in coverage:
            continue

        for track in coverage[platform]:
            links = track.get("link", [])

            # Handle both list and string format
            if isinstance(links, str):
                links = [links] if links else []

            # Skip if no links filled
            if not links:
                continue

            for link in links:
                if link and link.strip():
                    pending.append({
                        "platform": platform,
                        "track_id": track.get("track_id", ""),
                        "artist": track.get("artist", "Unknown"),
                        "title": track.get("title", "Unknown"),
                        "songstats_id": track.get("songstats_id", ""),
                        "link": link.strip(),
                    })

    return pending


def display_pending_summary(
        pending: list[dict[str, Any]],
        logger: logging.Logger,
) -> None:
    """Display summary of pending submissions by platform.

    Args:
        pending: List of pending submissions.
        logger: Logger instance.
    """
    # Group by platform
    by_platform: dict[str, list[dict[str, Any]]] = {}

    for entry in pending:
        platform = entry["platform"]
        if platform not in by_platform:
            by_platform[platform] = []
        by_platform[platform].append(entry)

    logger.info("")
    logger.info("Pending Link Submissions:")
    logger.info("-" * 60)

    total = 0

    for platform in PLATFORMS:
        if platform not in by_platform:
            continue

        entries = by_platform[platform]
        total += len(entries)
        display_name = PLATFORM_DISPLAY_NAMES.get(platform, platform)

        logger.info("")
        logger.info("%s (%d links):", display_name, len(entries))

        for entry in entries[:5]:
            logger.info("  - %s - %s", entry["artist"], entry["title"])
            logger.info("    %s", entry["link"])

        if len(entries) > 5:
            logger.info("  ... and %d more", len(entries) - 5)

    logger.info("")
    logger.info("-" * 60)
    logger.info("Total pending: %d links", total)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Submit platform links to Songstats API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modes:
  (default)   Show pending submissions
  --submit    Submit all pending links to Songstats API

Examples:
  python _scripts/manual_link_submission.py
  python _scripts/manual_link_submission.py --submit
  python _scripts/manual_link_submission.py --submit --platform soundcloud
  python _scripts/manual_link_submission.py --submit --debug
""",
    )

    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit pending links to Songstats API",
    )

    parser.add_argument(
        "--platform",
        type=str,
        choices=list(PLATFORMS),
        default=None,
        help="Filter by specific platform",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (shows API responses)",
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to platform_coverage.json (default: _data/input/platform_coverage.json)",
    )

    return parser.parse_args()


def main() -> None:
    """Main entry point for link submission utility."""
    args = parse_args()

    settings = get_settings()
    log_file = settings.data_dir / "logs" / LOG_FILE

    log_level: LogLevel = "DEBUG" if args.debug else "INFO"

    setup_logging(
        level=log_level,
        console_level=log_level,
        log_file=log_file,
    )

    logger = get_logger(__name__)

    # Determine coverage file path
    if args.input:
        coverage_path = args.input

        if not coverage_path.is_absolute():
            coverage_path = PROJECT_ROOT / coverage_path

    else:
        coverage_path = settings.data_dir / "input" / COVERAGE_FILE

    try:
        logger.info("=" * 60)

        if args.submit:
            logger.info("Link Submission Mode")
        else:
            logger.info("Pending Submissions Preview")

        logger.info("=" * 60)

        logger.info("Loading coverage from: %s", coverage_path)
        coverage = load_coverage(coverage_path)

        pending = get_pending_submissions(coverage, args.platform)

        if not pending:
            logger.info("")
            logger.info("No pending submissions found.")

            if args.platform:
                logger.info("Platform filter: %s", args.platform)

            logger.info("")
            logger.info("To add links:")
            logger.info("  1. Open %s", coverage_path.name)
            logger.info("  2. Fill in 'link' field for tracks")
            logger.info("  3. Run this script again")
            sys.exit(0)

        if args.submit:
            # Submit mode
            logger.info("Found %d pending submissions", len(pending))

            if args.platform:
                logger.info("Platform filter: %s", args.platform)

            logger.info("")

            with SongstatsClient() as client:
                results = submit_links_to_songstats(client, pending, logger)

            display_submission_results(results, logger)

        else:
            # Preview mode (default)
            display_pending_summary(pending, logger)

            logger.info("")
            logger.info("To submit these links, run:")
            logger.info("  python _scripts/manual_link_submission.py --submit")

        logger.info("")
        logger.info("Log file: %s", log_file)

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        logger.info("Run platform coverage first:")
        logger.info("  python _scripts/manual_platform_coverage.py --generate")
        sys.exit(1)

    except json.JSONDecodeError as e:
        logger.error("Invalid JSON: %s", e)
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
