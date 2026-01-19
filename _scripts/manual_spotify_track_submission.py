"""Standalone utility for submitting manual track additions to Songstats.

Reads pending tracks from manual_review.json and processes a CSV/JSON input file
with (songstats_artist_id, spotify_track_id) pairs to add tracks via Songstats API.

Usage:
    # Generate template from manual_review.json:
    python _scripts/manual_spotify_track_submission.py --generate
    uv run python _scripts/manual_spotify_track_submission.py --generate

    # With explicit input file:
    python _scripts/manual_spotify_track_submission.py input.csv
    uv run python _scripts/manual_spotify_track_submission.py input.json

    # Auto-detect from default folder (_data/input):
    python _scripts/manual_spotify_track_submission.py
    uv run python _scripts/manual_spotify_track_submission.py

    # Or run directly from IDE (F5/Run) - uses _data/input by default

Input CSV Format:
    songstats_artist_id,spotify_track_id
    abc123,4uLU6hMCjMI75M1A2tKUQC
    def456,7ouMYWpwJ422jRcDASZB7P

Input JSON Format:
    [
        {"songstats_artist_id": "abc123", "spotify_track_id": "4uLU6hMCjMI75M1A2tKUQC"},
        {"songstats_artist_id": "def456", "spotify_track_id": ["7ouMYWpwJ422jRcDASZB7P", "2abc..."]}
    ]

    Note: spotify_track_id can be a single string or a list of strings (JSON only).

Output:
    - Console: Real-time progress with success/failure counts
    - Log file: _data/logs/manual_submissions.log
"""

# Standard library
import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from time import sleep
from typing import Any

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Local imports (reuse existing components)
# ruff: noqa: E402
from _shared import (
    display_submission_results,
    save_json_atomically,
    setup_script_context,
)

from msc.clients.songstats import SongstatsClient
from msc.config.settings import get_settings
from msc.utils.path_utils import validate_path_within_base


def load_manual_review() -> list[dict[str, Any]]:
    """Load pending tracks from manual_review.json.

    Finds the most recent run directory and loads its manual_review.json.

    Returns:
        List of pending track dictionaries from manual review queue.
    """
    settings = get_settings()

    runs_dir = settings.data_dir / "runs"
    if not runs_dir.exists():
        return []

    run_dirs = sorted(runs_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)

    for run_dir in run_dirs:
        manual_review_file = run_dir / "manual_review.json"
        if manual_review_file.exists():
            with open(manual_review_file, encoding="utf-8") as f:
                return json.load(f)

    return []


def load_input_file(file_path: Path) -> list[dict[str, Any]]:
    """Load artist/track ID pairs from CSV or JSON input file.

    Args:
        file_path: Path to input CSV or JSON file.

    Returns:
        List of dictionaries with 'songstats_artist_id' and 'spotify_track_id' keys.
        For JSON, spotify_track_id can be a string or list of strings.

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If file format is unsupported or invalid.
    """
    validate_path_within_base(file_path, PROJECT_ROOT)

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return _parse_csv(file_path)

    elif suffix == ".json":
        return _parse_json(file_path)

    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .csv or .json")


def _parse_csv(file_path: Path) -> list[dict[str, str]]:
    """Parse CSV input file.

    Args:
        file_path: Path to CSV file.

    Returns:
        List of parsed row dictionaries.

    Raises:
        ValueError: If required columns are missing.
    """
    with open(file_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        data = list(reader)

        if not data:
            return []

        required = {"songstats_artist_id", "spotify_track_id"}
        if not required.issubset(data[0].keys()):
            raise ValueError(
                f"CSV must have columns: {', '.join(sorted(required))}. "
                f"Found: {', '.join(sorted(data[0].keys()))}"
            )

        return data


def _parse_json(file_path: Path) -> list[dict[str, Any]]:
    """Parse JSON input file.

    Args:
        file_path: Path to JSON file.

    Returns:
        List of parsed objects. spotify_track_id can be a string or list of strings.

    Raises:
        ValueError: If JSON structure is invalid.
    """
    with open(file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("JSON must be a list of objects")

    if not data:
        return []

    required = {"songstats_artist_id", "spotify_track_id"}
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            raise ValueError(f"Item {idx} is not an object")

        if not required.issubset(item.keys()):
            raise ValueError(
                f"Item {idx} missing required keys. "
                f"Required: {', '.join(sorted(required))}"
            )

        # Validate spotify_track_id is string or list of strings
        track_id = item["spotify_track_id"]
        if isinstance(track_id, str):
            continue
        elif isinstance(track_id, list):
            if not all(isinstance(tid, str) for tid in track_id):
                raise ValueError(
                    f"Item {idx}: spotify_track_id list must contain only strings"
                )
        else:
            raise ValueError(
                f"Item {idx}: spotify_track_id must be a string or list of strings"
            )

    return data


def submit_tracks(
        client: SongstatsClient,
        submissions: list[dict[str, Any]],
        logger: logging.Logger,
) -> dict[str, Any]:
    """Submit tracks to Songstats API.

    Args:
        client: Initialized SongstatsClient.
        submissions: List of artist/track ID pairs. spotify_track_id can be string or list.
        logger: Logger instance for output.

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
        artist_id = submission["songstats_artist_id"]
        track_ids = submission["spotify_track_id"]
        track_name = submission.get("track", f"{artist_id} / {track_ids}")

        # Normalize to list for uniform processing
        if isinstance(track_ids, str):
            track_ids = [track_ids]

        logger.info(
            "Processing %d/%d: artist=%s, track(s)=%s",
            idx,
            len(submissions),
            artist_id,
            track_ids,
        )

        for track_id in track_ids:
            spotify_link = f"https://open.spotify.com/track/{track_id}"
            response = client.add_artist_track(
                songstats_artist_id=artist_id,
                link=spotify_link,
            )

            logger.debug("API response: %s", response)

            if not response:
                results["failed"] += 1
                results["failed_tracks"].append(f"{track_name} [{track_id}] (no response)")
                logger.error("Failed to submit: %s (No response)", track_id)

            elif response.get("result") == "success":
                results["success"] += 1
                results["successful_tracks"].append(f"{track_name} [{track_id}]")
                logger.info("Successfully added: %s", track_id)

            elif "support team" in response.get("message", "").lower():
                # Manual review required - not an error, just pending
                results["pending"] += 1
                results["pending_tracks"].append(f"{track_name} [{track_id}]")
                logger.warning("Pending manual review: %s", track_id)

            else:
                results["failed"] += 1
                message = response.get("message", "Unknown error")
                results["failed_tracks"].append(f"{track_name} [{track_id}] ({message})")
                logger.error("Failed to submit: %s (%s)", track_id, message)

            sleep(1)  # Let the API breathe

    return results


def display_pending_tracks(pending: list[dict[str, Any]], logger: logging.Logger) -> None:
    """Display pending tracks from manual review queue.

    Args:
        pending: List of pending track dictionaries.
        logger: Logger instance for output.
    """
    logger.info("Pending tracks in manual_review.json: %d", len(pending))

    if pending:
        logger.info("First 10 pending tracks:")

        for track in pending[:10]:
            logger.info(
                "  - %s - %s (ID: %s)",
                track.get("artist", "Unknown"),
                track.get("title", "Unknown"),
                track.get("track_id", "N/A"),
            )

        if len(pending) > 10:
            logger.info("  ... and %d more", len(pending) - 10)


# Default input folder and file relative to project root
DEFAULT_INPUT_FOLDER = "_data/input"
DEFAULT_INPUT_FILE = "spotify_submission.json"


def generate_template(pending_tracks: list[dict[str, Any]], output_path: Path) -> int:
    """Generate a template submission file from pending manual review tracks.

    Creates a JSON file with track info pre-filled and empty ID fields for the user
    to complete.

    Args:
        pending_tracks: List of pending track dictionaries from manual_review.json.
        output_path: Path to write the template file.

    Returns:
        Number of tracks written to template.
    """
    template_entries = []

    for track in pending_tracks:
        artist = track.get("artist", "Unknown")
        title = track.get("title", "Unknown")

        template_entries.append({
            "track": f"{artist} - {title}",
            "songstats_artist_id": "",
            "spotify_track_id": "",
        })

    save_json_atomically(template_entries, output_path)

    return len(template_entries)


def find_input_file(input_dir: Path) -> Path | None:
    """Find a CSV or JSON input file in the specified directory.

    First checks for the default file (spotify_submission.json), then falls back
    to the most recently modified .csv or .json file.

    Args:
        input_dir: Directory to search for input files.

    Returns:
        Path to the input file, or None if no valid files found.
    """
    if not input_dir.exists():
        return None

    # First, check for the default file
    default_file = input_dir / DEFAULT_INPUT_FILE
    if default_file.exists():
        return default_file

    # Fall back to most recent .csv or .json file
    input_files = list(input_dir.glob("*.csv")) + list(input_dir.glob("*.json"))

    if not input_files:
        return None

    return max(input_files, key=lambda p: p.stat().st_mtime)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed argument namespace.
    """
    parser = argparse.ArgumentParser(
        description="Submit manual track additions to Songstats API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Input CSV format:
  songstats_artist_id,spotify_track_id
  abc123,4uLU6hMCjMI75M1A2tKUQC

Input JSON format:
  [{"songstats_artist_id": "abc123", "spotify_track_id": "4uLU6hMCjMI75M1A2tKUQC"}]

Examples:
  python _scripts/manual_spotify_track_submission.py
  python _scripts/manual_spotify_track_submission.py submissions.csv
  uv run python _scripts/manual_spotify_track_submission.py submissions.json
""",
    )

    parser.add_argument(
        "input_file",
        nargs="?",
        type=Path,
        default=None,
        help=f"Input CSV or JSON file. If not provided, auto-detects from {DEFAULT_INPUT_FOLDER}/",
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help=f"Directory to search for input files (default: {DEFAULT_INPUT_FOLDER})",
    )

    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate template file from manual_review.json with track names pre-filled",
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging (shows API responses)",
    )

    return parser.parse_args()


LOG_FILE = "manual_submissions.log"


def main() -> None:
    """Main entry point for manual track submission script."""
    args = parse_args()

    # Initialize common context
    ctx = setup_script_context(args, LOG_FILE)
    logger = ctx.logger

    # Handle --generate mode
    if args.generate:
        logger.info("=" * 60)
        logger.info("Generate Template Mode")
        logger.info("=" * 60)

        pending_tracks = load_manual_review()

        if not pending_tracks:
            logger.warning("No pending tracks found in manual_review.json")
            logger.info("Run the pipeline first to generate manual_review.json")
            sys.exit(0)

        output_path = PROJECT_ROOT / DEFAULT_INPUT_FOLDER / DEFAULT_INPUT_FILE
        count = generate_template(pending_tracks, output_path)

        logger.info("Generated template with %d tracks", count)
        logger.info("Output: %s", output_path)
        logger.info("")
        logger.info("Next steps:")
        logger.info("  1. Open %s", output_path.name)
        logger.info("  2. Fill in songstats_artist_id and spotify_track_id for each track")
        logger.info("  3. Run this script again without --generate to submit")
        return

    # Determine input file path
    if args.input_file:
        # Explicit file provided
        input_path = args.input_file

        if not input_path.is_absolute():
            input_path = PROJECT_ROOT / input_path

    else:
        # Auto-detect from default or specified input directory
        input_dir = args.input_dir if args.input_dir else ctx.input_dir

        if not input_dir.is_absolute():
            input_dir = PROJECT_ROOT / input_dir

        logger.info("Searching for input files in: %s", input_dir)
        input_path = find_input_file(input_dir)

        if not input_path:
            logger.error("No .csv or .json files found in %s", input_dir)
            logger.info("Use --generate to create a template from manual_review.json")
            sys.exit(1)

        logger.info("Auto-detected input file: %s", input_path.name)

    try:
        logger.info("=" * 60)
        logger.info("Manual Track Submission Utility")
        logger.info("=" * 60)

        pending_tracks = load_manual_review()
        display_pending_tracks(pending_tracks, logger)

        logger.info("")
        logger.info("Loading input file: %s", input_path)
        submissions = load_input_file(input_path)
        logger.info("Loaded %d submissions", len(submissions))

        if not submissions:
            logger.warning("No submissions found in input file")
            sys.exit(0)

        logger.info("")
        logger.info("Submitting tracks to Songstats API...")

        with SongstatsClient() as client:
            results = submit_tracks(client, submissions, logger)

        display_submission_results(results, logger)

        logger.info("")
        logger.info("Log file: %s", ctx.log_file)

    except FileNotFoundError as e:
        logger.error("File not found: %s", e)
        sys.exit(1)

    except ValueError as e:
        logger.error("Invalid input: %s", e)
        sys.exit(1)

    except Exception as e:
        logger.exception("Unexpected error: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
