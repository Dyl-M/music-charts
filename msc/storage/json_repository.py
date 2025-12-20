"""JSON file-based repository implementations.

Concrete repository implementations using JSON files for persistence.
Provides simple, human-readable storage while maintaining the repository
abstraction for future migration to databases if needed.
"""

# Standard library
import json
from pathlib import Path

# Third-party
import pandas as pd
from pydantic import ValidationError

# Local
from msc.models.track import Track
from msc.models.stats import TrackWithStats
from msc.storage.repository import StatsRepository, TrackRepository
from msc.utils.logging import get_logger
from msc.utils.path_utils import secure_write


class JSONTrackRepository(TrackRepository):
    """JSON file-based implementation of TrackRepository.

    Stores tracks as a JSON array, with each track serialized
    using Pydantic's model_dump. Uses track.identifier as the unique key.
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize repository with file path.

        Args:
            file_path: Path to JSON file for storage
        """
        super().__init__()
        self.file_path = file_path
        self.logger = get_logger(__name__)
        self._tracks: dict[str, Track] = {}
        self._load()

    def _load(self) -> None:
        """Load tracks from JSON file if it exists."""
        if not self.file_path.exists():
            self.logger.debug("Repository file does not exist: %s", self.file_path)
            return

        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)

            for track_data in data:
                track = Track.model_validate(track_data)
                self._tracks[track.identifier] = track

            self.logger.info("Loaded %d tracks from %s", len(self._tracks), self.file_path)

        except (OSError, json.JSONDecodeError, ValidationError, KeyError, TypeError) as error:
            self.logger.exception("Failed to load tracks from %s: %s", self.file_path, error)
            self._tracks = {}

    def _save(self) -> None:
        """Persist tracks to JSON file atomically."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            data = [track.model_dump(mode="json") for track in self._tracks.values()]

            # Write to temp file first for atomicity
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic replace (works on Windows and POSIX)
            temp_file.replace(self.file_path)

            self.logger.debug("Saved %d tracks to %s", len(self._tracks), self.file_path)

        except (OSError, json.JSONEncodeError, TypeError) as error:
            self.logger.exception("Failed to save tracks to %s: %s", self.file_path, error)
            raise  # Re-raise to let caller handle failure

    def add(self, item: Track) -> None:
        """Add a track to the repository."""
        self._tracks[item.identifier] = item
        self._save()

    def get(self, identifier: str) -> Track | None:
        """Retrieve a track by identifier."""
        return self._tracks.get(identifier)

    def get_all(self) -> list[Track]:
        """Retrieve all tracks."""
        return list(self._tracks.values())

    def exists(self, identifier: str) -> bool:
        """Check if a track exists."""
        return identifier in self._tracks

    def remove(self, identifier: str) -> None:
        """Remove a track from the repository."""
        if identifier in self._tracks:
            del self._tracks[identifier]
            self._save()

    def clear(self) -> None:
        """Remove all tracks."""
        self._tracks.clear()
        self._save()

    def count(self) -> int:
        """Get the number of tracks."""
        return len(self._tracks)

    def find_by_title_artist(self, title: str, artist: str) -> Track | None:
        """Find a track by title and artist."""
        for track in self._tracks.values():
            if track.title.lower() == title.lower() and track.primary_artist.lower() == artist.lower():
                return track
        return None

    def get_unprocessed(self, processed_ids: set[str]) -> list[Track]:
        """Get tracks that haven't been processed yet."""
        return [track for track in self._tracks.values() if track.identifier not in processed_ids]


class JSONStatsRepository(StatsRepository):
    """JSON file-based implementation of StatsRepository.

    Stores enriched tracks with statistics as a JSON array.
    Uses track.identifier as the unique key. Supports both
    nested and flat export formats for backward compatibility.
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize repository with file path.

        Args:
            file_path: Path to JSON file for storage
        """
        super().__init__()
        self.file_path = file_path
        self.logger = get_logger(__name__)
        self._stats: dict[str, TrackWithStats] = {}
        self._load()

    def _load(self) -> None:
        """Load stats from JSON file if it exists."""
        if not self.file_path.exists():
            self.logger.debug("Repository file does not exist: %s", self.file_path)
            return

        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)

            for stats_data in data:
                # Try nested format first, fall back to flat format
                try:
                    stats = TrackWithStats.model_validate(stats_data)

                except (ValidationError, KeyError, TypeError):
                    stats = TrackWithStats.from_flat_dict(stats_data)

                self._stats[stats.identifier] = stats

            self.logger.info("Loaded %d stats from %s", len(self._stats), self.file_path)

        except (OSError, json.JSONDecodeError, ValidationError, KeyError, TypeError, AttributeError) as error:
            self.logger.exception("Failed to load stats from %s: %s", self.file_path, error)
            self._stats = {}

    def _save(self) -> None:
        """Persist stats to JSON file atomically."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            data = [stats.model_dump(mode="json") for stats in self._stats.values()]

            # Write to temp file first for atomicity
            temp_file = self.file_path.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            # Atomic replace (works on Windows and POSIX)
            temp_file.replace(self.file_path)

            self.logger.debug("Saved %d stats to %s", len(self._stats), self.file_path)

        except (OSError, json.JSONEncodeError, TypeError) as error:
            self.logger.exception("Failed to save stats to %s: %s", self.file_path, error)
            raise  # Re-raise to let caller handle failure

    def add(self, item: TrackWithStats) -> None:
        """Add enriched track stats to the repository."""
        self._stats[item.identifier] = item
        self._save()

    def get(self, identifier: str) -> TrackWithStats | None:
        """Retrieve stats by track identifier."""
        return self._stats.get(identifier)

    def get_all(self) -> list[TrackWithStats]:
        """Retrieve all enriched tracks."""
        return list(self._stats.values())

    def exists(self, identifier: str) -> bool:
        """Check if stats exist for a track."""
        return identifier in self._stats

    def remove(self, identifier: str) -> None:
        """Remove stats for a track."""
        if identifier in self._stats:
            del self._stats[identifier]
            self._save()

    def clear(self) -> None:
        """Remove all stats."""
        self._stats.clear()
        self._save()

    def count(self) -> int:
        """Get the number of enriched tracks."""
        return len(self._stats)

    def save_batch(self, items: list[TrackWithStats]) -> None:
        """Save multiple items efficiently (single write)."""
        for item in items:
            self._stats[item.identifier] = item
        self._save()

    def export_to_json(self, file_path: Path, flat: bool = False) -> None:
        """Export all items to JSON file.

        Args:
            file_path: Path to output JSON file
            flat: If True, use flat dictionary format for legacy compatibility
        """
        try:
            if flat:
                data = [stats.to_flat_dict() for stats in self._stats.values()]

            else:
                data = [stats.model_dump(mode="json") for stats in self._stats.values()]

            with secure_write(file_path, encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self.logger.info(
                "Exported %d items to %s (flat=%s)", len(self._stats), file_path, flat
            )

        except (OSError, TypeError, AttributeError, ValueError) as error:
            self.logger.exception("Failed to export to %s: %s", file_path, error)

    def export_to_csv(self, file_path: Path) -> None:
        """Export all items to CSV file using pandas."""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to flat dictionaries for tabular format
            data = [stats.to_flat_dict() for stats in self._stats.values()]
            df = pd.DataFrame(data)

            df.to_csv(file_path, index=False, encoding="utf-8")

            self.logger.info("Exported %d items to CSV: %s", len(self._stats), file_path)

        except (OSError, ValueError, AttributeError, KeyError) as error:
            self.logger.exception("Failed to export to CSV: %s - %s", file_path, error)

    def get_by_songstats_id(self, songstats_id: str) -> TrackWithStats | None:
        """Find a track by Songstats ID."""
        for stats in self._stats.values():
            if stats.songstats_identifiers.songstats_id == songstats_id:
                return stats
        return None
