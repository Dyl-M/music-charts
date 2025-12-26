"""Unit tests for EnrichmentStage.

Tests platform statistics enrichment via Songstats API.
"""

# Standard library
from unittest.mock import MagicMock

# Third-party
import pytest

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import PlatformStats, TrackWithStats
from msc.pipeline.enrich import EnrichmentStage
from msc.pipeline.observer import EventType


class TestEnrichmentStageInit:
    """Tests for EnrichmentStage initialization."""

    @staticmethod
    def test_sets_songstats_client(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should set songstats client."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        assert stage.songstats is mock_songstats_client

    @staticmethod
    def test_sets_stats_repository(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should set stats repository."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        assert stage.repository is mock_stats_repository

    @staticmethod
    def test_default_include_youtube_true(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should default include_youtube to True."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        assert stage.include_youtube is True

    @staticmethod
    def test_accepts_include_youtube_false(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should accept include_youtube parameter."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            include_youtube=False,
        )

        assert stage.include_youtube is False


class TestEnrichmentStageName:
    """Tests for EnrichmentStage.stage_name property."""

    @staticmethod
    def test_returns_enrichment(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should return 'Enrichment'."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        assert stage.stage_name == "Enrichment"


class TestEnrichmentStageExtract:
    """Tests for EnrichmentStage.extract method."""

    @staticmethod
    def test_returns_empty_without_repository(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should return empty list without track repository."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage.extract()

        assert result == []

    @staticmethod
    def test_loads_from_track_repository(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_track_repository: MagicMock,
            sample_tracks: list[Track],
    ) -> None:
        """Should load tracks from repository."""
        mock_track_repository.get_all.return_value = sample_tracks

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            track_repository=mock_track_repository,
        )

        result = stage.extract()

        assert result == sample_tracks


class TestEnrichmentStageTransform:
    """Tests for EnrichmentStage.transform method."""

    @staticmethod
    def test_returns_empty_for_empty_input(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should return empty list for empty input."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage.transform([])

        assert result == []

    @staticmethod
    def test_filters_tracks_without_songstats_id(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should skip tracks without Songstats ID."""
        # sample_track has no songstats_id
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage.transform([sample_track])

        assert result == []
        mock_songstats_client.get_platform_stats.assert_not_called()

    @staticmethod
    def test_fetches_platform_stats(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track_with_songstats_id: Track,
    ) -> None:
        """Should fetch platform stats for each track."""
        mock_songstats_client.get_available_platforms.return_value = {"spotify"}
        mock_songstats_client.get_platform_stats.return_value = {
            "spotify_streams_total": 1000000
        }
        mock_songstats_client.get_historical_peaks.return_value = {}

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            include_youtube=False,
        )

        result = stage.transform([sample_track_with_songstats_id])

        mock_songstats_client.get_platform_stats.assert_called_once()
        assert len(result) == 1

    @staticmethod
    def test_creates_track_with_stats(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track_with_songstats_id: Track,
    ) -> None:
        """Should create TrackWithStats model."""
        mock_songstats_client.get_available_platforms.return_value = {"spotify"}
        mock_songstats_client.get_platform_stats.return_value = {
            "spotify_streams_total": 1000000
        }
        mock_songstats_client.get_historical_peaks.return_value = {}

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            include_youtube=False,
        )

        result = stage.transform([sample_track_with_songstats_id])

        assert len(result) == 1
        assert isinstance(result[0], TrackWithStats)

    @staticmethod
    def test_skips_already_enriched_tracks(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track_with_songstats_id: Track,
            sample_track_with_stats: TrackWithStats,
    ) -> None:
        """Should skip already enriched tracks."""
        from datetime import datetime
        from msc.storage.checkpoint import CheckpointState

        # Setup checkpoint with track already processed
        now = datetime.now()
        checkpoint = CheckpointState(
            stage_name="enrichment",
            created_at=now,
            last_updated=now,
            processed_ids={sample_track_with_songstats_id.identifier},
            failed_ids=set(),
        )
        mock_checkpoint_manager.load_checkpoint.return_value = checkpoint
        mock_stats_repository.get.return_value = sample_track_with_stats

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage.transform([sample_track_with_songstats_id])

        # Should not call API for already processed
        mock_songstats_client.get_platform_stats.assert_not_called()
        assert len(result) == 1

    @staticmethod
    def test_fetches_youtube_data_when_enabled(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track_with_songstats_id: Track,
    ) -> None:
        """Should fetch YouTube data when enabled."""
        mock_songstats_client.get_available_platforms.return_value = {"spotify"}
        mock_songstats_client.get_platform_stats.return_value = {}
        mock_songstats_client.get_historical_peaks.return_value = {}
        mock_songstats_client.get_youtube_videos.return_value = None

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            include_youtube=True,
        )

        stage.transform([sample_track_with_songstats_id])

        mock_songstats_client.get_youtube_videos.assert_called_once()

    @staticmethod
    def test_skips_youtube_when_disabled(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_track_with_songstats_id: Track,
    ) -> None:
        """Should skip YouTube data when disabled."""
        mock_songstats_client.get_available_platforms.return_value = {"spotify"}
        mock_songstats_client.get_platform_stats.return_value = {}
        mock_songstats_client.get_historical_peaks.return_value = {}

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
            include_youtube=False,
        )

        stage.transform([sample_track_with_songstats_id])

        mock_songstats_client.get_youtube_videos.assert_not_called()


class TestEnrichmentStageLoad:
    """Tests for EnrichmentStage.load method."""

    @staticmethod
    def test_saves_to_repository(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            sample_tracks_with_stats: list[TrackWithStats],
    ) -> None:
        """Should save enriched tracks to repository."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        stage.load(sample_tracks_with_stats)

        mock_stats_repository.save_batch.assert_called_once_with(
            sample_tracks_with_stats
        )

    @staticmethod
    def test_notifies_checkpoint_saved(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_observer,
            sample_tracks_with_stats: list[TrackWithStats],
    ) -> None:
        """Should notify checkpoint saved event."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )
        stage.attach(mock_observer)

        stage.load(sample_tracks_with_stats)

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.CHECKPOINT_SAVED in event_types


class TestEnrichmentStageCreatePlatformStats:
    """Tests for EnrichmentStage._create_platform_stats method."""

    @staticmethod
    def test_returns_empty_for_empty_data(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should return empty PlatformStats for empty data."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage._create_platform_stats({})

        assert isinstance(result, PlatformStats)

    @staticmethod
    def test_handles_invalid_data(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should handle invalid data gracefully."""
        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        # Invalid data - should not raise
        result = stage._create_platform_stats({"invalid_key": "invalid_value"})

        assert isinstance(result, PlatformStats)


class TestEnrichmentStageMergePeaks:
    """Tests for EnrichmentStage._merge_peaks method."""

    @staticmethod
    def test_merges_peaks_into_stats() -> None:
        """Should merge peaks data into stats."""
        stats_data = {"spotify_streams_total": 1000000}
        peaks_data = {"spotify": {"popularity": {"peak": 85}}}

        EnrichmentStage._merge_peaks(stats_data, peaks_data)

        assert "spotify_popularity_peak" in stats_data
        assert stats_data["spotify_popularity_peak"] == 85

    @staticmethod
    def test_handles_empty_peaks() -> None:
        """Should handle empty peaks data."""
        stats_data = {"spotify_streams_total": 1000000}
        peaks_data = {}

        EnrichmentStage._merge_peaks(stats_data, peaks_data)

        # Should not modify stats
        assert stats_data == {"spotify_streams_total": 1000000}

    @staticmethod
    def test_handles_nested_peaks() -> None:
        """Should handle nested peaks structure."""
        stats_data = {}
        peaks_data = {
            "spotify": {"popularity": {"peak": 90}},
            "deezer": {"popularity": {"peak": 75}},
        }

        EnrichmentStage._merge_peaks(stats_data, peaks_data)

        assert stats_data["spotify_popularity_peak"] == 90
        assert stats_data["deezer_popularity_peak"] == 75

    @staticmethod
    def test_ignores_non_dict_metrics() -> None:
        """Should ignore non-dict metrics."""
        stats_data = {}
        peaks_data = {"spotify": "invalid"}

        EnrichmentStage._merge_peaks(stats_data, peaks_data)

        assert stats_data == {}


class TestEnrichmentStageExceptionHandling:
    """Tests for exception handling in EnrichmentStage."""

    @staticmethod
    def test_handles_api_exception_during_transform(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should handle API exception during enrichment."""
        # Create track with songstats ID
        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="test_123",
                songstats_title="Test Track",
            ),
        )

        mock_songstats_client.get_available_platforms.side_effect = RuntimeError("API failure")
        mock_checkpoint_manager.load_checkpoint.return_value = None

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        result = stage.transform([track])

        # Should return empty list when all tracks fail
        assert len(result) == 0

    @staticmethod
    def test_notifies_item_failed_on_exception(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_observer,
    ) -> None:
        """Should notify ITEM_FAILED event on exception."""
        # Create track with songstats ID
        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="test_123",
                songstats_title="Test Track",
            ),
        )

        mock_songstats_client.get_available_platforms.side_effect = RuntimeError("API failure")
        mock_checkpoint_manager.load_checkpoint.return_value = None

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )
        stage.attach(mock_observer)

        stage.transform([track])

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.ITEM_FAILED in event_types

    @staticmethod
    def test_marks_track_as_failed_on_exception(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should mark track as failed in checkpoint on exception."""
        # Create track with songstats ID
        track = Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="test_123",
                songstats_title="Test Track",
            ),
        )

        mock_songstats_client.get_available_platforms.side_effect = RuntimeError("API failure")

        mock_checkpoint = MagicMock()
        mock_checkpoint.processed_ids = set()
        mock_checkpoint.failed_ids = set()
        mock_checkpoint_manager.load_checkpoint.return_value = mock_checkpoint

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        stage.transform([track])

        # Verify checkpoint was saved with failed track
        mock_checkpoint_manager.save_checkpoint.assert_called()


class TestEnrichmentStageLoadErrors:
    """Tests for error handling in EnrichmentStage.load method."""

    @staticmethod
    def test_handles_repository_exception(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
    ) -> None:
        """Should raise exception when repository fails."""
        mock_stats_repository.save_batch.side_effect = RuntimeError("Save failed")

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )

        with pytest.raises(RuntimeError, match="Save failed"):
            stage.load([])

    @staticmethod
    def test_notifies_error_on_repository_failure(
            mock_songstats_client: MagicMock,
            mock_stats_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_observer,
    ) -> None:
        """Should notify ERROR event when repository fails."""
        mock_stats_repository.save_batch.side_effect = RuntimeError("Save failed")

        stage = EnrichmentStage(
            songstats_client=mock_songstats_client,
            stats_repository=mock_stats_repository,
            checkpoint_manager=mock_checkpoint_manager,
        )
        stage.attach(mock_observer)

        with pytest.raises(RuntimeError):
            stage.load([])

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.ERROR in event_types
