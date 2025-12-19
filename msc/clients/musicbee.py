"""MusicBee library XML parser."""

# Standard library
from pathlib import Path
import shutil
from typing import Any

# Third-party
import libpybee

# Local
from msc.config.settings import Settings, get_settings
from msc.utils.logging import get_logger


class MusicBeeClient:
    """Client for parsing MusicBee library XML files.

    Provides access to MusicBee playlists and tracks with automatic
    caching, error handling, and resource cleanup.

    The client copies the XML file to a cache directory before parsing
    to avoid locking the original MusicBee library file.

    Supports context manager for automatic cleanup:
        >>> with MusicBeeClient() as client:
        ...     tracks = client.get_playlist_tracks("4361", year=2025)

    Example:
        >>> client = MusicBeeClient()
        >>> tracks = client.get_playlist_tracks("4361", year=2025)
        >>> len(tracks)
        152
        >>> client.close()  # Clean up cached files
    """

    def __init__(
            self,
            library_path: Path | None = None,
            settings: Settings | None = None,
    ):
        """Initialize the MusicBee client.

        Args:
            library_path: Path to iTunes Music Library.xml file.
                Uses settings.musicbee_library if None.
            settings: Application settings. Uses global settings if None.

        Raises:
            FileNotFoundError: If the library file doesn't exist.

        Example:
            >>> client = MusicBeeClient(Path("path/to/library.xml"))
            >>> # Or use settings
            >>> client2 = MusicBeeClient()  # Uses MSC_MUSICBEE_LIBRARY
        """
        self.settings = settings or get_settings()
        self.library_path = library_path or self.settings.musicbee_library
        self.logger = get_logger(self.__class__.__name__)

        # Validate file exists
        if not self.library_path.exists():
            raise FileNotFoundError(
                f"MusicBee library not found: {self.library_path}"
            )

        # State
        self._library: libpybee.Library | None = None
        self._cached_xml_path: Path | None = None

    def get_library(self) -> libpybee.Library:
        """Load and parse MusicBee library XML.

        The XML file is copied to the cache directory before parsing to
        avoid locking the original file. The parsed library is cached
        in memory after the first call.

        Returns:
            Parsed library object containing all playlists and tracks.

        Raises:
            RuntimeError: If XML parsing fails.

        Example:
            >>> client = MusicBeeClient()
            >>> library = client.get_library()
            >>> len(library.playlists)
            25
            >>> len(library.tracks)
            5432
        """
        if self._library is not None:
            return self._library

        try:
            # Copy to cache directory
            cache_dir = self.settings.data_dir / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)

            self._cached_xml_path = cache_dir / "lib.xml"

            self.logger.info(
                "Copying library from %s to %s",
                self.library_path,
                self._cached_xml_path,
            )

            shutil.copyfile(self.library_path, self._cached_xml_path)

            # Parse XML
            self.logger.info("Parsing library XML...")
            self._library = libpybee.Library(str(self._cached_xml_path))

            playlist_count = len(self._library.playlists)
            track_count = len(self._library.tracks)

            self.logger.info(
                "Loaded library: %d playlists, %d tracks",
                playlist_count,
                track_count,
            )

            return self._library

        except Exception as e:
            self.logger.error("Failed to parse library: %s", e)
            raise RuntimeError(f"Failed to parse MusicBee library: {e}") from e

    def get_playlist_tracks(
            self,
            playlist_id: str,
            year: int | None = None,
    ) -> list[libpybee.Track]:
        """Get tracks from a playlist, optionally filtered by year.

        Args:
            playlist_id: MusicBee playlist identifier (e.g., "4361").
            year: Optional year filter (e.g., 2025). Returns all years if None.

        Returns:
            List of Track objects. Empty list if playlist not found.

        Example:
            >>> client = MusicBeeClient()
            >>> # Get all tracks from playlist
            >>> a_track = client.get_playlist_tracks("4361")
            >>> len(a_track)
            500
            >>> # Filter by year
            >>> tracks_2025 = client.get_playlist_tracks("4361", year=2025)
            >>> len(tracks_2025)
            152
            >>> all(t.year == 2025 for t in tracks_2025)
            True
        """
        library = self.get_library()

        # Check playlist exists
        if playlist_id not in library.playlists:
            self.logger.error("Playlist %s not found", playlist_id)
            return []

        playlist = library.playlists[playlist_id]
        tracks = playlist.tracks

        self.logger.debug(
            "Found %d tracks in playlist %s",
            len(tracks),
            playlist_id,
        )

        # Apply year filter
        if year is not None:
            tracks = [t for t in tracks if t.year == year]
            self.logger.debug(
                "Filtered to %d tracks for year %d",
                len(tracks),
                year,
            )

        return tracks

    def get_all_playlists(self) -> dict[str, Any]:
        """Get all playlists in the library.

        Returns a dictionary with playlist metadata including name and
        track count. Useful for discovery and debugging.

        Returns:
            Dictionary mapping playlist ID to playlist metadata.

        Example:
            >>> client = MusicBeeClient()
            >>> playlists = client.get_all_playlists()
            >>> playlists['4361']
            {'name': 'DJ Tracks', 'track_count': 500}
            >>> list(playlists.keys())
            ['4361', '5892', '7123']
        """
        library = self.get_library()

        playlists_info = {
            pid: {
                "name": playlist.name if hasattr(playlist, "name") else "Unknown",
                "track_count": len(playlist.tracks),
            }
            for pid, playlist in library.playlists.items()
        }

        self.logger.debug("Retrieved %d playlists", len(playlists_info))
        return playlists_info

    def find_playlist_by_name(
            self,
            name: str,
            exact_match: bool = False,
    ) -> str | None:
        """Find playlist ID by name.

        MusicBee assigns playlist IDs dynamically based on library size,
        making hardcoded IDs unreliable. This method searches by name instead.

        Args:
            name: Playlist name to search for.
            exact_match: If True, require exact match (case-insensitive).
                        If False, match if name is contained in playlist name.

        Returns:
            Playlist ID if found, None otherwise.

        Example:
            >>> client = MusicBeeClient()
            >>> # Exact match
            >>> client.find_playlist_by_name("✅ 2025 Selection", exact_match=True)
            '5218'
            >>> # Partial match
            >>> client.find_playlist_by_name("Selection")
            '5213'  # Returns first match like "'20 and older Selection"
        """
        if not name or not name.strip():
            self.logger.error("Playlist name is required")
            return None

        library = self.get_library()
        search_name = name.strip().lower()

        for pid, playlist in library.playlists.items():
            playlist_name = getattr(playlist, "name", "").lower()

            # Check match based on mode
            matches = (
                playlist_name == search_name if exact_match
                else search_name in playlist_name
            )

            if matches:
                self.logger.debug("Found playlist '%s' with ID %s", name, pid)
                return pid

        self.logger.warning("Playlist '%s' not found", name)
        return None

    def close(self) -> None:
        """Clean up resources and delete cached XML file.

        Removes the cached library XML file from the cache directory
        and clears the in-memory library object.

        This method is called automatically when using the client as a
        context manager.

        Example:
            >>> client = MusicBeeClient()
            >>> library = client.get_library()
            >>> client.close()  # Clean up
            >>> # Or use context manager
            >>> with MusicBeeClient() as client:
            ...     library2 = client.get_library()
            ... # Automatically cleaned up
        """
        if self._cached_xml_path and self._cached_xml_path.exists():
            self.logger.debug("Cleaning up cached XML: %s", self._cached_xml_path)
            self._cached_xml_path.unlink()
            self._cached_xml_path = None

        self._library = None

    def __enter__(self) -> "MusicBeeClient":
        """Context manager entry.

        Returns:
            Self for use in with statement.

        Example:
            >>> with MusicBeeClient() as client:
            ...     tracks = client.get_playlist_tracks("4361")
        """
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit with automatic cleanup.

        Args:
            *args: Exception info (exc_type, exc_val, exc_tb).

        Example:
            >>> with MusicBeeClient() as client:
            ...     tracks = client.get_playlist_tracks("4361")
            ... # close() called automatically here
        """
        self.close()
