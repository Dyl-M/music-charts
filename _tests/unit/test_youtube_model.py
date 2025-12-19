"""Tests for YouTube video metadata models."""

# Standard library
import json

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.track import SongstatsIdentifiers
from msc.models.youtube import YouTubeVideo, YouTubeVideoData


class TestYouTubeVideo:
    """Tests for YouTubeVideo model."""

    @staticmethod
    def test_create_valid_video() -> None:
        """Test creating valid YouTubeVideo instance."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        assert video.video_id == "s0UcVIcQ8B4"
        assert video.views == 271568
        assert video.channel_name == "Hardwell"

    @staticmethod
    def test_alias_ytb_id() -> None:
        """Test video_id can be set via ytb_id alias."""
        video = YouTubeVideo(
            ytb_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        assert video.video_id == "s0UcVIcQ8B4"

    @staticmethod
    def test_negative_views_rejected() -> None:
        """Test negative views are rejected."""
        with pytest.raises(ValidationError):
            YouTubeVideo(
                video_id="abc123",
                views=-1000,
                channel_name="Test"
            )

    @staticmethod
    def test_frozen_model() -> None:
        """Test YouTubeVideo is immutable."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Test"
        )
        with pytest.raises(ValidationError):
            video.views = 2000

    @staticmethod
    def test_is_topic_channel_true() -> None:
        """Test is_topic_channel property returns True for topic channels."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Hardwell - Topic"
        )
        assert video.is_topic_channel is True

    @staticmethod
    def test_is_topic_channel_false() -> None:
        """Test is_topic_channel property returns False for regular channels."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Hardwell"
        )
        assert video.is_topic_channel is False

    @staticmethod
    def test_json_serialization() -> None:
        """Test YouTubeVideo can be serialized to JSON."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        json_str = video.model_dump_json()
        data = json.loads(json_str)
        assert data["video_id"] == "s0UcVIcQ8B4"
        assert data["views"] == 271568
        assert data["channel_name"] == "Hardwell"

    @staticmethod
    def test_model_dump_with_alias() -> None:
        """Test model_dump uses alias when by_alias=True."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        data = video.model_dump(by_alias=True)
        assert "ytb_id" in data
        assert data["ytb_id"] == "s0UcVIcQ8B4"


class TestYouTubeVideoData:
    """Tests for YouTubeVideoData model."""

    @staticmethod
    def test_create_valid_video_data() -> None:
        """Test creating valid YouTubeVideoData instance."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["s0UcVIcQ8B4", "ekZ06PHmxAw"],
            songstats_identifiers=identifiers
        )

        assert video_data.most_viewed.video_id == "s0UcVIcQ8B4"
        assert len(video_data.all_sources) == 2
        assert video_data.songstats_identifiers.songstats_id == "qmr6e0bx"

    @staticmethod
    def test_all_sources_min_length() -> None:
        """Test all_sources must have at least one video ID."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Test"
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )

        with pytest.raises(ValidationError):
            YouTubeVideoData(
                most_viewed=video,
                all_sources=[],
                songstats_identifiers=identifiers
            )

    @staticmethod
    def test_video_count_property() -> None:
        """Test video_count property returns correct count."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["s0UcVIcQ8B4", "ekZ06PHmxAw", "cf7E_u0jATs"],
            songstats_identifiers=identifiers
        )

        assert video_data.video_count == 3

    @staticmethod
    def test_frozen_model() -> None:
        """Test YouTubeVideoData is immutable."""
        video = YouTubeVideo(
            video_id="abc123",
            views=1000,
            channel_name="Test"
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test"
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["abc123"],
            songstats_identifiers=identifiers
        )

        with pytest.raises(ValidationError):
            video_data.all_sources = ["new_id"]

    @staticmethod
    def test_json_serialization() -> None:
        """Test YouTubeVideoData can be serialized to JSON."""
        video = YouTubeVideo(
            video_id="s0UcVIcQ8B4",
            views=271568,
            channel_name="Hardwell"
        )
        identifiers = SongstatsIdentifiers(
            songstats_id="qmr6e0bx",
            songstats_title="16"
        )
        video_data = YouTubeVideoData(
            most_viewed=video,
            all_sources=["s0UcVIcQ8B4", "ekZ06PHmxAw"],
            songstats_identifiers=identifiers
        )

        json_str = video_data.model_dump_json()
        data = json.loads(json_str)

        assert data["most_viewed"]["video_id"] == "s0UcVIcQ8B4"
        assert len(data["all_sources"]) == 2
        assert data["songstats_identifiers"]["songstats_id"] == "qmr6e0bx"
