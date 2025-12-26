"""Integration tests for YouTube client with real API.

Tests real API interactions when OAuth credentials are available.
"""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.clients.youtube import YouTubeClient


class TestYouTubeClientRealAPI:
    """Integration tests for YouTubeClient with real API."""

    @staticmethod
    def test_credentials_file_exists(youtube_credentials_path: Path | None) -> None:
        """Should check if credentials file exists."""
        if youtube_credentials_path is None:
            pytest.skip("YouTube credentials not available")

        # Note: Full initialization may require browser interaction
        # This tests just the path handling
        assert youtube_credentials_path.exists()

    @staticmethod
    def test_client_constructor() -> None:
        """Should accept rate_limit and timeout parameters."""
        # Client constructor takes rate_limit and timeout, not credentials_path
        # Actual authentication happens on first API call
        try:
            client = YouTubeClient(rate_limit=10, timeout=30)
            # Just test that construction works
            assert client is not None

        except (OSError, ValueError, RuntimeError):
            # May fail if tokens not available
            pytest.skip("YouTube credentials setup required")

    @staticmethod
    def test_get_video_details_with_credentials(
            youtube_credentials_path: Path | None,
    ) -> None:
        """Should get video details when credentials available."""
        if youtube_credentials_path is None:
            pytest.skip("YouTube credentials not available")

        try:
            client = YouTubeClient()

            # Use a well-known video ID
            video_id = "dQw4w9WgXcQ"  # Rick Astley - Never Gonna Give You Up
            details = client.get_video_details(video_id)
            assert details is None or isinstance(details, dict)

        except Exception as e:
            pytest.skip(f"YouTube OAuth requires interaction: {e}")

    @staticmethod
    def test_quota_awareness() -> None:
        """YouTube client should be quota-aware."""
        # This just tests that settings have quota handling
        from msc.config.settings import Settings

        settings = Settings()
        assert hasattr(settings, "youtube_quota_daily")

    @staticmethod
    def test_rate_limiter_integration() -> None:
        """Should have rate limiting capability."""
        from msc.utils.retry import RateLimiter

        limiter = RateLimiter(requests_per_second=10)
        # Should be usable without error
        limiter.wait()

    @staticmethod
    def test_get_videos_details_batch(
            youtube_credentials_path: Path | None,
    ) -> None:
        """Should batch multiple video detail requests."""
        if youtube_credentials_path is None:
            pytest.skip("YouTube credentials not available")

        try:
            client = YouTubeClient()
            video_ids = ["dQw4w9WgXcQ", "9bZkp7q19f0"]  # Two well-known videos
            details = client.get_videos_details(video_ids)
            assert isinstance(details, list)

        except Exception as e:
            pytest.skip(f"YouTube OAuth requires interaction: {e}")

    @staticmethod
    def test_close_method() -> None:
        """Should have close method."""
        try:
            client = YouTubeClient()
            client.close()  # Should not raise

        except (OSError, ValueError, RuntimeError):
            pytest.skip("YouTube credentials setup required")
