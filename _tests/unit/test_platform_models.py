"""Tests for platform statistics models."""

# Standard library
import json

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.platforms import (
    AmazonMusicStats,
    AppleMusicStats,
    BeatportStats,
    DeezerStats,
    SoundCloudStats,
    SpotifyStats,
    TidalStats,
    TikTokStats,
    TracklistsStats,
    YouTubeStats,
)


class TestSpotifyStats:
    """Tests for SpotifyStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid SpotifyStats instance."""
        stats = SpotifyStats(
            streams_total=3805083,
            popularity_peak=62,
            playlist_reach_total=8493255,
            playlists_editorial_total=6,
            charts_total=0
        )
        assert stats.streams_total == 3805083
        assert stats.popularity_peak == 62
        assert stats.playlist_reach_total == 8493255
        assert stats.playlists_editorial_total == 6
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = SpotifyStats()
        assert stats.streams_total is None
        assert stats.popularity_peak is None
        assert stats.playlist_reach_total is None
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_none_vs_zero_distinction() -> None:
        """Test None and zero are different values."""
        stats_none = SpotifyStats(streams_total=None)
        stats_zero = SpotifyStats(streams_total=0)

        assert stats_none.streams_total is None
        assert stats_zero.streams_total == 0
        assert stats_none.streams_total != stats_zero.streams_total

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        # Using alias names (legacy format)
        stats = SpotifyStats(
            spotify_streams_total=1000000,
            spotify_popularity_peak=75
        )
        assert stats.streams_total == 1000000
        assert stats.popularity_peak == 75

    @staticmethod
    def test_popularity_validation_range() -> None:
        """Test popularity must be 0-100."""
        # Valid boundaries
        stats_min = SpotifyStats(popularity_peak=0)
        stats_max = SpotifyStats(popularity_peak=100)
        assert stats_min.popularity_peak == 0
        assert stats_max.popularity_peak == 100

        # Invalid: below 0
        with pytest.raises(ValidationError) as exc_info:
            SpotifyStats(popularity_peak=-1)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("popularity_peak",) for e in errors)

        # Invalid: above 100
        with pytest.raises(ValidationError) as exc_info:
            SpotifyStats(popularity_peak=101)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("popularity_peak",) for e in errors)

    @staticmethod
    def test_negative_values_rejected() -> None:
        """Test negative values are rejected for count fields."""
        with pytest.raises(ValidationError) as exc_info:
            SpotifyStats(streams_total=-1000)
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("streams_total",) for e in errors)

    @staticmethod
    def test_frozen_model() -> None:
        """Test SpotifyStats is immutable."""
        stats = SpotifyStats(streams_total=1000000)
        with pytest.raises(ValidationError):
            stats.streams_total = 2000000

    @staticmethod
    def test_json_serialization() -> None:
        """Test model can be serialized to JSON."""
        stats = SpotifyStats(
            streams_total=1000000,
            popularity_peak=75
        )
        json_str = stats.model_dump_json()
        data = json.loads(json_str)
        assert data["streams_total"] == 1000000
        assert data["popularity_peak"] == 75

    @staticmethod
    def test_json_deserialization_with_aliases() -> None:
        """Test loading from JSON with alias names."""
        json_str = '{"spotify_streams_total": 1000000, "spotify_popularity_peak": 75}'
        stats = SpotifyStats.model_validate_json(json_str)
        assert stats.streams_total == 1000000
        assert stats.popularity_peak == 75

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = SpotifyStats(
            streams_total=1000000,
            popularity_peak=75
        )
        data = stats.model_dump(by_alias=True)
        assert "spotify_streams_total" in data
        assert "spotify_popularity_peak" in data
        assert data["spotify_streams_total"] == 1000000
        assert data["spotify_popularity_peak"] == 75

    @staticmethod
    def test_model_dump_excludes_none() -> None:
        """Test model_dump excludes None values when requested."""
        stats = SpotifyStats(streams_total=1000000)
        data = stats.model_dump(exclude_none=True)
        assert "streams_total" in data
        assert "popularity_peak" not in data


class TestDeezerStats:
    """Tests for DeezerStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid DeezerStats instance."""
        stats = DeezerStats(
            popularity_peak=80,
            playlist_reach_total=650437,
            playlists_editorial_total=5,
            charts_total=0
        )
        assert stats.popularity_peak == 80
        assert stats.playlist_reach_total == 650437
        assert stats.playlists_editorial_total == 5
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = DeezerStats()
        assert stats.popularity_peak is None
        assert stats.playlist_reach_total is None
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = DeezerStats(
            deezer_popularity_peak=80,
            deezer_playlist_reach_total=650437
        )
        assert stats.popularity_peak == 80
        assert stats.playlist_reach_total == 650437

    @staticmethod
    def test_popularity_validation_range() -> None:
        """Test popularity must be 0-100."""
        stats_min = DeezerStats(popularity_peak=0)
        stats_max = DeezerStats(popularity_peak=100)
        assert stats_min.popularity_peak == 0
        assert stats_max.popularity_peak == 100

        with pytest.raises(ValidationError):
            DeezerStats(popularity_peak=101)

    @staticmethod
    def test_frozen_model() -> None:
        """Test DeezerStats is immutable."""
        stats = DeezerStats(popularity_peak=80)
        with pytest.raises(ValidationError):
            stats.popularity_peak = 90

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = DeezerStats(
            popularity_peak=80,
            playlist_reach_total=650437
        )
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "deezer_popularity_peak" in data
        assert "deezer_playlist_reach_total" in data


class TestAppleMusicStats:
    """Tests for AppleMusicStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid AppleMusicStats instance."""
        stats = AppleMusicStats(
            playlists_editorial_total=6,
            charts_total=15
        )
        assert stats.playlists_editorial_total == 6
        assert stats.charts_total == 15

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = AppleMusicStats()
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = AppleMusicStats(
            apple_music_playlists_editorial_total=6,
            apple_music_charts_total=15
        )
        assert stats.playlists_editorial_total == 6
        assert stats.charts_total == 15

    @staticmethod
    def test_negative_values_rejected() -> None:
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            AppleMusicStats(playlists_editorial_total=-1)

    @staticmethod
    def test_frozen_model() -> None:
        """Test AppleMusicStats is immutable."""
        stats = AppleMusicStats(charts_total=15)
        with pytest.raises(ValidationError):
            stats.charts_total = 20

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = AppleMusicStats(
            playlists_editorial_total=6,
            charts_total=15
        )
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "apple_music_playlists_editorial_total" in data
        assert "apple_music_charts_total" in data


class TestYouTubeStats:
    """Tests for YouTubeStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid YouTubeStats instance."""
        stats = YouTubeStats(
            video_views_total=527735,
            short_views_total=2573,
            engagement_rate_total=3.0,
            playlists_editorial_total=1,
            charts_total=0
        )
        assert stats.video_views_total == 527735
        assert stats.short_views_total == 2573
        assert stats.engagement_rate_total == 3.0
        assert stats.playlists_editorial_total == 1
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = YouTubeStats()
        assert stats.video_views_total is None
        assert stats.short_views_total is None
        assert stats.engagement_rate_total is None
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = YouTubeStats(
            youtube_video_views_total=527735,
            youtube_short_views_total=2573,
            youtube_engagement_rate_total=3.0
        )
        assert stats.video_views_total == 527735
        assert stats.short_views_total == 2573
        assert stats.engagement_rate_total == 3.0

    @staticmethod
    def test_engagement_rate_float() -> None:
        """Test engagement_rate accepts float values."""
        stats = YouTubeStats(engagement_rate_total=3.5)
        assert stats.engagement_rate_total == 3.5

    @staticmethod
    def test_negative_values_rejected() -> None:
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            YouTubeStats(video_views_total=-1000)

        with pytest.raises(ValidationError):
            YouTubeStats(engagement_rate_total=-1.0)

    @staticmethod
    def test_frozen_model() -> None:
        """Test YouTubeStats is immutable."""
        stats = YouTubeStats(video_views_total=527735)
        with pytest.raises(ValidationError):
            stats.video_views_total = 1000000

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = YouTubeStats(
            video_views_total=527735,
            short_views_total=2573,
            engagement_rate_total=3.0
        )
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "youtube_video_views_total" in data
        assert "youtube_short_views_total" in data
        assert "youtube_engagement_rate_total" in data

    @staticmethod
    def test_json_serialization_with_float() -> None:
        """Test JSON serialization handles float values correctly."""
        stats = YouTubeStats(
            video_views_total=100000,
            engagement_rate_total=5.7
        )
        json_str = stats.model_dump_json()
        data = json.loads(json_str)
        assert data["video_views_total"] == 100000
        assert data["engagement_rate_total"] == 5.7


class TestTikTokStats:
    """Tests for TikTokStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid TikTokStats instance."""
        stats = TikTokStats(
            views_total=583273,
            engagement_rate_total=5.7,
            charts_total=0
        )
        assert stats.views_total == 583273
        assert stats.engagement_rate_total == 5.7
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = TikTokStats()
        assert stats.views_total is None
        assert stats.engagement_rate_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = TikTokStats(
            tiktok_views_total=583273,
            tiktok_engagement_rate_total=5.7
        )
        assert stats.views_total == 583273
        assert stats.engagement_rate_total == 5.7

    @staticmethod
    def test_frozen_model() -> None:
        """Test TikTokStats is immutable."""
        stats = TikTokStats(views_total=583273)
        with pytest.raises(ValidationError):
            stats.views_total = 1000000

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = TikTokStats(views_total=583273, engagement_rate_total=5.7)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "tiktok_views_total" in data
        assert "tiktok_engagement_rate_total" in data


class TestSoundCloudStats:
    """Tests for SoundCloudStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid SoundCloudStats instance."""
        stats = SoundCloudStats(
            streams_total=88503,
            engagement_rate_total=3.0,
            charts_total=0
        )
        assert stats.streams_total == 88503
        assert stats.engagement_rate_total == 3.0
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = SoundCloudStats()
        assert stats.streams_total is None
        assert stats.engagement_rate_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = SoundCloudStats(
            soundcloud_streams_total=88503,
            soundcloud_engagement_rate_total=3.0
        )
        assert stats.streams_total == 88503
        assert stats.engagement_rate_total == 3.0

    @staticmethod
    def test_frozen_model() -> None:
        """Test SoundCloudStats is immutable."""
        stats = SoundCloudStats(streams_total=88503)
        with pytest.raises(ValidationError):
            stats.streams_total = 100000

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = SoundCloudStats(streams_total=88503)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "soundcloud_streams_total" in data


class TestTidalStats:
    """Tests for TidalStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid TidalStats instance."""
        stats = TidalStats(
            popularity_peak=32,
            playlists_editorial_total=0,
            charts_total=0
        )
        assert stats.popularity_peak == 32
        assert stats.playlists_editorial_total == 0
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = TidalStats()
        assert stats.popularity_peak is None
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = TidalStats(
            tidal_popularity_peak=32,
            tidal_playlists_editorial_total=0
        )
        assert stats.popularity_peak == 32
        assert stats.playlists_editorial_total == 0

    @staticmethod
    def test_popularity_validation_range() -> None:
        """Test popularity must be 0-100."""
        stats_min = TidalStats(popularity_peak=0)
        stats_max = TidalStats(popularity_peak=100)
        assert stats_min.popularity_peak == 0
        assert stats_max.popularity_peak == 100

        with pytest.raises(ValidationError):
            TidalStats(popularity_peak=101)

    @staticmethod
    def test_frozen_model() -> None:
        """Test TidalStats is immutable."""
        stats = TidalStats(popularity_peak=32)
        with pytest.raises(ValidationError):
            stats.popularity_peak = 50

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = TidalStats(popularity_peak=32)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "tidal_popularity_peak" in data


class TestAmazonMusicStats:
    """Tests for AmazonMusicStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid AmazonMusicStats instance."""
        stats = AmazonMusicStats(
            playlists_editorial_total=26,
            charts_total=0
        )
        assert stats.playlists_editorial_total == 26
        assert stats.charts_total == 0

    @staticmethod
    def test_all_fields_optional() -> None:
        """Test all fields default to None."""
        stats = AmazonMusicStats()
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None

    @staticmethod
    def test_field_aliases() -> None:
        """Test fields can be set via aliases."""
        stats = AmazonMusicStats(
            amazon_playlists_editorial_total=26,
            amazon_charts_total=0
        )
        assert stats.playlists_editorial_total == 26
        assert stats.charts_total == 0

    @staticmethod
    def test_frozen_model() -> None:
        """Test AmazonMusicStats is immutable."""
        stats = AmazonMusicStats(playlists_editorial_total=26)
        with pytest.raises(ValidationError):
            stats.playlists_editorial_total = 30

    @staticmethod
    def test_model_dump_with_aliases() -> None:
        """Test model_dump uses aliases when by_alias=True."""
        stats = AmazonMusicStats(playlists_editorial_total=26)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "amazon_playlists_editorial_total" in data


class TestBeatportStats:
    """Tests for BeatportStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid BeatportStats instance."""
        stats = BeatportStats(dj_charts_total=35)
        assert stats.dj_charts_total == 35

    @staticmethod
    def test_field_optional() -> None:
        """Test field defaults to None."""
        stats = BeatportStats()
        assert stats.dj_charts_total is None

    @staticmethod
    def test_field_alias() -> None:
        """Test field can be set via alias."""
        stats = BeatportStats(beatport_dj_charts_total=35)
        assert stats.dj_charts_total == 35

    @staticmethod
    def test_negative_value_rejected() -> None:
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            BeatportStats(dj_charts_total=-1)

    @staticmethod
    def test_frozen_model() -> None:
        """Test BeatportStats is immutable."""
        stats = BeatportStats(dj_charts_total=35)
        with pytest.raises(ValidationError):
            stats.dj_charts_total = 40

    @staticmethod
    def test_model_dump_with_alias() -> None:
        """Test model_dump uses alias when by_alias=True."""
        stats = BeatportStats(dj_charts_total=35)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "beatport_dj_charts_total" in data
        assert data["beatport_dj_charts_total"] == 35


class TestTracklistsStats:
    """Tests for TracklistsStats model."""

    @staticmethod
    def test_create_valid_stats() -> None:
        """Test creating valid TracklistsStats instance."""
        stats = TracklistsStats(unique_support=40)
        assert stats.unique_support == 40

    @staticmethod
    def test_field_optional() -> None:
        """Test field defaults to None."""
        stats = TracklistsStats()
        assert stats.unique_support is None

    @staticmethod
    def test_field_alias() -> None:
        """Test field can be set via alias."""
        stats = TracklistsStats(**{"1001tracklists_unique_support": 40})
        assert stats.unique_support == 40

    @staticmethod
    def test_negative_value_rejected() -> None:
        """Test negative values are rejected."""
        with pytest.raises(ValidationError):
            TracklistsStats(unique_support=-1)

    @staticmethod
    def test_frozen_model() -> None:
        """Test TracklistsStats is immutable."""
        stats = TracklistsStats(unique_support=40)
        with pytest.raises(ValidationError):
            stats.unique_support = 50

    @staticmethod
    def test_model_dump_with_alias() -> None:
        """Test model_dump uses alias when by_alias=True."""
        stats = TracklistsStats(unique_support=40)
        data = stats.model_dump(by_alias=True, exclude_none=True)
        assert "1001tracklists_unique_support" in data
        assert data["1001tracklists_unique_support"] == 40
