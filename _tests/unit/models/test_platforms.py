"""Unit tests for platform statistics models.

Tests for all 10 platform stats models: Spotify, AppleMusic, YouTube, Deezer,
TikTok, Beatport, Tidal, SoundCloud, Amazon, and Tracklists.
"""

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
    def test_creates_with_all_fields() -> None:
        """Should create with all fields."""
        stats = SpotifyStats(
            streams_total=1000000,
            popularity_peak=75,
            playlist_reach_total=500000,
            playlists_editorial_total=50,
            charts_total=10,
        )
        assert stats.streams_total == 1000000
        assert stats.popularity_peak == 75

    @staticmethod
    def test_defaults_all_to_none() -> None:
        """Should default all fields to None."""
        stats = SpotifyStats()
        assert stats.streams_total is None
        assert stats.popularity_peak is None
        assert stats.playlist_reach_total is None

    @staticmethod
    def test_is_frozen() -> None:
        """Should be immutable."""
        stats = SpotifyStats(streams_total=100)
        with pytest.raises(ValidationError):
            stats.streams_total = 200  # type: ignore[misc]

    @staticmethod
    def test_validates_popularity_max() -> None:
        """Should reject popularity above 100."""
        with pytest.raises(ValidationError):
            SpotifyStats(popularity_peak=101)

    @staticmethod
    def test_validates_non_negative() -> None:
        """Should reject negative values."""
        with pytest.raises(ValidationError):
            SpotifyStats(streams_total=-1)

    @staticmethod
    def test_accepts_alias() -> None:
        """Should accept aliased field names."""
        stats = SpotifyStats(spotify_streams_total=100)  # type: ignore[call-arg]
        assert stats.streams_total == 100


class TestAppleMusicStats:
    """Tests for AppleMusicStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = AppleMusicStats(
            playlists_editorial_total=20,
            charts_total=10,
        )
        assert stats.playlists_editorial_total == 20
        assert stats.charts_total == 10

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = AppleMusicStats()
        assert stats.playlists_editorial_total is None
        assert stats.charts_total is None


class TestYouTubeStats:
    """Tests for YouTubeStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = YouTubeStats(
            video_views_total=2000000,
            short_views_total=50000,
            engagement_rate_total=3.5,
            playlists_editorial_total=5,
            charts_total=10,
        )
        assert stats.video_views_total == 2000000
        assert stats.short_views_total == 50000
        assert stats.engagement_rate_total == 3.5

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = YouTubeStats()
        assert stats.video_views_total is None
        assert stats.short_views_total is None


class TestDeezerStats:
    """Tests for DeezerStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = DeezerStats(
            popularity_peak=80,
            playlist_reach_total=50000,
        )
        assert stats.popularity_peak == 80

    @staticmethod
    def test_validates_popularity() -> None:
        """Should validate popularity range."""
        with pytest.raises(ValidationError):
            DeezerStats(popularity_peak=101)


class TestTikTokStats:
    """Tests for TikTokStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = TikTokStats(
            views_total=5000000,
            engagement_rate_total=5.7,
            charts_total=3,
        )
        assert stats.views_total == 5000000
        assert stats.engagement_rate_total == 5.7

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = TikTokStats()
        assert stats.views_total is None
        assert stats.engagement_rate_total is None


class TestBeatportStats:
    """Tests for BeatportStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = BeatportStats(dj_charts_total=35)
        assert stats.dj_charts_total == 35

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = BeatportStats()
        assert stats.dj_charts_total is None


class TestTidalStats:
    """Tests for TidalStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = TidalStats(
            popularity_peak=32,
            playlists_editorial_total=5,
            charts_total=2,
        )
        assert stats.popularity_peak == 32
        assert stats.playlists_editorial_total == 5

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = TidalStats()
        assert stats.popularity_peak is None
        assert stats.playlists_editorial_total is None


class TestSoundCloudStats:
    """Tests for SoundCloudStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = SoundCloudStats(
            streams_total=500000,
            engagement_rate_total=3.0,
        )
        assert stats.streams_total == 500000

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = SoundCloudStats()
        assert stats.streams_total is None


class TestAmazonMusicStats:
    """Tests for AmazonMusicStats model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = AmazonMusicStats(
            playlists_editorial_total=26,
            charts_total=3,
        )
        assert stats.playlists_editorial_total == 26

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = AmazonMusicStats()
        assert stats.playlists_editorial_total is None


class TestTracklistsStats:
    """Tests for TracklistsStats (1001Tracklists) model."""

    @staticmethod
    def test_creates_with_fields() -> None:
        """Should create with fields."""
        stats = TracklistsStats(unique_support=50)
        assert stats.unique_support == 50

    @staticmethod
    def test_defaults_to_none() -> None:
        """Should default fields to None."""
        stats = TracklistsStats()
        assert stats.unique_support is None


class TestAllPlatformsFrozen:
    """Test that all platform models are immutable."""

    @staticmethod
    @pytest.mark.parametrize(
        "model_class",
        [
            SpotifyStats,
            AppleMusicStats,
            YouTubeStats,
            DeezerStats,
            TikTokStats,
            BeatportStats,
            TidalStats,
            SoundCloudStats,
            AmazonMusicStats,
            TracklistsStats,
        ],
    )
    def test_model_is_frozen(model_class: type) -> None:
        """Should be frozen (immutable)."""
        instance = model_class()
        # All models should have frozen=True in config
        assert instance.model_config.get("frozen") is True
