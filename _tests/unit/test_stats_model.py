"""Tests for platform stats container and combined track models."""

# Standard library
import json

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.platforms import DeezerStats, SpotifyStats
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track


class TestPlatformStats:
    """Tests for PlatformStats container model."""

    @staticmethod
    def test_create_empty_stats() -> None:
        """Test creating empty PlatformStats (all platforms None)."""
        stats = PlatformStats()
        assert stats.spotify.streams_total is None
        assert stats.deezer.popularity_peak is None
        assert stats.apple_music.playlists_editorial_total is None
        assert stats.youtube.video_views_total is None
        assert stats.tiktok.views_total is None
        assert stats.soundcloud.streams_total is None
        assert stats.tidal.popularity_peak is None
        assert stats.amazon_music.playlists_editorial_total is None
        assert stats.beatport.dj_charts_total is None
        assert stats.tracklists.unique_support is None

    @staticmethod
    def test_create_with_specific_platforms() -> None:
        """Test creating PlatformStats with specific platform data."""
        stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000),
            deezer=DeezerStats(popularity_peak=80)
        )
        assert stats.spotify.streams_total == 1000000
        assert stats.deezer.popularity_peak == 80
        # Other platforms should have default empty stats
        assert stats.apple_music.playlists_editorial_total is None

    @staticmethod
    def test_group_by_platform_empty() -> None:
        """Test _group_by_platform with empty data."""
        result = PlatformStats._group_by_platform({}, "spotify_")
        assert result == {}

    @staticmethod
    def test_group_by_platform_with_matching_keys() -> None:
        """Test _group_by_platform extracts matching keys."""
        data = {
            "spotify_streams_total": 1000000,
            "spotify_popularity_peak": 75,
            "deezer_popularity_peak": 80,
            "other_field": "value"
        }
        result = PlatformStats._group_by_platform(data, "spotify_")
        assert result == {
            "spotify_streams_total": 1000000,
            "spotify_popularity_peak": 75
        }

    @staticmethod
    def test_group_by_platform_no_matches() -> None:
        """Test _group_by_platform with no matching keys."""
        data = {
            "deezer_popularity_peak": 80,
            "youtube_video_views_total": 500000
        }
        result = PlatformStats._group_by_platform(data, "spotify_")
        assert result == {}

    @staticmethod
    def test_from_flat_dict_empty() -> None:
        """Test from_flat_dict with empty dictionary."""
        stats = PlatformStats.from_flat_dict({})
        assert stats.spotify.streams_total is None
        assert stats.deezer.popularity_peak is None

    @staticmethod
    def test_from_flat_dict_with_data() -> None:
        """Test from_flat_dict with platform-prefixed keys."""
        flat_data = {
            "spotify_streams_total": 3805083,
            "spotify_popularity_peak": 62,
            "deezer_popularity_peak": 80,
            "deezer_playlist_reach_total": 650437,
            "youtube_video_views_total": 527735,
        }
        stats = PlatformStats.from_flat_dict(flat_data)
        assert stats.spotify.streams_total == 3805083
        assert stats.spotify.popularity_peak == 62
        assert stats.deezer.popularity_peak == 80
        assert stats.deezer.playlist_reach_total == 650437
        assert stats.youtube.video_views_total == 527735

    @staticmethod
    def test_to_flat_dict_empty() -> None:
        """Test to_flat_dict with empty stats."""
        stats = PlatformStats()
        flat = stats.to_flat_dict()
        # Should be empty since all values are None and exclude_none=True
        assert flat == {}

    @staticmethod
    def test_to_flat_dict_with_data() -> None:
        """Test to_flat_dict with populated stats."""
        stats = PlatformStats(
            spotify=SpotifyStats(
                streams_total=3805083,
                popularity_peak=62
            ),
            deezer=DeezerStats(
                popularity_peak=80,
                playlist_reach_total=650437
            )
        )
        flat = stats.to_flat_dict()
        assert flat["spotify_streams_total"] == 3805083
        assert flat["spotify_popularity_peak"] == 62
        assert flat["deezer_popularity_peak"] == 80
        assert flat["deezer_playlist_reach_total"] == 650437

    @staticmethod
    def test_roundtrip_conversion() -> None:
        """Test flat → nested → flat roundtrip is lossless."""
        original_flat = {
            "spotify_streams_total": 3805083,
            "spotify_popularity_peak": 62,
            "spotify_playlist_reach_total": 8493255,
            "deezer_popularity_peak": 80,
            "deezer_playlist_reach_total": 650437,
            "apple_music_playlists_editorial_total": 6,
            "youtube_video_views_total": 527735,
            "youtube_engagement_rate_total": 3.0,
            "tiktok_views_total": 583273,
            "soundcloud_streams_total": 88503,
            "tidal_popularity_peak": 32,
            "amazon_playlists_editorial_total": 26,
            "beatport_dj_charts_total": 35,
            "1001tracklists_unique_support": 40,
        }

        # Convert to nested model
        stats = PlatformStats.from_flat_dict(original_flat)

        # Convert back to flat
        result_flat = stats.to_flat_dict()

        # Should be identical
        assert result_flat == original_flat

    @staticmethod
    def test_frozen_model() -> None:
        """Test PlatformStats is immutable."""
        stats = PlatformStats()
        with pytest.raises(ValidationError):
            stats.spotify = SpotifyStats(streams_total=1000000)

    @staticmethod
    def test_json_serialization() -> None:
        """Test PlatformStats can be serialized to JSON."""
        stats = PlatformStats(
            spotify=SpotifyStats(streams_total=1000000)
        )
        json_str = stats.model_dump_json()
        data = json.loads(json_str)
        assert data["spotify"]["streams_total"] == 1000000

    @staticmethod
    def test_all_platforms_present() -> None:
        """Test all 10 platforms are accessible."""
        stats = PlatformStats()
        # Verify all platform attributes exist
        assert hasattr(stats, "spotify")
        assert hasattr(stats, "deezer")
        assert hasattr(stats, "apple_music")
        assert hasattr(stats, "youtube")
        assert hasattr(stats, "tiktok")
        assert hasattr(stats, "soundcloud")
        assert hasattr(stats, "tidal")
        assert hasattr(stats, "amazon_music")
        assert hasattr(stats, "beatport")
        assert hasattr(stats, "tracklists")


class TestTrackWithStats:
    """Tests for TrackWithStats combined model."""

    @staticmethod
    def test_create_minimal_instance() -> None:
        """Test creating minimal TrackWithStats."""
        track = Track(
            title="Test",
            artist_list=["artist"],
            year=2024
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )

        track_with_stats = TrackWithStats(
            track=track,
            songstats_identifiers=identifiers
        )

        assert track_with_stats.track.title == "Test"
        assert track_with_stats.songstats_identifiers.songstats_id == "abc123"
        # platform_stats should default to empty
        assert track_with_stats.platform_stats.spotify.streams_total is None

    @staticmethod
    def test_create_full_instance() -> None:
        """Test creating TrackWithStats with all fields."""
        track = Track(
            title="16",
            artist_list=["blasterjaxx", "hardwell", "maddix"],
            year=2024,
            genre=["hard techno"],
            label=["revealed"]
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        platform_stats = PlatformStats(
            spotify=SpotifyStats(streams_total=3805083, popularity_peak=62),
            deezer=DeezerStats(popularity_peak=80)
        )

        track_with_stats = TrackWithStats(
            track=track,
            songstats_identifiers=identifiers,
            platform_stats=platform_stats
        )

        assert track_with_stats.track.title == "16"
        assert track_with_stats.track.artist_list == ["blasterjaxx", "hardwell", "maddix"]
        assert track_with_stats.songstats_identifiers.songstats_id == "qmr6e0bx"
        assert track_with_stats.platform_stats.spotify.streams_total == 3805083
        assert track_with_stats.platform_stats.deezer.popularity_peak == 80

    @staticmethod
    def test_from_legacy_json_minimal() -> None:
        """Test from_legacy_json with minimal data."""
        legacy_data = {
            "title": "Test",
            "artist_list": ["artist"],
            "year": 2024,
            "songstats_identifiers": {
                "s_id": "abc123",
                "s_title": "Test"
            }
        }

        track = TrackWithStats.from_legacy_json(legacy_data)
        assert track.track.title == "Test"
        assert track.songstats_identifiers.songstats_id == "abc123"

    @staticmethod
    def test_from_legacy_json_full() -> None:
        """Test from_legacy_json with complete data."""
        legacy_data = {
            "title": "16",
            "artist_list": ["blasterjaxx", "hardwell", "maddix"],
            "year": 2024,
            "genre": ["hard techno"],
            "label": ["revealed"],
            "request": "blasterjaxx, hardwell, maddix 16",
            "songstats_identifiers": {
                "s_id": "qmr6e0bx",
                "s_title": "16"
            },
            "data": {
                "spotify_streams_total": 3805083,
                "spotify_popularity_peak": 62,
                "deezer_popularity_peak": 80,
                "deezer_playlist_reach_total": 650437
            }
        }

        track = TrackWithStats.from_legacy_json(legacy_data)

        # Verify track metadata
        assert track.track.title == "16"
        assert track.track.artist_list == ["blasterjaxx", "hardwell", "maddix"]
        assert track.track.year == 2024
        assert track.track.genre == ["hard techno"]
        assert track.track.label == ["revealed"]
        assert track.track.search_query == "blasterjaxx, hardwell, maddix 16"

        # Verify identifiers
        assert track.songstats_identifiers.songstats_id == "qmr6e0bx"
        assert track.songstats_identifiers.songstats_title == "16"

        # Verify platform stats
        assert track.platform_stats.spotify.streams_total == 3805083
        assert track.platform_stats.spotify.popularity_peak == 62
        assert track.platform_stats.deezer.popularity_peak == 80
        assert track.platform_stats.deezer.playlist_reach_total == 650437

    @staticmethod
    def test_frozen_model() -> None:
        """Test TrackWithStats is immutable."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        identifiers = SongstatsIdentifiers(songstats_id="abc123", songstats_title="Test")
        track_with_stats = TrackWithStats(
            track=track,
            songstats_identifiers=identifiers
        )

        with pytest.raises(ValidationError):
            track_with_stats.track = Track(title="New", artist_list=["new"], year=2025)

    @staticmethod
    def test_nested_field_access() -> None:
        """Test accessing deeply nested fields."""
        legacy_data = {
            "title": "16",
            "artist_list": ["blasterjaxx", "hardwell", "maddix"],
            "year": 2024,
            "songstats_identifiers": {
                "s_id": "qmr6e0bx",
                "s_title": "16"
            },
            "data": {
                "spotify_streams_total": 3805083
            }
        }

        track = TrackWithStats.from_legacy_json(legacy_data)

        # Deep access should work
        assert track.track.primary_artist == "blasterjaxx"
        assert track.track.all_artists_string == "blasterjaxx, hardwell, maddix"
        assert track.platform_stats.spotify.streams_total == 3805083

    @staticmethod
    def test_json_serialization() -> None:
        """Test TrackWithStats can be serialized to JSON."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        identifiers = SongstatsIdentifiers(songstats_id="abc123", songstats_title="Test")
        track_with_stats = TrackWithStats(
            track=track,
            songstats_identifiers=identifiers
        )

        json_str = track_with_stats.model_dump_json()
        data = json.loads(json_str)

        assert data["track"]["title"] == "Test"
        assert data["songstats_identifiers"]["songstats_id"] == "abc123"

    @staticmethod
    def test_model_dump_excludes_none() -> None:
        """Test model_dump excludes None values."""
        track = Track(title="Test", artist_list=["artist"], year=2024)
        identifiers = SongstatsIdentifiers(songstats_id="abc123", songstats_title="Test")
        track_with_stats = TrackWithStats(
            track=track,
            songstats_identifiers=identifiers
        )

        data = track_with_stats.model_dump(exclude_none=True)

        # Track should not have grouping or search_query (both None)
        assert "grouping" not in data["track"]
        assert "search_query" not in data["track"]

        # Platform stats should not have nested empty dicts
        # (depends on implementation details of model_dump)
