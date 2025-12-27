"""Unit tests for YouTube video metadata models.

Tests YouTubeVideo and YouTubeVideoData models.
"""

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.track import SongstatsIdentifiers
from msc.models.youtube import YouTubeVideo, YouTubeVideoData


class TestYouTubeVideoCreation:
    """Tests for YouTubeVideo model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with required fields."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell",
        )
        assert video.video_id == "s0UcVIcQ8B4"
        assert video.views == 271568
        assert video.channel_name == "Hardwell"

    @staticmethod
    def test_accepts_ytb_id_alias() -> None:
        """Should accept ytb_id as alias for video_id."""
        video = YouTubeVideo(
            ytb_id="s0UcVIcQ8B4",  # type: ignore[call-arg]
            views=271568,
            channel_name="Hardwell",
        )
        assert video.video_id == "s0UcVIcQ8B4"

    @staticmethod
    def test_accepts_zero_views() -> None:
        """Should accept zero views."""
        video = YouTubeVideo(
            video_id="abc123",
            views=0,
            channel_name="Channel",
        )
        assert video.views == 0


class TestYouTubeVideoValidation:
    """Tests for YouTubeVideo field validation."""

    @staticmethod
    def test_rejects_negative_views() -> None:
        """Should reject negative view count."""
        with pytest.raises(ValidationError):
            YouTubeVideo(
                video_id="abc123",
                views=-1,
                channel_name="Channel",
            )

    @staticmethod
    def test_requires_video_id() -> None:
        """Should require video_id."""
        with pytest.raises(ValidationError):
            YouTubeVideo(views=1000, channel_name="Channel")  # type: ignore[call-arg]

    @staticmethod
    def test_requires_channel_name() -> None:
        """Should require channel_name."""
        with pytest.raises(ValidationError):
            YouTubeVideo(video_id="abc123", views=1000)  # type: ignore[call-arg]


class TestYouTubeVideoImmutability:
    """Tests for YouTubeVideo immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        with pytest.raises(ValidationError):
            video.views = 2000  # type: ignore[misc]


class TestYouTubeVideoIsTopicChannel:
    """Tests for YouTubeVideo.is_topic_channel property."""

    @staticmethod
    def test_returns_true_for_topic_channel() -> None:
        """Should return True for topic channels."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Hardwell - Topic",
        )
        assert video.is_topic_channel is True

    @staticmethod
    def test_returns_false_for_regular_channel() -> None:
        """Should return False for regular channels."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Hardwell",
        )
        assert video.is_topic_channel is False

    @staticmethod
    def test_case_sensitive() -> None:
        """Should be case-sensitive for topic detection."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Hardwell - topic",  # lowercase
        )
        assert video.is_topic_channel is False


class TestYouTubeVideoEquality:
    """Tests for YouTubeVideo equality comparison."""

    @staticmethod
    def test_equal_instances() -> None:
        """Should be equal when all fields match."""
        video1 = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        video2 = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        assert video1 == video2

    @staticmethod
    def test_not_equal_different_views() -> None:
        """Should not be equal when views differ."""
        video1 = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        video2 = YouTubeVideo(
            video_id="abc123",
            views=2000,
            channel_name="Channel",
        )
        assert video1 != video2


class TestYouTubeVideoDataCreation:
    """Tests for YouTubeVideoData model creation."""

    @staticmethod
    def test_creates_with_required_fields() -> None:
        """Should create with required fields."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell",
        )
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16",
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["s0UcVIcQ8B4"],
            songstats_identifiers=ids,
        )
        assert video_data.most_viewed.video_id == "s0UcVIcQ8B4"
        assert video_data.all_sources == ["s0UcVIcQ8B4"]
        assert video_data.songstats_identifiers.songstats_id == "qmr6e0bx"

    @staticmethod
    def test_creates_with_multiple_sources() -> None:
        """Should create with multiple video sources."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell",
        )
        ids = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16",
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["s0UcVIcQ8B4", "ekZ06PHmxAw", "xyz789"],
            songstats_identifiers=ids,
        )
        assert len(video_data.all_sources) == 3


class TestYouTubeVideoDataValidation:
    """Tests for YouTubeVideoData field validation."""

    @staticmethod
    def test_requires_at_least_one_source() -> None:
        """Should require at least one source in all_sources."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        with pytest.raises(ValidationError, match="all_sources"):
            YouTubeVideoData(
                most_viewed=video,
                all_sources=[],  # Empty list should fail
                songstats_identifiers=ids,
            )

    @staticmethod
    def test_requires_most_viewed() -> None:
        """Should require most_viewed video."""
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        with pytest.raises(ValidationError):
            YouTubeVideoData(
                all_sources=["abc123"],  # type: ignore[call-arg]
                songstats_identifiers=ids,
            )


class TestYouTubeVideoDataImmutability:
    """Tests for YouTubeVideoData immutability."""

    @staticmethod
    def test_is_frozen() -> None:
        """Should not allow field modification."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=ids,
        )
        new_video = YouTubeVideo(
            video_id="xyz789",
            views=2000,
            channel_name="Other",
        )
        with pytest.raises(ValidationError):
            video_data.most_viewed = new_video  # type: ignore[misc]


class TestYouTubeVideoDataVideoCount:
    """Tests for YouTubeVideoData.video_count property."""

    @staticmethod
    def test_returns_single_count() -> None:
        """Should return 1 for single video."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=ids,
        )
        assert video_data.video_count == 1

    @staticmethod
    def test_returns_multiple_count() -> None:
        """Should return correct count for multiple videos."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123", "def456", "ghi789", "jkl012"],
            songstats_identifiers=ids,
        )
        assert video_data.video_count == 4


class TestYouTubeVideoDataEquality:
    """Tests for YouTubeVideoData equality comparison."""

    @staticmethod
    def test_equal_instances() -> None:
        """Should be equal when all fields match."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        video_data1 = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=ids,
        )
        video_data2 = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=ids,
        )
        assert video_data1 == video_data2

    @staticmethod
    def test_not_equal_different_sources() -> None:
        """Should not be equal when sources differ."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Channel",
        )
        ids = SongstatsIdentifiers(
            songstats_id="abc",
            songstats_title="Test",
        )
        video_data1 = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=ids,
        )
        video_data2 = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123", "def456"],
            songstats_identifiers=ids,
        )
        assert video_data1 != video_data2
