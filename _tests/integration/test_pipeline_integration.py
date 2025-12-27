"""Integration tests for full pipeline execution.

Tests the orchestrator.run() method which coordinates all pipeline stages.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.clients import create_mock_songstats_client
from msc.models.track import Track
from msc.pipeline.observer import EventType, PipelineEvent, PipelineObserver
from msc.pipeline.orchestrator import PipelineOrchestrator


class MockObserver(PipelineObserver):
    """Observer that collects events for testing."""

    def __init__(self) -> None:
        """Initialize mock observer."""
        self.events: list[PipelineEvent] = []

    def on_event(self, event: PipelineEvent) -> None:
        """Collect events."""
        self.events.append(event)

    def get_events_by_type(self, event_type: EventType) -> list[PipelineEvent]:
        """Filter events by type."""
        return [e for e in self.events if e.event_type == event_type]


class TestPipelineOrchestratorRun:
    """Tests for PipelineOrchestrator.run() method - CRITICAL for coverage."""

    @staticmethod
    def test_run_initializes_with_test_mode(tmp_path: Path) -> None:
        """Should initialize orchestrator with test_mode and track_limit."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.test_library_path = tmp_path / "test_library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            # Create test library file
            (tmp_path / "test_library.xml").write_text("<dict></dict>", encoding="utf-8")

            with patch("msc.pipeline.orchestrator.MusicBeeClient"):
                orchestrator = PipelineOrchestrator(
                    data_dir=tmp_path,
                    test_mode=True,
                    track_limit=5,
                    new_run=True,
                )

                assert orchestrator.test_mode is True
                assert orchestrator.track_limit == 5

    @staticmethod
    def test_run_emits_pipeline_started_event(tmp_path: Path) -> None:
        """Should emit PIPELINE_STARTED event when run() is called."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            # Mock extraction to return empty list
            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
            )

            # Add test observer
            observer = MockObserver()
            orchestrator.attach(observer)

            # Run pipeline with only extraction
            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            # Check for PIPELINE_STARTED event
            started_events = observer.get_events_by_type(EventType.PIPELINE_STARTED)
            assert len(started_events) >= 1
            assert "Starting music-charts pipeline" in started_events[0].message

    @staticmethod
    def test_run_emits_pipeline_completed_event(tmp_path: Path) -> None:
        """Should emit PIPELINE_COMPLETED event on success."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
            )

            observer = MockObserver()
            orchestrator.attach(observer)

            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            completed_events = observer.get_events_by_type(EventType.PIPELINE_COMPLETED)
            assert len(completed_events) >= 1
            assert "Pipeline completed successfully" in completed_events[0].message

    @staticmethod
    def test_run_extraction_only(tmp_path: Path) -> None:
        """Should run only extraction stage when specified."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            # Create sample tracks
            sample_tracks = [
                Track(title="Track 1", artist_list=["Artist 1"], year=2024),
                Track(title="Track 2", artist_list=["Artist 2"], year=2024),
            ]
            mock_stage = MagicMock()
            mock_stage.run.return_value = sample_tracks
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
            )

            result = orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            # Should have called extraction stage
            mock_stage.run.assert_called_once()
            # Result should be None (no ranking)
            assert result is None

    @staticmethod
    def test_run_with_track_limit_passed_to_extraction(tmp_path: Path) -> None:
        """Should pass track_limit to ExtractionStage."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract_class.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
                track_limit=3,
            )

            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            # Verify track_limit was passed to ExtractionStage
            call_kwargs = mock_extract_class.call_args.kwargs
            assert call_kwargs.get("track_limit") == 3

    @staticmethod
    def test_run_handles_stage_exception(tmp_path: Path) -> None:
        """Should emit PIPELINE_FAILED event when stage throws exception."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            # Make extraction raise exception
            mock_stage = MagicMock()
            mock_stage.run.side_effect = RuntimeError("Test extraction failure")
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
            )

            observer = MockObserver()
            orchestrator.attach(observer)

            with pytest.raises(RuntimeError, match="Test extraction failure"):
                orchestrator.run(
                    run_extraction=True,
                    run_enrichment=False,
                    run_ranking=False,
                )

            # Should have emitted PIPELINE_FAILED
            failed_events = observer.get_events_by_type(EventType.PIPELINE_FAILED)
            assert len(failed_events) >= 1

    @staticmethod
    def test_run_attaches_observers_to_stages(tmp_path: Path) -> None:
        """Should attach pipeline observers to each stage."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.ExtractionStage") as mock_extract:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2024
            mock_settings_obj.musicbee_library = tmp_path / "library.xml"
            mock_settings_obj.songstats_api_key = "test_key"
            mock_settings_obj.songstats_rate_limit = 10
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings.return_value = mock_settings_obj

            mock_stage = MagicMock()
            mock_stage.run.return_value = []
            mock_extract.return_value = mock_stage

            orchestrator = PipelineOrchestrator(
                data_dir=tmp_path,
                new_run=True,
            )

            orchestrator.run(
                run_extraction=True,
                run_enrichment=False,
                run_ranking=False,
            )

            # Stage should have had attach called for each observer
            assert mock_stage.attach.called


class TestExtractionStageIntegration:
    """Integration tests for ExtractionStage with real test data."""

    @staticmethod
    def test_extraction_applies_track_limit() -> None:
        """Should limit tracks when track_limit is set."""
        from msc.pipeline.extract import ExtractionStage

        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.year = 2024
            mock_settings.return_value = mock_settings_obj

            # Mock clients
            mock_musicbee = MagicMock()
            mock_musicbee.find_playlist_by_name.return_value = "12345"
            mock_musicbee.get_playlist_tracks.return_value = [
                {"title": f"Track {i}", "artist_list": [f"Artist {i}"], "year": 2024}
                for i in range(10)
            ]

            mock_songstats = MagicMock()
            mock_repository = MagicMock()
            mock_checkpoint = MagicMock()
            mock_checkpoint.load_checkpoint.return_value = None
            mock_review = MagicMock()

            stage = ExtractionStage(
                musicbee_client=mock_musicbee,
                songstats_client=mock_songstats,
                track_repository=mock_repository,
                checkpoint_manager=mock_checkpoint,
                review_queue=mock_review,
                playlist_name="Test Playlist",
                track_limit=3,
            )

            # Run extraction
            tracks = stage.extract()

            # Should be limited to 3 tracks
            assert len(tracks) == 3

    @staticmethod
    def test_extraction_without_limit_returns_all() -> None:
        """Should return all tracks when no limit is set."""
        from msc.pipeline.extract import ExtractionStage

        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings_obj = MagicMock()
            mock_settings_obj.year = 2024
            mock_settings.return_value = mock_settings_obj

            mock_musicbee = MagicMock()
            mock_musicbee.find_playlist_by_name.return_value = "12345"
            mock_musicbee.get_playlist_tracks.return_value = [
                {"title": f"Track {i}", "artist_list": [f"Artist {i}"], "year": 2024}
                for i in range(10)
            ]

            mock_songstats = MagicMock()
            mock_repository = MagicMock()
            mock_checkpoint = MagicMock()
            mock_checkpoint.load_checkpoint.return_value = None
            mock_review = MagicMock()

            stage = ExtractionStage(
                musicbee_client=mock_musicbee,
                songstats_client=mock_songstats,
                track_repository=mock_repository,
                checkpoint_manager=mock_checkpoint,
                review_queue=mock_review,
                playlist_name="Test Playlist",
                track_limit=None,  # No limit
            )

            tracks = stage.extract()

            # Should return all 10 tracks
            assert len(tracks) == 10


class TestMockSongstatsClient:
    """Tests for the mock Songstats client factory."""

    @staticmethod
    def test_create_mock_returns_configured_mock() -> None:
        """Should return a properly configured mock client."""
        mock = create_mock_songstats_client()

        # Test search_track
        results = mock.search_track("test", "artist")
        assert isinstance(results, list)
        assert len(results) > 0
        assert "songstats_track_id" in results[0]

        # Test get_track_info
        info = mock.get_track_info("test_id")
        assert isinstance(info, dict)
        assert "title" in info

        # Test get_available_platforms
        platforms = mock.get_available_platforms("test_id")
        assert isinstance(platforms, set)
        assert "spotify" in platforms

        # Test get_platform_stats
        stats = mock.get_platform_stats("test_id", ["spotify"])
        assert isinstance(stats, dict)
        assert "spotify" in stats

        # Test close
        mock.close()  # Should not raise


class TestOrchestratorFullPipeline:
    """Tests for full pipeline execution across all stages."""

    @staticmethod
    def test_run_enrichment_stage_with_tracks(tmp_path: Path) -> None:
        """Should run enrichment stage with extracted tracks."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.EnrichmentStage") as mock_enrich:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Mock enrichment stage
            mock_stage = MagicMock()
            mock_stage.transform.return_value = []
            mock_enrich.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            # Run enrichment only (no extraction, no ranking)
            orchestrator.run(
                run_extraction=False,
                run_enrichment=True,
                run_ranking=False,
            )

            # Verify enrichment stage was called
            mock_stage.transform.assert_called_once()
            mock_stage.load.assert_called_once()

    @staticmethod
    def test_run_ranking_stage_with_enriched_tracks(tmp_path: Path) -> None:
        """Should run ranking stage with enriched tracks."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.RankingStage") as mock_rank:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Mock ranking stage
            mock_stage = MagicMock()
            mock_results = MagicMock()
            mock_results.rankings = []
            mock_stage.transform.return_value = mock_results
            mock_rank.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            # Run ranking only
            result = orchestrator.run(
                run_extraction=False,
                run_enrichment=False,
                run_ranking=True,
            )

            # Verify ranking stage was called
            mock_stage.transform.assert_called_once()
            mock_stage.load.assert_called_once()
            assert result == mock_results

    @staticmethod
    def test_loads_tracks_from_repository_when_skipping_extraction(tmp_path: Path) -> None:
        """Should load tracks from repository when extraction is skipped."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.EnrichmentStage") as mock_enrich:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Mock enrichment stage
            mock_stage = MagicMock()
            mock_stage.transform.return_value = []
            mock_enrich.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            # Mock track repository to return some tracks
            orchestrator.track_repository = MagicMock()
            orchestrator.track_repository.get_all.return_value = [MagicMock()]

            # Run enrichment only (extraction skipped)
            orchestrator.run(
                run_extraction=False,
                run_enrichment=True,
                run_ranking=False,
            )

            # Verify tracks were loaded from repository
            orchestrator.track_repository.get_all.assert_called_once()

    @staticmethod
    def test_loads_enriched_tracks_from_repository_when_skipping_enrichment(tmp_path: Path) -> None:
        """Should load enriched tracks from repository when enrichment is skipped."""
        with patch("msc.pipeline.orchestrator.get_settings") as mock_settings, \
                patch("msc.pipeline.orchestrator.MusicBeeClient"), \
                patch("msc.pipeline.orchestrator.SongstatsClient"), \
                patch("msc.pipeline.orchestrator.RankingStage") as mock_rank:
            mock_settings.return_value.data_dir = tmp_path
            mock_settings.return_value.year = 2024
            mock_settings.return_value.musicbee_library = tmp_path / "library.xml"
            mock_settings.return_value.songstats_api_key = "test_key"
            mock_settings.return_value.songstats_rate_limit = 10
            mock_settings.return_value.output_dir = tmp_path / "output"
            (tmp_path / "library.xml").write_text("<library/>", encoding="utf-8")

            # Mock ranking stage
            mock_stage = MagicMock()
            mock_results = MagicMock()
            mock_results.rankings = []
            mock_stage.transform.return_value = mock_results
            mock_rank.return_value = mock_stage

            orchestrator = PipelineOrchestrator(new_run=True)

            # Mock stats repository to return some tracks
            orchestrator.stats_repository = MagicMock()
            orchestrator.stats_repository.get_all.return_value = [MagicMock()]

            # Run ranking only (enrichment skipped)
            orchestrator.run(
                run_extraction=False,
                run_enrichment=False,
                run_ranking=True,
            )

            # Verify enriched tracks were loaded from repository
            orchestrator.stats_repository.get_all.assert_called_once()
