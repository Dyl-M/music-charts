"""Extraction stage: MusicBee library → Songstats ID resolution.

Extracts tracks from MusicBee library, searches for Songstats IDs,
and handles checkpoint resumability and manual review queue.
"""

# Standard library
from datetime import datetime
from typing import Any

# Third-party
from pydantic import ValidationError

# Local
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.config.constants import REJECT_KEYWORDS
from msc.config.settings import get_settings
from msc.models.track import Track
from msc.pipeline.base import PipelineStage
from msc.pipeline.observer import EventType, Observable
from msc.storage.checkpoint import CheckpointManager, ManualReviewQueue
from msc.storage.json_repository import JSONTrackRepository
from msc.utils.logging import get_logger
from msc.utils.text import build_search_query, format_title, remove_remixer


class ExtractionStage(PipelineStage[list[Track], list[Track]], Observable):
    """Extraction pipeline stage.

    Responsibilities:
    1. Extract tracks from MusicBee playlist
    2. Search for Songstats ID for each track
    3. Handle checkpoint resumability (skip already processed)
    4. Add tracks without Songstats ID to manual review queue
    5. Save tracks to repository
    """

    def __init__(
            self,
            musicbee_client: MusicBeeClient,
            songstats_client: SongstatsClient,
            track_repository: JSONTrackRepository,
            checkpoint_manager: CheckpointManager,
            review_queue: ManualReviewQueue,
            playlist_name: str | None = None,
            track_limit: int | None = None,
    ) -> None:
        """Initialize extraction stage.

        Args:
            musicbee_client: Client for MusicBee library access
            songstats_client: Client for Songstats API
            track_repository: Repository for storing tracks
            checkpoint_manager: Manager for checkpoint state
            review_queue: Queue for tracks needing manual review
            playlist_name: Name of playlist to extract (default: from settings)
            track_limit: Maximum number of tracks to process (None = no limit)
        """
        Observable.__init__(self)
        self.musicbee = musicbee_client
        self.songstats = songstats_client
        self.repository = track_repository
        self.checkpoint_mgr = checkpoint_manager
        self.review_queue = review_queue
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        self.track_limit = track_limit

        # Determine playlist name
        if playlist_name is None:
            playlist_name = f"✅ {self.settings.year} Selection"

        self.playlist_name = playlist_name

    @property
    def stage_name(self) -> str:
        """Human-readable name for this pipeline stage."""
        return "Extraction"

    def extract(self) -> list[Track]:
        """Extract tracks from MusicBee playlist.

        Returns:
            List of tracks from the playlist
        """
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Extraction",
            message=f"Extracting tracks from playlist '{self.playlist_name}'",
        )

        self.notify(event)

        try:
            # Find playlist by name
            playlist_id = self.musicbee.find_playlist_by_name(self.playlist_name, exact_match=True)

            if not playlist_id:
                self.logger.error("Playlist not found: %s", self.playlist_name)
                return []

            # Get tracks from playlist
            raw_tracks = self.musicbee.get_playlist_tracks(playlist_id)

            # Filter by year and convert to Track models
            tracks: list[Track] = []

            for track_data in raw_tracks:
                # Handle both dict and object (libpybee.Track) formats
                if isinstance(track_data, dict):
                    year = track_data.get("year")
                    artist_list = track_data.get("artist_list", [])
                    artist = track_data.get("artist")  # MusicBee "Artist Displayed" tag
                    title = track_data.get("title", "")
                    grouping = track_data.get("grouping")
                    genre = track_data.get("genre")

                else:
                    year = track_data.year
                    artist_list = getattr(track_data, "artist_list", [])
                    artist = getattr(track_data, "artist", None)  # MusicBee "Artist Displayed" tag
                    title = track_data.title
                    grouping = getattr(track_data, "grouping", None)
                    genre = getattr(track_data, "genre", None)

                # Check year
                if year != self.settings.year:
                    continue

                # Create Track model
                try:
                    # Use native artist_list from libpybee (no manual parsing needed)
                    # Fallback to empty list if not available
                    if not artist_list:
                        artist_list = []

                    # Get optional fields with fallback
                    # Note: In this MusicBee setup, record labels are stored in the 'grouping' field
                    # Authoritative labels are now in songstats_identifiers.songstats_labels

                    # Handle genre - may be string or list
                    genre_list = [genre] if genre and not isinstance(genre, list) else (genre if genre else [])

                    # libpybee returns grouping as a list natively - use directly
                    grouping_list = grouping if grouping else []

                    track = Track(
                        title=title,
                        artist_list=artist_list,
                        artist=artist,  # MusicBee "Artist Displayed" tag
                        year=year,
                        genre=genre_list,
                        grouping=grouping_list,  # Store as list (supports multiple values)
                        # songstats_identifiers will default to empty SongstatsIdentifiers
                    )
                    tracks.append(track)

                except (ValidationError, KeyError, TypeError, AttributeError) as error:
                    self.logger.exception(
                        "Failed to create Track model for: %s - %s",
                        title if 'title' in locals() else "Unknown",
                        error,
                    )

            self.logger.info(
                "Extracted %d tracks from playlist %s (year %d)",
                len(tracks),
                self.playlist_name,
                self.settings.year,
            )

            # Apply track limit if specified
            if self.track_limit and len(tracks) > self.track_limit:
                self.logger.info("Limiting to %d tracks (from %d)", self.track_limit, len(tracks))
                tracks = tracks[:self.track_limit]

            return tracks

        except Exception as error:
            event = self.create_event(
                EventType.STAGE_FAILED,
                stage_name="Extraction",
                message="Failed to extract tracks",
                error=error,
            )

            self.notify(event)
            raise

    def transform(self, data: list[Track]) -> list[Track]:
        """Transform tracks by resolving Songstats IDs.

        Args:
            data: Tracks extracted from MusicBee

        Returns:
            Tracks with Songstats IDs resolved
        """
        if not data:
            self.logger.warning("No tracks to transform")
            return []

        # Load or create checkpoint
        checkpoint = self.checkpoint_mgr.load_checkpoint("extraction") or self.checkpoint_mgr.create_checkpoint(
            "extraction",
            metadata={
                "playlist_name": self.playlist_name,
                "year": self.settings.year,
                "started_at": datetime.now().isoformat(),
            },
        )

        # Notify stage started with total count
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Extraction",
            message="Resolving Songstats IDs",
            metadata={"total": len(data)},
        )

        self.notify(event)
        enriched_tracks: list[Track] = []

        for track in data:
            track_id = track.identifier

            # Skip if already processed (checkpoint hit)
            if track_id in checkpoint.processed_ids:
                cached_track = self._handle_cached_track(track, checkpoint)
                if cached_track:
                    enriched_tracks.append(cached_track)
                    continue
                # Fall through to reprocess if cache miss

            # Notify processing
            event = self.create_event(
                EventType.ITEM_PROCESSING,
                stage_name="Extraction",
                item_id=track_id,
                message=f"Searching Songstats: {track.title} - {track.primary_artist}",
                metadata={"current_item": track.title},
            )
            self.notify(event)

            # Process track
            track = self._process_track_search(track, checkpoint)
            enriched_tracks.append(track)

            # Save checkpoint after each track
            self.checkpoint_mgr.save_checkpoint(checkpoint)

        # Notify stage completed
        event = self.create_event(
            EventType.STAGE_COMPLETED,
            stage_name="Extraction",
            message=f"Processed {len(enriched_tracks)} tracks",
            metadata={
                "total": len(enriched_tracks),
                "found_ids": len(checkpoint.processed_ids),
                "missing_ids": len(checkpoint.failed_ids),
            },
        )

        self.notify(event)
        return enriched_tracks

    def _process_track_search(self, track: Track, checkpoint: Any) -> Track:
        """Process a single track's Songstats search.

        Args:
            track: Track to search
            checkpoint: Current checkpoint state

        Returns:
            Track with search results applied
        """
        query = None

        try:
            # Build search query
            formatted_title = format_title(track.title)
            artists_without_remixer = remove_remixer(formatted_title, track.artist_list)
            query = build_search_query(formatted_title, artists_without_remixer)

            # Search Songstats
            search_results = self.songstats.search_track(query, limit=1)

            if not search_results:
                return self._handle_no_match(track, query, checkpoint)

            # Found Songstats ID
            result = search_results[0]

            # Validate for reject keywords only (ISSUE-013)
            is_valid, reject_reason = self._validate_track_match(track, result)
            if not is_valid:
                return self._handle_rejected_match(track, result, query, reject_reason, checkpoint)

            # Process valid match
            return self._process_valid_match(track, result, query, checkpoint)

        except Exception as error:
            return self._handle_search_error(track, query, error, checkpoint)

    def _process_valid_match(
            self, track: Track, result: dict[str, Any], query: str, checkpoint: Any
    ) -> Track:
        """Process a valid Songstats match.

        Args:
            track: Original track
            result: Songstats search result
            query: Search query used
            checkpoint: Current checkpoint state

        Returns:
            Track with Songstats identifiers populated
        """
        songstats_id = result.get("songstats_track_id", "")

        # Extract metadata (artists, labels, ISRC)
        songstats_artists, songstats_labels, isrc = self._extract_songstats_metadata(
            result, songstats_id
        )

        # Update identifiers immutably (Track is frozen)
        updated_identifiers = track.songstats_identifiers.model_copy(
            update={
                "songstats_id": songstats_id,
                "songstats_title": result.get("title", ""),
                "isrc": isrc,
                "songstats_artists": songstats_artists,
                "songstats_labels": songstats_labels,
            }
        )

        track = track.model_copy(
            update={
                "songstats_identifiers": updated_identifiers,
                "search_query": query,
            }
        )

        self.logger.info(
            "Found Songstats ID for '%s - %s': %s",
            track.primary_artist,
            track.title,
            track.songstats_identifiers.songstats_id,
        )

        # Add to processed
        checkpoint.processed_ids.add(track.identifier)

        # Notify success
        event = self.create_event(
            EventType.ITEM_COMPLETED,
            stage_name="Extraction",
            item_id=track.identifier,
            message=f"Found ID: {track.songstats_identifiers.songstats_id}",
        )
        self.notify(event)

        return track

    def _handle_cached_track(
            self, track: Track, checkpoint: Any
    ) -> Track | None:
        """Handle track that was already processed (checkpoint hit).

        Args:
            track: Track to check
            checkpoint: Current checkpoint state

        Returns:
            Cached track from repository if found, None if needs reprocessing
        """
        existing_track = self.repository.get(track.identifier)

        if existing_track:
            self.logger.debug("Skipping already processed track: %s", track.identifier)
            event = self.create_event(
                EventType.ITEM_SKIPPED,
                stage_name="Extraction",
                item_id=track.identifier,
                message=f"Already processed: {track.title} - {track.primary_artist}",
            )
            self.notify(event)
            return existing_track

        # Repository lost track - mark for reprocessing
        self.logger.warning(
            "Track %s in checkpoint but missing from repository, reprocessing",
            track.identifier
        )
        checkpoint.processed_ids.remove(track.identifier)
        return None

    def _extract_songstats_metadata(
            self, result: dict[str, Any], songstats_id: str
    ) -> tuple[list[str], list[str], str | None]:
        """Extract artists, labels, and ISRC from Songstats result.

        Args:
            result: Songstats search result
            songstats_id: Songstats track ID

        Returns:
            Tuple of (artists, labels, isrc)
        """
        # Extract artist list
        songstats_artists = result.get("artists", [])
        if isinstance(songstats_artists, list):
            songstats_artists = [
                artist["name"] if isinstance(artist, dict) else str(artist)
                for artist in songstats_artists
            ]
        else:
            songstats_artists = []

        # Extract label list
        songstats_labels = result.get("labels", [])
        if isinstance(songstats_labels, list):
            songstats_labels = [
                label["name"] if isinstance(label, dict) else str(label)
                for label in songstats_labels
            ]
        else:
            songstats_labels = []

        # Fetch ISRC from track info
        isrc = None
        if songstats_id:
            track_info = self.songstats.get_track_info(songstats_id)
            if track_info:
                track_info_data = track_info.get("track_info", {})
                links = track_info_data.get("links", [])
                for link in links:
                    if isinstance(link, dict) and link.get("isrc"):
                        isrc = link["isrc"]
                        self.logger.debug(
                            "Found ISRC for %s from %s: %s",
                            songstats_id,
                            link.get("platform", "unknown"),
                            isrc
                        )
                        break
                if not isrc:
                    self.logger.debug("No ISRC found for %s", songstats_id)

        return songstats_artists, songstats_labels, isrc

    def _handle_rejected_match(
            self, track: Track, result: dict[str, Any], query: str,
            reject_reason: str, checkpoint: Any
    ) -> Track:
        """Handle rejected Songstats match (karaoke, instrumental, etc.).

        Args:
            track: Original track
            result: Songstats search result
            query: Search query used
            reject_reason: Reason for rejection
            checkpoint: Current checkpoint state

        Returns:
            Track with search_query set
        """
        self.logger.warning(
            "Rejected match for '%s - %s': %s (Songstats: '%s')",
            track.primary_artist,
            track.title,
            reject_reason,
            result.get("title", ""),
        )

        track = track.model_copy(update={"search_query": query})

        self.review_queue.add(
            track_id=track.identifier,
            title=track.title,
            artist=track.primary_artist,
            reason=f"Rejected: {reject_reason}",
            metadata={
                "query": query,
                "songstats_title": result.get("title", ""),
                "songstats_id": result.get("songstats_track_id", ""),
            },
        )

        checkpoint.failed_ids.add(track.identifier)

        event = self.create_event(
            EventType.WARNING,
            stage_name="Extraction",
            item_id=track.identifier,
            message=f"Rejected match ({reject_reason}): {result.get('title', 'Unknown')}"
        )
        self.notify(event)

        return track

    def _handle_no_match(
            self, track: Track, query: str, checkpoint: Any
    ) -> Track:
        """Handle case when no Songstats match found.

        Args:
            track: Original track
            query: Search query used
            checkpoint: Current checkpoint state

        Returns:
            Track with search_query set
        """
        self.logger.warning(
            "No Songstats ID found for: %s - %s",
            track.primary_artist,
            track.title
        )

        track = track.model_copy(update={"search_query": query})

        self.review_queue.add(
            track_id=track.identifier,
            title=track.title,
            artist=track.primary_artist,
            reason="No Songstats ID found in search results",
            metadata={"query": query},
        )

        checkpoint.failed_ids.add(track.identifier)

        event = self.create_event(
            EventType.WARNING,
            stage_name="Extraction",
            item_id=track.identifier,
            message=f"No Songstats ID found (added to review queue): {track.title} - {track.primary_artist}"
        )
        self.notify(event)

        return track

    def _handle_search_error(
            self, track: Track, query: str | None, error: Exception, checkpoint: Any
    ) -> Track:
        """Handle error during Songstats search.

        Args:
            track: Original track
            query: Search query used (may be None if error occurred before query built)
            error: Exception that occurred
            checkpoint: Current checkpoint state

        Returns:
            Track (possibly with search_query set)
        """
        self.logger.exception("Failed to search Songstats for: %s", track.identifier)

        if query:
            track = track.model_copy(update={"search_query": query})

        self.review_queue.add(
            track_id=track.identifier,
            title=track.title,
            artist=track.primary_artist,
            reason=f"Error during Songstats search: {error!s}",
        )

        checkpoint.failed_ids.add(track.identifier)

        event = self.create_event(
            EventType.ITEM_FAILED,
            stage_name="Extraction",
            item_id=track.identifier,
            message=f"Search failed: {error!s}",
            error=error,
        )
        self.notify(event)

        return track

    @staticmethod
    def _normalize_artists(artists: list[str]) -> list[str]:
        """Normalize artist list for comparison.

        Removes duplicates (case-insensitive) and sorts alphabetically.

        Args:
            artists: List of artist names

        Returns:
            Normalized list (deduplicated, lowercase, sorted)
        """
        # Deduplicate case-insensitively using a set (lowercase)
        unique_artists = {artist.lower() for artist in artists if artist}
        # Return sorted list for consistent ordering
        return sorted(unique_artists)

    def _validate_track_match(self, track: Track, result: dict[str, Any]) -> tuple[bool, str]:
        """Validate that Songstats result matches the searched track.

        Only checks for reject keywords (karaoke, instrumental, etc.).
        Similarity validation disabled to maximize match success rate.

        Args:
            track: Original track from MusicBee
            result: Search result from Songstats API

        Returns:
            Tuple of (is_valid, reason) where:
                - is_valid: True if match is valid, False if contains reject keyword
                - reason: Rejection reason (keyword found) or empty string
        """
        songstats_title = result.get("title", "").lower()

        # Reject obvious mismatches (karaoke, instrumental, cover versions)
        for keyword in REJECT_KEYWORDS:
            if keyword in songstats_title:
                self.logger.debug(
                    "Rejecting match for '%s' - contains keyword '%s' in title: %s",
                    track.title,
                    keyword,
                    songstats_title,
                )
                return False, f"Contains reject keyword: '{keyword}'"

        # Accept all other matches (no similarity validation)
        return True, ""

    def load(self, data: list[Track]) -> None:
        """Save enriched tracks to repository.

        Args:
            data: Tracks with Songstats IDs resolved
        """
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Extraction",
            message=f"Saving {len(data)} tracks to repository",
        )

        self.notify(event)

        try:
            for track in data:
                self.repository.add(track)

            self.logger.info("Saved %d tracks to repository", len(data))

            # Notify checkpoint saved
            event = self.create_event(
                EventType.CHECKPOINT_SAVED,
                stage_name="Extraction",
                message="Tracks saved to repository",
            )

            self.notify(event)

        except Exception as error:
            self.logger.exception("Failed to save tracks to repository")

            event = self.create_event(
                EventType.ERROR,
                stage_name="Extraction",
                message="Failed to save tracks",
                error=error,
            )

            self.notify(event)
            raise
