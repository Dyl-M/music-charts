"""Unit tests for YouTube client module.

Tests YouTubeClient API functionality with mocked responses.
"""

# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.clients.youtube import YouTubeClient


@pytest.fixture
def mock_settings():
    """Mock settings for YouTube client."""
    with patch("msc.clients.youtube.get_settings") as mock:
        settings = MagicMock()
        settings.youtube_rate_limit = 10
        settings.youtube_quota_daily = 10000
        settings.get_youtube_credentials.return_value = None
        settings.get_youtube_oauth.return_value = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_secret",
            }
        }
        mock.return_value = settings
        yield settings


@pytest.fixture
def mock_oauth_flow():
    """Mock OAuth flow."""
    with patch("msc.clients.youtube.InstalledAppFlow") as mock:
        flow = MagicMock()
        credentials = MagicMock()
        credentials.token = "test_token"
        credentials.refresh_token = "test_refresh"
        credentials.token_uri = "https://oauth2.googleapis.com/token"
        credentials.client_id = "test_client_id"
        credentials.client_secret = "test_secret"
        credentials.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        flow.run_local_server.return_value = credentials
        mock.from_client_config.return_value = flow
        yield mock


@pytest.fixture
def mock_pyyoutube():
    """Mock pyyoutube client."""
    with patch("msc.clients.youtube.pyt") as mock:
        yield mock


@pytest.fixture
def client(mock_settings, mock_oauth_flow, mock_pyyoutube):
    """Create a YouTubeClient with mocked dependencies."""
    client = YouTubeClient()
    # Force authentication
    # noinspection PyProtectedMember
    client._authenticate()
    return client


class TestYouTubeClientInit:
    """Tests for YouTubeClient initialization."""

    @staticmethod
    def test_uses_settings_rate_limit(mock_settings, mock_oauth_flow, mock_pyyoutube) -> None:
        """Should use rate limit from settings."""
        client = YouTubeClient()
        assert client.rate_limiter is not None

    @staticmethod
    def test_uses_provided_rate_limit(mock_settings, mock_oauth_flow, mock_pyyoutube) -> None:
        """Should use provided rate limit."""
        client = YouTubeClient(rate_limit=5)
        # Rate limiter should be created with custom limit
        assert client.rate_limiter is not None

    @staticmethod
    def test_starts_without_client(mock_settings) -> None:
        """Should start without YouTube client."""
        with patch("msc.clients.youtube.InstalledAppFlow"):
            client = YouTubeClient()
            assert client._youtube_client is None


class TestYouTubeClientAuthentication:
    """Tests for YouTubeClient authentication."""

    @staticmethod
    def test_runs_oauth_flow_when_no_credentials(
        mock_settings, mock_oauth_flow, mock_pyyoutube
    ) -> None:
        """Should run OAuth flow when no cached credentials."""
        client = YouTubeClient()
        client._authenticate()
        mock_oauth_flow.from_client_config.assert_called_once()

    @staticmethod
    def test_uses_cached_credentials(mock_settings, mock_pyyoutube) -> None:
        """Should use cached credentials when available."""
        mock_settings.get_youtube_credentials.return_value = {
            "token": "cached_token",
            "refresh_token": "cached_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_id",
            "client_secret": "test_secret",
            "scopes": ["scope1"],
        }

        with patch("msc.clients.youtube.Credentials") as mock_creds:
            creds = MagicMock()
            creds.expired = False
            mock_creds.from_authorized_user_info.return_value = creds

            client = YouTubeClient()
            client._authenticate()
            mock_creds.from_authorized_user_info.assert_called_once()


class TestYouTubeClientHealthCheck:
    """Tests for YouTubeClient.health_check method."""

    @staticmethod
    def test_returns_true_on_success(client) -> None:
        """Should return True when API responds."""
        with patch.object(client, "get_video_details", return_value={"title": "Test"}):
            assert client.health_check() is True

    @staticmethod
    def test_returns_false_on_error(client) -> None:
        """Should return False when API fails."""
        with patch.object(client, "get_video_details", side_effect=Exception("Error")):
            assert client.health_check() is False


class TestYouTubeClientGetQuota:
    """Tests for YouTubeClient.get_quota method."""

    @staticmethod
    def test_returns_quota_info(client, mock_settings) -> None:
        """Should return quota information."""
        result = client.get_quota()
        assert result["daily_limit"] == 10000
        assert "note" in result


class TestYouTubeClientGetVideoDetails:
    """Tests for YouTubeClient.get_video_details method."""

    @staticmethod
    def test_returns_video_data(client, mock_pyyoutube) -> None:
        """Should return parsed video data."""
        mock_video = MagicMock()
        mock_video.id = "test123"
        mock_video.snippet.title = "Test Video"
        mock_video.snippet.description = "Test Description"
        mock_video.snippet.channelId = "UC123"
        mock_video.snippet.channelTitle = "Test Channel"
        mock_video.snippet.publishedAt = "2020-01-01T00:00:00Z"
        mock_video.contentDetails.duration = "PT3M30S"
        mock_video.statistics.viewCount = "1000000"
        mock_video.statistics.likeCount = "50000"
        mock_video.statistics.commentCount = "1000"

        client.youtube_client.videos.list.return_value.items = [mock_video]

        result = client.get_video_details("test123")
        assert result["video_id"] == "test123"
        assert result["title"] == "Test Video"
        assert result["view_count"] == 1000000

    @staticmethod
    def test_returns_empty_for_empty_id(client) -> None:
        """Should return empty dict for empty video ID."""
        result = client.get_video_details("")
        assert result == {}

    @staticmethod
    def test_returns_empty_when_not_found(client) -> None:
        """Should return empty dict when video not found."""
        client.youtube_client.videos.list.return_value.items = []
        result = client.get_video_details("nonexistent")
        assert result == {}


class TestYouTubeClientGetVideosDetails:
    """Tests for YouTubeClient.get_videos_details method."""

    @staticmethod
    def test_returns_empty_for_empty_list(client) -> None:
        """Should return empty list for empty input."""
        result = client.get_videos_details([])
        assert result == []

    @staticmethod
    def test_filters_empty_ids(client) -> None:
        """Should filter out empty video IDs."""
        result = client.get_videos_details(["", "  ", None])  # type: ignore[list-item]
        assert result == []

    @staticmethod
    def test_batches_requests(client) -> None:
        """Should batch requests for many videos."""
        # Create 60 video IDs (more than batch size of 50)
        video_ids = [f"vid{i}" for i in range(60)]

        with patch.object(client, "_fetch_video_batch", return_value=[]) as mock_fetch:
            client.get_videos_details(video_ids)
            # Should be called twice (50 + 10)
            assert mock_fetch.call_count == 2


class TestYouTubeClientGetPlaylistVideos:
    """Tests for YouTubeClient.get_playlist_videos method."""

    @staticmethod
    def test_returns_empty_for_empty_id(client) -> None:
        """Should return empty list for empty playlist ID."""
        result = client.get_playlist_videos("")
        assert result == []

    @staticmethod
    def test_handles_pagination(client) -> None:
        """Should handle paginated responses."""
        mock_item = MagicMock()
        mock_item.contentDetails.videoId = "vid123"
        mock_item.snippet.title = "Test Video"
        mock_item.snippet.description = "Description"
        mock_item.snippet.channelId = "UC123"
        mock_item.snippet.channelTitle = "Channel"
        mock_item.snippet.publishedAt = "2020-01-01"
        mock_item.snippet.position = 0

        # First page has next token, second page doesn't
        first_response = MagicMock()
        first_response.items = [mock_item]
        first_response.nextPageToken = "token123"

        second_response = MagicMock()
        second_response.items = [mock_item]
        second_response.nextPageToken = None

        client.youtube_client.playlistItems.list.side_effect = [
            first_response,
            second_response,
        ]

        result = client.get_playlist_videos("playlist123")
        assert len(result) == 2


class TestYouTubeClientParseVideoData:
    """Tests for YouTubeClient._parse_video_data method."""

    @staticmethod
    def test_parses_all_fields() -> None:
        """Should parse all video fields."""
        mock_video = MagicMock()
        mock_video.id = "vid123"
        mock_video.snippet.title = "Title"
        mock_video.snippet.description = "Desc"
        mock_video.snippet.channelId = "UC123"
        mock_video.snippet.channelTitle = "Channel"
        mock_video.snippet.publishedAt = "2020-01-01"
        mock_video.contentDetails.duration = "PT5M"
        mock_video.statistics.viewCount = "500"
        mock_video.statistics.likeCount = "50"
        mock_video.statistics.commentCount = "5"

        result = YouTubeClient._parse_video_data(mock_video)
        assert result["video_id"] == "vid123"
        assert result["title"] == "Title"
        assert result["view_count"] == 500
        assert result["like_count"] == 50
        assert result["comment_count"] == 5

    @staticmethod
    def test_handles_missing_statistics() -> None:
        """Should handle missing statistics gracefully."""
        mock_video = MagicMock()
        mock_video.id = "vid123"
        mock_video.snippet.title = "Title"
        mock_video.snippet.description = "Desc"
        mock_video.snippet.channelId = "UC123"
        mock_video.snippet.channelTitle = "Channel"
        mock_video.snippet.publishedAt = "2020-01-01"
        mock_video.contentDetails.duration = "PT5M"
        mock_video.statistics = None

        result = YouTubeClient._parse_video_data(mock_video)
        assert result["view_count"] == 0
        assert result["like_count"] == 0
        assert result["comment_count"] == 0


class TestYouTubeClientParsePlaylistItem:
    """Tests for YouTubeClient._parse_playlist_item method."""

    @staticmethod
    def test_parses_all_fields() -> None:
        """Should parse all playlist item fields."""
        mock_item = MagicMock()
        mock_item.contentDetails.videoId = "vid123"
        mock_item.snippet.title = "Title"
        mock_item.snippet.description = "Desc"
        mock_item.snippet.channelId = "UC123"
        mock_item.snippet.channelTitle = "Channel"
        mock_item.snippet.publishedAt = "2020-01-01"
        mock_item.snippet.position = 5

        result = YouTubeClient._parse_playlist_item(mock_item)
        assert result["video_id"] == "vid123"
        assert result["title"] == "Title"
        assert result["position"] == 5


class TestYouTubeClientClose:
    """Tests for YouTubeClient cleanup."""

    @staticmethod
    def test_clears_youtube_client(client) -> None:
        """Should clear YouTube client on close."""
        client.close()
        assert client._youtube_client is None

    @staticmethod
    def test_clears_credentials(client) -> None:
        """Should clear credentials on close."""
        client.close()
        assert client._credentials is None
