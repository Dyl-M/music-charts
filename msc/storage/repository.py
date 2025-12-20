"""Abstract repository interfaces for data access layer.

This module defines the repository pattern for clean separation between
business logic and data persistence. Repositories provide a collection-like
interface for domain objects while hiding persistence details.
"""

# Standard library
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar

# Local
from msc.models.track import Track
from msc.models.stats import TrackWithStats

T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract base repository for CRUD operations.

    Provides a collection-like interface for domain objects,
    abstracting away persistence implementation details.
    """

    @abstractmethod
    def add(self, item: T) -> None:
        """Add an item to the repository.

        Args:
            item: The item to add
        """
        ...

    @abstractmethod
    def get(self, identifier: str) -> T | None:
        """Retrieve an item by identifier.

        Args:
            identifier: Unique identifier for the item

        Returns:
            The item if found, None otherwise
        """
        ...

    @abstractmethod
    def get_all(self) -> list[T]:
        """Retrieve all items from the repository.

        Returns:
            List of all items
        """
        ...

    @abstractmethod
    def exists(self, identifier: str) -> bool:
        """Check if an item exists.

        Args:
            identifier: Unique identifier for the item

        Returns:
            True if item exists, False otherwise
        """
        ...

    @abstractmethod
    def remove(self, identifier: str) -> None:
        """Remove an item from the repository.

        Args:
            identifier: Unique identifier for the item to remove
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all items from the repository."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Get the number of items in the repository.

        Returns:
            Number of items
        """
        ...


class TrackRepository(Repository[Track]):
    """Repository for Track domain objects.

    Manages persistence and retrieval of Track objects,
    using track identifier as the unique key.
    """

    @abstractmethod
    def find_by_title_artist(self, title: str, artist: str) -> Track | None:
        """Find a track by title and artist.

        Args:
            title: Track title
            artist: Artist name

        Returns:
            Track if found, None otherwise
        """
        ...

    @abstractmethod
    def get_unprocessed(self, processed_ids: set[str]) -> list[Track]:
        """Get tracks that haven't been processed yet.

        Args:
            processed_ids: Set of track identifiers already processed

        Returns:
            List of unprocessed tracks
        """
        ...


class StatsRepository(Repository[TrackWithStats]):
    """Repository for TrackWithStats domain objects.

    Manages persistence and retrieval of enriched tracks with
    platform statistics, using track identifier as the unique key.
    """

    @abstractmethod
    def save_batch(self, items: list[TrackWithStats]) -> None:
        """Save multiple items efficiently.

        Args:
            items: List of items to save
        """
        ...

    @abstractmethod
    def export_to_json(self, file_path: Path, flat: bool = False) -> None:
        """Export all items to JSON file.

        Args:
            file_path: Path to output JSON file
            flat: If True, use flat dictionary format for legacy compatibility
        """
        ...

    @abstractmethod
    def export_to_csv(self, file_path: Path) -> None:
        """Export all items to CSV file.

        Args:
            file_path: Path to output CSV file
        """
        ...

    @abstractmethod
    def get_by_songstats_id(self, songstats_id: str) -> TrackWithStats | None:
        """Find a track by Songstats ID.

        Args:
            songstats_id: Songstats track identifier

        Returns:
            TrackWithStats if found, None otherwise
        """
        ...
