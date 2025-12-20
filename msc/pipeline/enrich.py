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
from msc.models.youtube import YouTubeVideoData
from msc.pipeline.base import PipelineStage
from msc.pipeline.observer import EventType, Observable
from msc.storage.checkpoint import CheckpointManager
from msc.storage.json_repository import JSONStatsRepository
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
    ) -> None:
        """Initialize enrichment stage.

        Args:
            songstats_client: Client for Songstats API
            stats_repository: Repository for storing enriched tracks
            checkpoint_manager: Manager for checkpoint state
            include_youtube: Whether to fetch YouTube video data
        """
        Observable.__init__(self)
        self.songstats = songstats_client
        self.repository = stats_repository
        self.checkpoint_mgr = checkpoint_manager
        self.include_youtube = include_youtube
        self.settings = get_settings()
        self.logger = get_logger(__name__)

    @property
    def stage_name(self) -> str:
        """Human-readable name for this pipeline stage."""
        return "Enrichment"

    def extract(self) -> list[Track]:
        """Extract tracks from input (not used in this stage).

        This stage receives tracks from previous stage output.
        """
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

            # Skip if already processed
            if track_id in checkpoint.processed_ids:
                # Load from repository
                existing_stats = self.repository.get(track_id)

                if existing_stats:
                    # Happy path - use cached track
                    self.logger.debug("Skipping already enriched track: %s", track_id)

                    # Notify skipped
                    event = self.create_event(
                        EventType.ITEM_SKIPPED,
                        stage_name="Enrichment",
                        item_id=track_id,
                        message=f"Already enriched: {track.title} - {track.primary_artist}",
                    )
                    self.notify(event)
                    enriched_tracks.append(existing_stats)
                    continue

                # Repository lost track - reprocess
                self.logger.warning(
                    "Track %s in checkpoint but missing from repository, reprocessing",
                    track_id
                )
                checkpoint.processed_ids.remove(track_id)
                # Fall through to processing logic

            # Notify processing
            event = self.create_event(
                EventType.ITEM_PROCESSING,
                stage_name="Enrichment",
                item_id=track_id,
                message=f"Fetching stats: {track.title} - {track.primary_artist}",
            )

            self.notify(event)

            try:
                songstats_id = track.songstats_identifiers.songstats_id

                # Fetch platform statistics
                platform_stats_data = self.songstats.get_platform_stats(songstats_id)

                if not platform_stats_data:
                    self.logger.warning(
                        "No platform stats found for: %s (ID: %s)",
                        track.title,
                        songstats_id,
                    )
                    checkpoint.failed_ids.add(track_id)

                    # Notify warning
                    event = self.create_event(
                        EventType.WARNING,
                        stage_name="Enrichment",
                        item_id=track_id,
                        message="No platform stats found",
                    )
                    self.notify(event)

                    # Continue with empty stats (defensive)
                    platform_stats_data = {}

                # Fetch historical peaks (for popularity metrics)
                peaks_data = self.songstats.get_historical_peaks(songstats_id)

                # Merge peaks into platform stats
                if peaks_data:
                    self._merge_peaks(platform_stats_data, peaks_data)

                # Create PlatformStats model from data
                platform_stats = self._create_platform_stats(platform_stats_data)

                # Optionally fetch YouTube video data
                youtube_data: YouTubeVideoData | None = None

                if self.include_youtube:
                    youtube_results = self.songstats.get_youtube_videos(songstats_id)

                    if youtube_results:
                        youtube_data = YouTubeVideoData.from_songstats_api(youtube_results)
                    else:
                        self.logger.debug("No YouTube data found for: %s", track.title)

                # Create TrackWithStats model (nested structure)
                track_with_stats = TrackWithStats(
                    track=track,  # Nested Track object
                    songstats_identifiers=track.songstats_identifiers,  # Nested SongstatsIdentifiers
                    platform_stats=platform_stats,
                )

                enriched_tracks.append(track_with_stats)

                # Mark as processed
                checkpoint.processed_ids.add(track_id)

                # Notify success
                event = self.create_event(
                    EventType.ITEM_COMPLETED,
                    stage_name="Enrichment",
                    item_id=track_id,
                    message="Stats fetched successfully",
                )
                self.notify(event)

                self.logger.info(
                    "Enriched track: %s - %s (ID: %s)",
                    track.primary_artist,
                    track.title,
                    songstats_id,
                )

            except Exception as error:
                self.logger.exception("Failed to enrich track: %s", track_id)

                # Mark as failed
                checkpoint.failed_ids.add(track_id)

                # Notify error
                event = self.create_event(
                    EventType.ITEM_FAILED,
                    stage_name="Enrichment",
                    item_id=track_id,
                    message=f"Enrichment failed: {error!s}",
                    error=error,
                )

                self.notify(event)

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

    def _create_platform_stats(self, stats_data: dict) -> PlatformStats:
        """Create PlatformStats model from API response data.

        Args:
            stats_data: Raw platform statistics from API

        Returns:
            PlatformStats model instance
        """
        # Use from_flat_dict to handle the flat structure from API
        try:
            return PlatformStats.from_flat_dict(stats_data)

        except (ValidationError, ValueError, KeyError, TypeError) as error:
            self.logger.exception("Failed to create PlatformStats from data: %s", error)
            # Return empty PlatformStats as fallback (defensive coding)
            return PlatformStats()
