"""Unit tests for ExtractionStage.

Tests MusicBee extraction and Songstats ID resolution.
"""

# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.models.track import Track
from msc.pipeline.extract import ExtractionStage
from msc.pipeline.observer import EventType


class TestExtractionStageInit:
    """Tests for ExtractionStage initialization."""

    @staticmethod
    def test_sets_clients(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should set all client instances."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        assert stage.musicbee is mock_musicbee_client
        assert stage.songstats is mock_songstats_client
        assert stage.repository is mock_track_repository

    @staticmethod
    def test_uses_default_playlist_name(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should use default playlist name from settings."""
        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = ExtractionStage(
                musicbee_client=mock_musicbee_client,
                songstats_client=mock_songstats_client,
                track_repository=mock_track_repository,
                checkpoint_manager=mock_checkpoint_manager,
                review_queue=mock_review_queue,
            )

            assert stage.playlist_name == "✅ 2024 Selection"

    @staticmethod
    def test_accepts_custom_playlist_name(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should accept custom playlist name."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
            playlist_name="Custom Playlist",
        )

        assert stage.playlist_name == "Custom Playlist"


class TestExtractionStageName:
    """Tests for ExtractionStage.stage_name property."""

    @staticmethod
    def test_returns_extraction(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should return 'Extraction'."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        assert stage.stage_name == "Extraction"


class TestExtractionStageExtract:
    """Tests for ExtractionStage.extract method."""

    @staticmethod
    def test_finds_playlist_by_name(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should find playlist by name."""
        mock_musicbee_client.find_playlist_by_name.return_value = "12345"
        mock_musicbee_client.get_playlist_tracks.return_value = []

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
            playlist_name="Test Playlist",
        )

        stage.extract()

        mock_musicbee_client.find_playlist_by_name.assert_called_once_with(
            "Test Playlist", exact_match=True
        )

    @staticmethod
    def test_returns_empty_when_playlist_not_found(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should return empty list when playlist not found."""
        mock_musicbee_client.find_playlist_by_name.return_value = None

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.extract()

        assert result == []

    @staticmethod
    def test_filters_tracks_by_year(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should filter tracks by year."""
        mock_musicbee_client.find_playlist_by_name.return_value = "12345"
        mock_musicbee_client.get_playlist_tracks.return_value = [
            {"title": "Track 2024", "artist_list": ["Artist"], "year": 2024},
            {"title": "Track 2023", "artist_list": ["Artist"], "year": 2023},
        ]

        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = ExtractionStage(
                musicbee_client=mock_musicbee_client,
                songstats_client=mock_songstats_client,
                track_repository=mock_track_repository,
                checkpoint_manager=mock_checkpoint_manager,
                review_queue=mock_review_queue,
            )

            result = stage.extract()

            assert len(result) == 1
            assert result[0].title == "Track 2024"

    @staticmethod
    def test_converts_to_track_models(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should convert raw data to Track models."""
        mock_musicbee_client.find_playlist_by_name.return_value = "12345"
        mock_musicbee_client.get_playlist_tracks.return_value = [
            {
                "title": "Test Track",
                "artist_list": ["Test Artist"],
                "year": 2024,
                "genre": "Electronic",
            }
        ]

        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = ExtractionStage(
                musicbee_client=mock_musicbee_client,
                songstats_client=mock_songstats_client,
                track_repository=mock_track_repository,
                checkpoint_manager=mock_checkpoint_manager,
                review_queue=mock_review_queue,
            )

            result = stage.extract()

            assert len(result) == 1
            assert isinstance(result[0], Track)
            assert result[0].title == "Test Track"


class TestExtractionStageTransform:
    """Tests for ExtractionStage.transform method."""

    @staticmethod
    def test_returns_empty_for_empty_input(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should return empty list for empty input."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([])

        assert result == []

    @staticmethod
    def test_searches_songstats_for_each_track(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should search Songstats for each track."""
        mock_songstats_client.search_track.return_value = []

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        stage.transform([sample_track])

        mock_songstats_client.search_track.assert_called_once()

    @staticmethod
    def test_adds_songstats_id_when_found(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should add Songstats ID when found."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "found123",
                "title": "Test Track",
                "artists": [],
                "labels": [],
            }
        ]
        mock_songstats_client.get_track_info.return_value = None

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        assert len(result) == 1
        assert result[0].songstats_identifiers.songstats_id == "found123"

    @staticmethod
    def test_adds_to_review_queue_when_not_found(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should add to review queue when no match found."""
        mock_songstats_client.search_track.return_value = []

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        stage.transform([sample_track])

        mock_review_queue.add.assert_called_once()

    @staticmethod
    def test_skips_already_processed_tracks(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should skip already processed tracks."""
        from datetime import datetime
        from msc.storage.checkpoint import CheckpointState

        # Setup checkpoint with track already processed
        now = datetime.now()
        checkpoint = CheckpointState(
            stage_name="extraction",
            created_at=now,
            last_updated=now,
            processed_ids={sample_track.identifier},
            failed_ids=set(),
        )
        mock_checkpoint_manager.load_checkpoint.return_value = checkpoint
        mock_track_repository.get.return_value = sample_track

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        # Should not call search_track for already processed
        mock_songstats_client.search_track.assert_not_called()
        assert len(result) == 1


class TestExtractionStageValidateTrackMatch:
    """Tests for ExtractionStage._validate_track_match method."""

    @staticmethod
    def test_rejects_karaoke_matches(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should reject matches containing 'karaoke'."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = {"title": "Test Track (Karaoke Version)"}

        is_valid, reason = stage._validate_track_match(sample_track, result)

        assert is_valid is False
        assert "karaoke" in reason.lower()

    @staticmethod
    def test_rejects_instrumental_matches(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should reject matches containing 'instrumental'."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = {"title": "Test Track (Instrumental)"}

        is_valid, reason = stage._validate_track_match(sample_track, result)

        assert is_valid is False
        assert "instrumental" in reason.lower()

    @staticmethod
    def test_accepts_valid_matches(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should accept valid matches."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = {"title": "Test Track (Original Mix)"}

        is_valid, reason = stage._validate_track_match(sample_track, result)

        assert is_valid is True
        assert reason == ""


class TestExtractionStageNormalizeArtists:
    """Tests for ExtractionStage._normalize_artists method."""

    @staticmethod
    def test_removes_duplicates() -> None:
        """Should remove duplicate artists."""
        artists = ["Artist A", "artist a", "Artist B"]

        result = ExtractionStage._normalize_artists(artists)

        assert len(result) == 2

    @staticmethod
    def test_sorts_alphabetically() -> None:
        """Should sort artists alphabetically."""
        artists = ["Zebra", "Apple", "Mango"]

        result = ExtractionStage._normalize_artists(artists)

        assert result == ["apple", "mango", "zebra"]

    @staticmethod
    def test_handles_empty_list() -> None:
        """Should handle empty list."""
        result = ExtractionStage._normalize_artists([])

        assert result == []

    @staticmethod
    def test_filters_empty_strings() -> None:
        """Should filter out empty strings."""
        artists = ["Artist A", "", "Artist B"]

        result = ExtractionStage._normalize_artists(artists)

        assert "" not in result


class TestExtractionStageLoad:
    """Tests for ExtractionStage.load method."""

    @staticmethod
    def test_saves_tracks_to_repository(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_tracks: list[Track],
    ) -> None:
        """Should save all tracks to repository."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        stage.load(sample_tracks)

        assert mock_track_repository.add.call_count == len(sample_tracks)

    @staticmethod
    def test_notifies_checkpoint_saved(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            mock_observer,
            sample_tracks: list[Track],
    ) -> None:
        """Should notify checkpoint saved event."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )
        stage.attach(mock_observer)

        stage.load(sample_tracks)

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.CHECKPOINT_SAVED in event_types

    @staticmethod
    def test_handles_repository_exception(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_tracks: list[Track],
    ) -> None:
        """Should raise exception when repository fails."""
        mock_track_repository.add.side_effect = RuntimeError("Repository error")

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        with pytest.raises(RuntimeError, match="Repository error"):
            stage.load(sample_tracks)


class TestExtractionStageTransformRejectKeywords:
    """Tests for transform method reject keyword handling."""

    @staticmethod
    def test_rejects_match_with_cover_keyword(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should reject matches containing 'cover' keyword."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "cover123",
                "title": "Test Track (Cover Version)",
                "artists": [],
                "labels": [],
            }
        ]

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        # Track should still be returned but added to review queue
        assert len(result) == 1
        mock_review_queue.add.assert_called_once()
        call_kwargs = mock_review_queue.add.call_args.kwargs
        assert "Rejected" in call_kwargs.get("reason", "")

    @staticmethod
    def test_rejects_match_with_tribute_keyword(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should reject matches containing 'tribute' keyword."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "tribute123",
                "title": "Test Track - A Tribute",
                "artists": [],
                "labels": [],
            }
        ]

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        assert len(result) == 1
        mock_review_queue.add.assert_called_once()


class TestExtractionStageTransformISRC:
    """Tests for ISRC extraction in transform method."""

    @staticmethod
    def test_extracts_isrc_from_track_info(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should extract ISRC from track info links."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "found123",
                "title": "Test Track",
                "artists": [],
                "labels": [],
            }
        ]
        mock_songstats_client.get_track_info.return_value = {
            "track_info": {
                "links": [
                    {"platform": "spotify", "isrc": "USRC12345678"},
                ]
            }
        }

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        assert len(result) == 1
        assert result[0].songstats_identifiers.isrc == "USRC12345678"

    @staticmethod
    def test_handles_missing_isrc(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should handle missing ISRC in track info."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "found123",
                "title": "Test Track",
                "artists": [],
                "labels": [],
            }
        ]
        mock_songstats_client.get_track_info.return_value = {
            "track_info": {
                "links": [
                    {"platform": "spotify"},  # No ISRC
                ]
            }
        }

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        assert len(result) == 1
        assert result[0].songstats_identifiers.isrc is None

    @staticmethod
    def test_handles_empty_links(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should handle empty links list in track info."""
        mock_songstats_client.search_track.return_value = [
            {
                "songstats_track_id": "found123",
                "title": "Test Track",
                "artists": [],
                "labels": [],
            }
        ]
        mock_songstats_client.get_track_info.return_value = {
            "track_info": {
                "links": []
            }
        }

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        assert len(result) == 1
        assert result[0].songstats_identifiers.isrc is None


class TestExtractionStageTransformExceptions:
    """Tests for exception handling in transform method."""

    @staticmethod
    def test_handles_songstats_search_exception(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            sample_track: Track,
    ) -> None:
        """Should handle Songstats search exception gracefully."""
        mock_songstats_client.search_track.side_effect = RuntimeError("API error")

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )

        result = stage.transform([sample_track])

        # Track should still be returned
        assert len(result) == 1
        # Should be added to review queue
        mock_review_queue.add.assert_called_once()
        call_kwargs = mock_review_queue.add.call_args.kwargs
        assert "Error" in call_kwargs.get("reason", "")

    @staticmethod
    def test_notifies_item_failed_on_exception(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            mock_observer,
            sample_track: Track,
    ) -> None:
        """Should notify ITEM_FAILED event on exception."""
        mock_songstats_client.search_track.side_effect = RuntimeError("API error")

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )
        stage.attach(mock_observer)

        stage.transform([sample_track])

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.ITEM_FAILED in event_types


class TestExtractionStageExtractException:
    """Tests for exception handling in extract method."""

    @staticmethod
    def test_notifies_stage_failed_on_exception(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            mock_observer,
    ) -> None:
        """Should notify STAGE_FAILED event on extraction exception."""
        mock_musicbee_client.find_playlist_by_name.side_effect = RuntimeError("MusicBee error")

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )
        stage.attach(mock_observer)

        with pytest.raises(RuntimeError, match="MusicBee error"):
            stage.extract()

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.STAGE_FAILED in event_types


class TestExtractionStageTrackLimit:
    """Tests for track limit functionality."""

    @staticmethod
    def test_accepts_track_limit_parameter(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should accept track_limit parameter."""
        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
            track_limit=5,
        )

        assert stage.track_limit == 5

    @staticmethod
    def test_limits_tracks_when_extracting(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
    ) -> None:
        """Should limit extracted tracks to track_limit."""
        mock_musicbee_client.find_playlist_by_name.return_value = "12345"
        mock_musicbee_client.get_playlist_tracks.return_value = [
            {"title": f"Track {i}", "artist_list": ["Artist"], "year": 2024}
            for i in range(10)
        ]

        with patch("msc.pipeline.extract.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = ExtractionStage(
                musicbee_client=mock_musicbee_client,
                songstats_client=mock_songstats_client,
                track_repository=mock_track_repository,
                checkpoint_manager=mock_checkpoint_manager,
                review_queue=mock_review_queue,
                track_limit=3,
            )

            result = stage.extract()

            assert len(result) == 3


class TestExtractionStageLoadError:
    """Tests for error handling in load method."""

    @staticmethod
    def test_notifies_error_on_repository_failure(
            mock_musicbee_client: MagicMock,
            mock_songstats_client: MagicMock,
            mock_track_repository: MagicMock,
            mock_checkpoint_manager: MagicMock,
            mock_review_queue: MagicMock,
            mock_observer,
            sample_tracks: list[Track],
    ) -> None:
        """Should notify ERROR event when repository fails."""
        mock_track_repository.add.side_effect = RuntimeError("Save failed")

        stage = ExtractionStage(
            musicbee_client=mock_musicbee_client,
            songstats_client=mock_songstats_client,
            track_repository=mock_track_repository,
            checkpoint_manager=mock_checkpoint_manager,
            review_queue=mock_review_queue,
        )
        stage.attach(mock_observer)

        with pytest.raises(RuntimeError):
            stage.load(sample_tracks)

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.ERROR in event_types
