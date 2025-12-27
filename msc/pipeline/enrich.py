"""Enrichment stage: Fetch comprehensive platform statistics.

Enriches tracks with platform statistics from Songstats API,
including optional YouTube video data.
"""

# Standard library
from datetime import datetime

# Third-party
from pydantic import ValidationError

# Local
from msc.clients.songstats import SongstatsClient
from msc.config.settings import get_settings
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import Track
from msc.models.youtube import YouTubeVideo, YouTubeVideoData
from msc.pipeline.base import PipelineStage
from msc.pipeline.observer import EventType, Observable
from msc.storage.checkpoint import CheckpointManager
from msc.storage.json_repository import JSONStatsRepository, JSONTrackRepository
from msc.utils.logging import get_logger


class EnrichmentStage(PipelineStage[list[Track], list[TrackWithStats]], Observable):
    """Enrichment pipeline stage.

    Responsibilities:
    1. Fetch comprehensive platform statistics from Songstats API
    2. Optionally fetch YouTube video data (quota-free via Songstats)
    3. Handle checkpoint resumability
    4. Convert to TrackWithStats models
    5. Save to stats repository
    """

    def __init__(
            self,
            songstats_client: SongstatsClient,
            stats_repository: JSONStatsRepository,
            checkpoint_manager: CheckpointManager,
            include_youtube: bool = True,
            track_repository: "JSONTrackRepository | None" = None,
    ) -> None:
        """Initialize enrichment stage.

        Args:
            songstats_client: Client for Songstats API
            stats_repository: Repository for storing enriched tracks
            checkpoint_manager: Manager for checkpoint state
            include_youtube: Whether to fetch YouTube video data
            track_repository: Optional repository for loading input tracks (enables standalone execution)
        """
        Observable.__init__(self)
        self.songstats = songstats_client
        self.repository = stats_repository
        self.checkpoint_mgr = checkpoint_manager
        self.include_youtube = include_youtube
        self.track_repository = track_repository
        self.settings = get_settings()
        self.logger = get_logger(__name__)

    @property
    def stage_name(self) -> str:
        """Human-readable name for this pipeline stage."""
        return "Enrichment"

    def extract(self) -> list[Track]:
        """Extract tracks from repository for standalone execution.

        Returns:
            List of tracks from repository, or empty list if no repository provided
        """
        if self.track_repository:
            tracks = self.track_repository.get_all()
            self.logger.info("Loaded %d tracks from repository", len(tracks))
            return tracks

        self.logger.debug("No track repository provided, returning empty list")
        return []

    def transform(self, data: list[Track]) -> list[TrackWithStats]:
        """Transform tracks by fetching platform statistics.

        Args:
            data: Tracks with Songstats IDs

        Returns:
            Tracks enriched with platform statistics
        """
        if not data:
            self.logger.warning("No tracks to enrich")
            return []

        # Filter tracks that have Songstats IDs
        tracks_with_ids = [
            track for track in data if track.songstats_identifiers.songstats_id
        ]

        if not tracks_with_ids:
            self.logger.warning("No tracks have Songstats IDs, skipping enrichment")
            return []

        # Load or create checkpoint
        checkpoint = self.checkpoint_mgr.load_checkpoint("enrichment") or self.checkpoint_mgr.create_checkpoint(
            "enrichment",
            metadata={
                "include_youtube": self.include_youtube,
                "started_at": datetime.now().isoformat(),
            },
        )

        # Notify stage started
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Enrichment",
            message=f"Enriching {len(tracks_with_ids)} tracks with platform stats",
            metadata={"total": len(tracks_with_ids)},
        )

        self.notify(event)
        enriched_tracks: list[TrackWithStats] = []

        for track in tracks_with_ids:
            track_id = track.identifier

            # Skip if already processed (checkpoint hit)
            if track_id in checkpoint.processed_ids:
                cached_stats = self._handle_cached_track(track, checkpoint)
                if cached_stats:
                    enriched_tracks.append(cached_stats)
                    continue
                # Fall through to reprocess if cache miss

            # Notify processing
            event = self.create_event(
                EventType.ITEM_PROCESSING,
                stage_name="Enrichment",
                item_id=track_id,
                message=f"Fetching stats: {track.title} - {track.primary_artist}",
                metadata={"current_item": track.title},
            )
            self.notify(event)

            # Process track enrichment
            track_with_stats = self._enrich_track(track, checkpoint)
            if track_with_stats:
                enriched_tracks.append(track_with_stats)

            # Save checkpoint after each track
            self.checkpoint_mgr.save_checkpoint(checkpoint)

        # Notify stage completed
        event = self.create_event(
            EventType.STAGE_COMPLETED,
            stage_name="Enrichment",
            message=f"Enriched {len(enriched_tracks)} tracks",
            metadata={
                "total": len(enriched_tracks),
                "successful": len(checkpoint.processed_ids),
                "failed": len(checkpoint.failed_ids),
            },
        )

        self.notify(event)
        return enriched_tracks

    def _handle_cached_track(self, track: Track, checkpoint) -> TrackWithStats | None:
        """Handle track that was already processed (checkpoint hit).

        Args:
            track: Track to check
            checkpoint: Current checkpoint state

        Returns:
            Cached stats from repository if found, None if needs reprocessing
        """
        existing_stats = self.repository.get(track.identifier)

        if existing_stats:
            self.logger.debug("Skipping already enriched track: %s", track.identifier)
            event = self.create_event(
                EventType.ITEM_SKIPPED,
                stage_name="Enrichment",
                item_id=track.identifier,
                message=f"Already enriched: {track.title} - {track.primary_artist}",
            )
            self.notify(event)
            return existing_stats

        # Repository lost track - mark for reprocessing
        self.logger.warning(
            "Track %s in checkpoint but missing from repository, reprocessing",
            track.identifier
        )
        checkpoint.processed_ids.remove(track.identifier)
        return None

    def _enrich_track(self, track: Track, checkpoint) -> TrackWithStats | None:
        """Enrich a single track with platform statistics.

        Args:
            track: Track to enrich
            checkpoint: Current checkpoint state

        Returns:
            TrackWithStats if successful, None if failed
        """
        try:
            songstats_id = track.songstats_identifiers.songstats_id

            # Fetch platform stats and peaks
            platform_stats = self._fetch_platform_stats(track, songstats_id, checkpoint)

            # Fetch YouTube data if enabled
            youtube_data = self._fetch_youtube_data(track, songstats_id)

            # Create TrackWithStats model
            track_with_stats = TrackWithStats(
                track=track,
                songstats_identifiers=track.songstats_identifiers,
                platform_stats=platform_stats,
                youtube_data=youtube_data,
            )

            # Mark as processed and notify
            checkpoint.processed_ids.add(track.identifier)
            event = self.create_event(
                EventType.ITEM_COMPLETED,
                stage_name="Enrichment",
                item_id=track.identifier,
                message="Stats fetched successfully",
            )
            self.notify(event)

            self.logger.info(
                "Enriched track: %s - %s (ID: %s)",
                track.primary_artist,
                track.title,
                songstats_id,
            )

            return track_with_stats

        except Exception as error:
            self.logger.exception("Failed to enrich track: %s", track.identifier)
            checkpoint.failed_ids.add(track.identifier)

            event = self.create_event(
                EventType.ITEM_FAILED,
                stage_name="Enrichment",
                item_id=track.identifier,
                message=f"Enrichment failed: {error!s}",
                error=error,
            )
            self.notify(event)

            return None

    def _fetch_platform_stats(
            self, track: Track, songstats_id: str, checkpoint
    ) -> PlatformStats:
        """Fetch platform statistics for a track.

        Args:
            track: Track being enriched
            songstats_id: Songstats track ID
            checkpoint: Current checkpoint state

        Returns:
            PlatformStats model
        """
        # Check which platforms track is available on
        available_platforms = self.songstats.get_available_platforms(songstats_id)
        self.logger.debug(
            "Track %s available on: %s",
            track.title,
            ", ".join(sorted(available_platforms)) if available_platforms else "none"
        )

        # Fetch platform statistics
        platform_stats_data = self.songstats.get_platform_stats(songstats_id)

        if not platform_stats_data:
            self.logger.warning(
                "No platform stats found for: %s (ID: %s)",
                track.title,
                songstats_id,
            )
            checkpoint.failed_ids.add(track.identifier)

            event = self.create_event(
                EventType.WARNING,
                stage_name="Enrichment",
                item_id=track.identifier,
                message="No platform stats found",
            )
            self.notify(event)
            platform_stats_data = {}

        # Fetch and merge historical peaks
        start_date = f"{self.settings.year}-01-01"
        peaks_data = self.songstats.get_historical_peaks(songstats_id, start_date)
        if peaks_data:
            platform_stats_data.update(peaks_data)

        return self._create_platform_stats(platform_stats_data, available_platforms)

    def _fetch_youtube_data(
            self, track: Track, songstats_id: str
    ) -> YouTubeVideoData | None:
        """Fetch YouTube video data for a track.

        Args:
            track: Track being enriched
            songstats_id: Songstats track ID

        Returns:
            YouTubeVideoData if found, None otherwise
        """
        if not self.include_youtube:
            return None

        youtube_results = self.songstats.get_youtube_videos(songstats_id)

        # Validate YouTube data has all required fields
        most_viewed = youtube_results.get("most_viewed") if youtube_results else None
        if not (most_viewed
                and most_viewed.get("ytb_id")
                and most_viewed.get("views") is not None
                and most_viewed.get("channel_name")):
            self.logger.debug("No YouTube data found for: %s", track.title)
            return None

        # Convert API response to YouTubeVideoData model
        most_viewed_video = YouTubeVideo(**youtube_results["most_viewed"])
        video_ids = [video["ytb_id"] for video in youtube_results["all_sources"]]

        return YouTubeVideoData(
            most_viewed=most_viewed_video,
            all_sources=video_ids,
            songstats_identifiers=track.songstats_identifiers,
        )

    def load(self, data: list[TrackWithStats]) -> None:
        """Save enriched tracks to repository.

        Args:
            data: Tracks with platform statistics
        """
        event = self.create_event(
            EventType.STAGE_STARTED,
            stage_name="Enrichment",
            message=f"Saving {len(data)} enriched tracks to repository",
        )
        self.notify(event)

        try:
            # Use batch save for efficiency
            self.repository.save_batch(data)
            self.logger.info("Saved %d enriched tracks to repository", len(data))

            # Notify checkpoint saved
            event = self.create_event(
                EventType.CHECKPOINT_SAVED,
                stage_name="Enrichment",
                message="Enriched tracks saved to repository",
            )

            self.notify(event)

        except Exception as error:
            self.logger.exception("Failed to save enriched tracks to repository")

            event = self.create_event(
                EventType.ERROR,
                stage_name="Enrichment",
                message="Failed to save enriched tracks",
                error=error,
            )

            self.notify(event)
            raise

    @staticmethod
    def _merge_peaks(stats_data: dict, peaks_data: dict) -> None:
        """Merge historical peaks into platform stats.

        Args:
            stats_data: Platform statistics dictionary (modified in place)
            peaks_data: Historical peaks dictionary
        """
        # Example: peaks_data might have {"spotify": {"popularity": {"peak": 85}}}
        # We want to add this as "spotify_popularity_peak" to stats_data

        for platform, metrics in peaks_data.items():
            if not isinstance(metrics, dict):
                continue

            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and "peak" in metric_data:
                    key = f"{platform}_{metric_name}_peak"
                    stats_data[key] = metric_data["peak"]

    def _create_platform_stats(
            self,
            stats_data: dict,
            available_platforms: set[str] | None = None
    ) -> PlatformStats:
        """Create PlatformStats model from API response data.

        Args:
            stats_data: Raw platform statistics from API
            available_platforms: Set of platform names where track exists

        Returns:
            PlatformStats model instance
        """
        # Use from_flat_dict to handle the flat structure from API
        # Pass available_platforms to filter platforms properly
        try:
            return PlatformStats.from_flat_dict(stats_data, available_platforms)

        except (ValidationError, ValueError, KeyError, TypeError) as error:
            self.logger.exception("Failed to create PlatformStats from data: %s", error)
            # Return empty PlatformStats as fallback (defensive coding)
            return PlatformStats()
