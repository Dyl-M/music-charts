"""Shared utilities for standalone scripts in _scripts/.

Provides common functions used across multiple manual utility scripts to
avoid code duplication.

Usage:
    from _shared import load_enriched_tracks, get_display_artist, setup_script_context
"""

# Standard library
import argparse
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from time import sleep
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local imports (reuse existing components)
# ruff: noqa: E402
from msc.clients.songstats import SongstatsClient
from msc.config.settings import Settings, get_settings
from msc.models.stats import TrackWithStats
from msc.utils.logging import LogLevel, get_logger, setup_logging
from msc.utils.path_utils import validate_path_within_base


@dataclass
class ScriptContext:
    """Context object containing common script initialization results."""

    args: argparse.Namespace
    settings: Settings
    logger: logging.Logger
    log_file: Path
    input_dir: Path


def setup_script_context(
        args: argparse.Namespace,
        log_filename: str,
) -> ScriptContext:
    """Initialize common script context (settings, logging, paths).

    Args:
        args: Parsed command-line arguments (must have 'debug' attribute).
        log_filename: Name of the log file (e.g., 'youtube_coverage.log').

    Returns:
        ScriptContext with initialized settings, logger, and paths.
    """
    settings = get_settings()
    log_file = settings.data_dir / "logs" / log_filename

    log_level: LogLevel = "DEBUG" if args.debug else "INFO"

    setup_logging(
        level=log_level,
        console_level=log_level,
        log_file=log_file,
    )

    logger = get_logger(__name__)
    input_dir = settings.data_dir / "input"

    return ScriptContext(
        args=args,
        settings=settings,
        logger=logger,
        log_file=log_file,
        input_dir=input_dir,
    )


def resolve_input_path(
        args: argparse.Namespace,
        settings: Settings,
        default_subpath: str = "output/enriched_tracks.json",
) -> Path:
    """Resolve input file path from args or default.

    Args:
        args: Parsed arguments (must have 'input' attribute).
        settings: Application settings.
        default_subpath: Default path relative to data_dir.

    Returns:
        Resolved absolute path to input file.
    """
    if args.input:
        input_path = args.input

        if not input_path.is_absolute():
            input_path = PROJECT_ROOT / input_path

        return input_path

    return settings.data_dir / default_subpath


def load_enriched_tracks(
        stats_path: Path,
        logger: logging.Logger | None = None,
) -> list[TrackWithStats]:
    """Load enriched tracks from stats JSON file.

    Args:
        stats_path: Path to enriched_tracks.json.
        logger: Optional logger for reporting skipped entries.

    Returns:
        List of TrackWithStats instances.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    validate_path_within_base(stats_path, PROJECT_ROOT)

    if not stats_path.exists():
        raise FileNotFoundError(f"Enriched tracks file not found: {stats_path}")

    with open(stats_path, encoding="utf-8") as f:
        data = json.load(f)

    tracks = []
    skipped = 0

    for item in data:
        try:
            track = TrackWithStats.model_validate(item)
            tracks.append(track)
        except Exception as e:
            skipped += 1

            if logger:
                logger.warning("Skipping invalid track entry: %s", e)

            continue

    if skipped > 0 and logger:
        logger.warning("Skipped %d invalid track entries", skipped)

    return tracks


def get_display_artist(track: TrackWithStats) -> str:
    """Get artist display name for output.

    Uses Track.artist (MusicBee "Artist Displayed" tag) if available,
    falls back to all_artists_string.

    Args:
        track: TrackWithStats instance.

    Returns:
        Artist display string.
    """
    if track.track.artist:
        return track.track.artist

    return track.track.all_artists_string


def submit_links_to_songstats(
        client: SongstatsClient,
        submissions: list[dict[str, Any]],
        logger: logging.Logger,
        platform_display_name: str | None = None,
) -> dict[str, Any]:
    """Submit links to Songstats API.

    Generic link submission function used by both platform link submission
    and YouTube link submission scripts.

    Args:
        client: Initialized SongstatsClient.
        submissions: List of submission entries. Each entry must have:
            - songstats_id: Songstats track ID
            - link: URL to submit
            - artist: Artist name (for display)
            - title: Track title (for display)
            - platform (optional): Platform name for display
        logger: Logger instance for output.
        platform_display_name: Optional platform name to include in logs.

    Returns:
        Dictionary with 'success', 'pending', 'failed' counts and track lists.
    """
    results: dict[str, Any] = {
        "success": 0,
        "pending": 0,
        "failed": 0,
        "successful_tracks": [],
        "pending_tracks": [],
        "failed_tracks": [],
    }

    for idx, submission in enumerate(submissions, start=1):
        songstats_id = submission["songstats_id"]
        link = submission["link"]
        track_name = f"{submission['artist']} - {submission['title']}"

        # Build log prefix
        if platform_display_name:
            prefix = f"[{platform_display_name}] "
        elif "platform" in submission:
            prefix = f"[{submission['platform']}] "
        else:
            prefix = ""

        logger.info(
            "Processing %d/%d: %s%s",
            idx,
            len(submissions),
            prefix,
            track_name,
        )
        logger.info("  Link: %s", link)

        if not songstats_id:
            results["failed"] += 1
            results["failed_tracks"].append(f"{track_name} (no songstats_id)")
            logger.error("  Failed: Missing songstats_id")
            continue

        response = client.add_track_link(
            link=link,
            songstats_track_id=songstats_id,
        )

        logger.debug("API response: %s", response)

        if not response:
            results["failed"] += 1
            results["failed_tracks"].append(f"{track_name} (no response)")
            logger.error("  Failed: No response from API")

        elif response.get("result") == "success":
            results["success"] += 1
            results["successful_tracks"].append(track_name)
            logger.info("  Success: Link submitted")

        elif "support team" in response.get("message", "").lower():
            # Manual review required - not an error, just pending
            results["pending"] += 1
            results["pending_tracks"].append(track_name)
            logger.warning("  Pending: Requires manual review")

        else:
            results["failed"] += 1
            message = response.get("message", "Unknown error")
            results["failed_tracks"].append(f"{track_name} ({message})")
            logger.error("  Failed: %s", message)

        sleep(1)  # Rate limiting

    return results


def display_submission_results(
        results: dict[str, Any],
        logger: logging.Logger,
) -> None:
    """Display submission results summary.

    Args:
        results: Results dictionary from submit_links_to_songstats.
        logger: Logger instance.
    """
    logger.info("")
    logger.info("=" * 60)
    logger.info("Submission Summary")
    logger.info("=" * 60)
    logger.info("Successful:     %d", results["success"])
    logger.info("Pending review: %d", results["pending"])
    logger.info("Failed:         %d", results["failed"])

    if results["successful_tracks"]:
        logger.info("")
        logger.info("Successfully submitted:")
        for track in results["successful_tracks"]:
            logger.info("  - %s", track)

    if results["pending_tracks"]:
        logger.info("")
        logger.info("Pending manual review:")
        for track in results["pending_tracks"]:
            logger.info("  - %s", track)

    if results["failed_tracks"]:
        logger.info("")
        logger.info("Failed submissions:")
        for track in results["failed_tracks"]:
            logger.info("  - %s", track)


def save_json_atomically(data: Any, output_path: Path) -> None:
    """Save data to JSON file atomically.

    Writes to a temporary file first, then replaces the target file.

    Args:
        data: Data to serialize to JSON.
        output_path: Path to write the file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temp_file = output_path.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    temp_file.replace(output_path)


def load_json_file(file_path: Path) -> Any:
    """Load JSON file.

    Args:
        file_path: Path to JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If file does not exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, encoding="utf-8") as f:
        return json.load(f)
