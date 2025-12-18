"""Integration tests for YouTubeClient with real API."""

# Standard library
import os

# Third-party
import pytest

# Local
from msc.clients.youtube import YouTubeClient

pytestmark = pytest.mark.skipif(
    not (os.path.exists("_tokens/oauth.json") and os.path.exists("_tokens/credentials.json")),
    reason="YouTube credentials not configured",
)


class TestYouTubeIntegration:
    """Integration tests for YouTubeClient with real YouTube API."""

    @staticmethod
    def test_health_check_with_real_api() -> None:
        """Should successfully ping YouTube API."""
        with YouTubeClient() as client:
            assert client.health_check() is True

    @staticmethod
    def test_get_video_details_real_video() -> None:
        """Should fetch details for real YouTube video (Rick Roll)."""
        with YouTubeClient() as client:
            video = client.get_video_details("dQw4w9WgXcQ")

            assert video["video_id"] == "dQw4w9WgXcQ"
            assert "Never Gonna Give You Up" in video["title"]
            assert "Rick Astley" in video["channel_name"]
            assert video["view_count"] > 0
            assert video["like_count"] > 0

    @staticmethod
    def test_get_videos_details_batch() -> None:
        """Should fetch multiple videos in batch."""
        with YouTubeClient() as client:
            video_ids = [
                "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
                "9bZkp7q19f0",  # PSY - GANGNAM STYLE
                "kJQP7kiw5Fk",  # Luis Fonsi - Despacito
            ]
            videos = client.get_videos_details(video_ids)

            assert len(videos) == 3
            assert all("video_id" in video for video in videos)
            assert all("title" in video for video in videos)
            assert all(video["view_count"] > 0 for video in videos)

    @staticmethod
    def test_get_playlist_videos_real_playlist() -> None:
        """Should fetch videos from a real public playlist."""
        with YouTubeClient() as client:
            # Using a small public playlist (YouTube Spotlight - Popular Music Videos)
            # Note: Replace with a known small playlist ID if needed
            playlist_id = "PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf"
            videos = client.get_playlist_videos(playlist_id)

            # Playlist might be empty or have videos
            assert isinstance(videos, list)
            if videos:
                assert "video_id" in videos[0]
                assert "title" in videos[0]

    @staticmethod
    def test_context_manager() -> None:
        """Should work with context manager."""
        with YouTubeClient() as client:
            quota = client.get_quota()
            assert "daily_limit" in quota

        # Client should be closed after context
        assert client._youtube_client is None

    @staticmethod
    def test_invalid_video_id() -> None:
        """Should return empty dict for invalid video ID."""
        with YouTubeClient() as client:
            video = client.get_video_details("invalid_id_12345")
            assert video == {}

    @staticmethod
    def test_invalid_playlist_id() -> None:
        """Should return empty list for invalid playlist ID."""
        with YouTubeClient() as client:
            videos = client.get_playlist_videos("invalid_playlist_12345")
            # Note: Depending on API behavior, might return empty list or raise exception
            # YouTubeClient should handle gracefully and return empty list
            assert videos == []
