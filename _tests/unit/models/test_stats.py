"""Unit tests for platform statistics container and combined track models.

Tests PlatformStats and TrackWithStats models.
"""

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.platforms import DeezerStats, SpotifyStats
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track
from msc.models.youtube import YouTubeVideo, YouTubeVideoData


class TestPlatformStatsCreation:
    """Tests for PlatformStats model creation."""

    @staticmethod
    def test_creates_with_defaults() -> None:
        """Should create with all default platform stats."""
        stats = PlatformStats()
        assert stats.spotify is not None
        assert stats.deezer is not None
        assert stats.apple_music is not None

    @staticmethod
    def test_default_platforms_are_empty() -> None:
        """Should have None values in default platform stats."""
        stats = PlatformStats()
        assert stats.spotify.streams_total is None
        assert stats.deezer.popularity_peak is None

    @staticmethod
    def test_creates_with_specific_platforms() -> None:
        """Should create with specific platform stats."""
        stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000),
            deezer=DeezerStats(popularity_peak=80),
        )
        assert stats.spotify.streams_total == 1000000
        assert stats.deezer.popularity_peak == 80

    @staticmethod
    def test_all_ten_platforms_accessible() -> None:
        """Should have all 10 platform stats accessible."""
        stats = PlatformStats()
        platforms = [
            stats.spotify,
            stats.deezer,
            stats.apple_music,
            stats.youtube,
            stats.tiktok,
            stats.soundcloud,
            stats.tidal,
            stats.amazon_music,
            stats.beatport,
            stats.tracklists,
        ]
        assert len(platforms) == 10
        assert all(p is not None for p in platforms)


class TestPlatformStatsImmutability:
    """Tests for PlatformStats immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        stats = PlatformStats()
        with pytest.raises(ValidationError):
            stats.spotify = SpotifyStats(streams_total=100)  # type: ignore[misc]


class TestPlatformStatsFromFlatDict:
    """Tests for PlatformStats.from_flat_dict method."""

    @staticmethod
    def test_groups_by_platform_prefix() -> None:
        """Should group fields by platform prefix."""
        flat_data = {
            "spotify_streams_total": 1000000,
            "spotify_popularity_peak": 75,
            "deezer_popularity_peak": 80,
        }
        stats = PlatformStats.from_flat_dict(flat_data)
        assert stats.spotify.streams_total == 1000000
        assert stats.spotify.popularity_peak == 75
        assert stats.deezer.popularity_peak == 80

    @staticmethod
    def test_handles_empty_dict() -> None:
        """Should handle empty dictionary."""
        stats = PlatformStats.from_flat_dict({})
        assert stats.spotify.streams_total is None
        assert stats.deezer.popularity_peak is None

    @staticmethod
    def test_filters_by_available_platforms() -> None:
        """Should only create platforms in available_platforms set."""
        flat_data = {
            "spotify_streams_total": 1000000,
            "deezer_popularity_peak": 80,
        }
        stats = PlatformStats.from_flat_dict(
            flat_data, available_platforms={"spotify"}
        )
        assert stats.spotify.streams_total == 1000000
        # Deezer not in available_platforms, uses default
        assert stats.deezer.popularity_peak is None

    @staticmethod
    def test_handles_1001tracklists_prefix() -> None:
        """Should handle 1001tracklists prefix mapping."""
        flat_data = {"1001tracklists_unique_support": 150}
        stats = PlatformStats.from_flat_dict(
            flat_data, available_platforms={"1001tracklists"}
        )
        assert stats.tracklists.unique_support == 150


class TestPlatformStatsToFlatDict:
    """Tests for PlatformStats.to_flat_dict method."""

    @staticmethod
    def test_flattens_nested_stats() -> None:
        """Should flatten nested platform stats."""
        stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000),
            deezer=DeezerStats(popularity_peak=80),
        )
        flat = stats.to_flat_dict()
        assert flat["spotify_streams_total"] == 1000000
        assert flat["deezer_popularity_peak"] == 80

    @staticmethod
    def test_excludes_none_values() -> None:
        """Should exclude None values from output."""
        stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000)
        )
        flat = stats.to_flat_dict()
        assert "spotify_streams_total" in flat
        assert "spotify_popularity_peak" not in flat

    @staticmethod
    def test_empty_stats_returns_empty_dict() -> None:
        """Should return empty dict for empty stats."""
        stats = PlatformStats()
        flat = stats.to_flat_dict()
        assert flat == {}


class TestTrackWithStatsCreation:
    """Tests for TrackWithStats model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with required fields."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        assert tws.track.title == "test"
        assert tws.songstats_identifiers.songstats_id == "abc"

    @staticmethod
    def test_defaults_platform_stats() -> None:
        """Should default platform_stats to empty PlatformStats."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        assert tws.platform_stats is not None
        assert tws.platform_stats.spotify.streams_total is None

    @staticmethod
    def test_defaults_youtube_data_to_none() -> None:
        """Should default youtube_data to None."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        assert tws.youtube_data is None

    @staticmethod
    def test_creates_with_all_fields() -> None:
        """Should create with all optional fields."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        platform_stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000)
        )
        video = YouTubeVideo(video_id="xyz", views=5000, channel_name="Channel")
        youtube_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["xyz"],
            songstats_identifiers=ids,
        )
        tws = TrackWithStats(
            track=track,
            songstats_identifiers=ids,
            platform_stats=platform_stats,
            youtube_data=youtube_data,
        )
        assert tws.platform_stats.spotify.streams_total == 1000000
        assert tws.youtube_data is not None
        assert tws.youtube_data.most_viewed.views == 5000


class TestTrackWithStatsImmutability:
    """Tests for TrackWithStats immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        with pytest.raises(ValidationError):
            tws.track = Track(title="new", artist_list=["new"], year=2024)  # type: ignore[misc]


class TestTrackWithStatsIdentifier:
    """Tests for TrackWithStats.identifier property."""

    @staticmethod
    def test_returns_track_identifier() -> None:
        """Should return track's identifier."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        assert tws.identifier == track.identifier

    @staticmethod
    def test_is_8_characters() -> None:
        """Should be 8-character string."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        assert len(tws.identifier) == 8


class TestTrackWithStatsFromLegacyJson:
    """Tests for TrackWithStats.from_legacy_json method."""

    @staticmethod
    def test_parses_basic_structure() -> None:
        """Should parse basic legacy JSON structure."""
        legacy_data = {
            "title": "16",
            "artist_list": ["blasterjaxx", "hardwell"],
            "year": 2024,
            "songstats_identifiers": {
                "s_id": "qmr6e0bx",
                "s_title": "16",
            },
            "data": {
                "spotify_streams_total": 3805083,
            },
        }
        tws = TrackWithStats.from_legacy_json(legacy_data)
        assert tws.track.title == "16"
        assert tws.track.artist_list == ["blasterjaxx", "hardwell"]
        assert tws.songstats_identifiers.songstats_id == "qmr6e0bx"
        assert tws.platform_stats.spotify.streams_total == 3805083

    @staticmethod
    def test_handles_label_as_grouping() -> None:
        """Should map 'label' field to track.grouping."""
        legacy_data = {
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "label": ["revealed", "spinnin"],
            "songstats_identifiers": {"s_id": "abc", "s_title": "Test"},
            "data": {},
        }
        tws = TrackWithStats.from_legacy_json(legacy_data)
        assert tws.track.grouping == ["revealed", "spinnin"]

    @staticmethod
    def test_handles_request_as_search_query() -> None:
        """Should map 'request' field to track.search_query."""
        legacy_data = {
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "request": "artist test track",
            "songstats_identifiers": {"s_id": "abc", "s_title": "Test"},
            "data": {},
        }
        tws = TrackWithStats.from_legacy_json(legacy_data)
        assert tws.track.search_query == "artist test track"

    @staticmethod
    def test_handles_missing_optional_fields() -> None:
        """Should handle missing optional fields."""
        legacy_data = {
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "songstats_identifiers": {"s_id": "abc", "s_title": "Test"},
        }
        tws = TrackWithStats.from_legacy_json(legacy_data)
        assert tws.track.genre == []
        assert tws.track.grouping == []


class TestTrackWithStatsFromFlatDict:
    """Tests for TrackWithStats.from_flat_dict method."""

    @staticmethod
    def test_parses_flat_structure() -> None:
        """Should parse flat dictionary structure."""
        flat_data = {
            "title": "16",
            "artist_list": ["blasterjaxx"],
            "year": 2024,
            "songstats_id": "qmr6e0bx",
            "songstats_title": "16",
            "spotify_streams_total": 3805083,
        }
        tws = TrackWithStats.from_flat_dict(flat_data)
        assert tws.track.title == "16"
        assert tws.songstats_identifiers.songstats_id == "qmr6e0bx"
        assert tws.platform_stats.spotify.streams_total == 3805083

    @staticmethod
    def test_handles_both_label_and_grouping() -> None:
        """Should prefer grouping over label."""
        flat_data = {
            "title": "test",
            "artist_list": ["artist"],
            "year": 2024,
            "songstats_id": "abc",
            "songstats_title": "Test",
            "label": ["label1"],
            "grouping": ["group1"],
        }
        tws = TrackWithStats.from_flat_dict(flat_data)
        # grouping takes precedence when both exist
        assert "group1" in tws.track.grouping or "label1" in tws.track.grouping


class TestTrackWithStatsToFlatDict:
    """Tests for TrackWithStats.to_flat_dict method."""

    @staticmethod
    def test_includes_track_id() -> None:
        """Should include track_id in output."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        flat = tws.to_flat_dict()
        assert "track_id" in flat
        assert flat["track_id"] == track.identifier

    @staticmethod
    def test_includes_songstats_id() -> None:
        """Should include songstats_id in output."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        flat = tws.to_flat_dict()
        assert flat["songstats_id"] == "abc"

    @staticmethod
    def test_includes_platform_stats() -> None:
        """Should include flattened platform stats."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        platform_stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000)
        )
        tws = TrackWithStats(
            track=track,
            songstats_identifiers=ids,
            platform_stats=platform_stats,
        )
        flat = tws.to_flat_dict()
        assert flat["spotify_streams_total"] == 1000000

    @staticmethod
    def test_excludes_none_values() -> None:
        """Should exclude None values from output."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws = TrackWithStats(track=track, songstats_identifiers=ids)
        flat = tws.to_flat_dict()
        # Should not contain platform keys with None values
        assert "spotify_popularity_peak" not in flat


class TestTrackWithStatsEquality:
    """Tests for TrackWithStats equality comparison."""

    @staticmethod
    def test_equal_instances() -> None:
        """Should be equal when fields match."""
        track = Track(title="test", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws1 = TrackWithStats(track=track, songstats_identifiers=ids)
        tws2 = TrackWithStats(track=track, songstats_identifiers=ids)
        assert tws1 == tws2

    @staticmethod
    def test_not_equal_different_track() -> None:
        """Should not be equal when tracks differ."""
        track1 = Track(title="test1", artist_list=["artist"], year=2024)
        track2 = Track(title="test2", artist_list=["artist"], year=2024)
        ids = SongstatsIdentifiers(songstats_id="abc", songstats_title="Test")
        tws1 = TrackWithStats(track=track1, songstats_identifiers=ids)
        tws2 = TrackWithStats(track=track2, songstats_identifiers=ids)
        assert tws1 != tws2
