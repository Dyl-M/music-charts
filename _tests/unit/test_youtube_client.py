"""Unit tests for YouTubeClient."""

# Standard library
from unittest.mock import MagicMock, PropertyMock, patch

# Third-party
import pyyoutube as pyt
from google.auth.exceptions import RefreshError

# Local
from msc.clients.youtube import YouTubeClient


class TestYouTubeClientInit:
    """Tests for YouTubeClient initialization."""

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_init_with_default_rate_limit(mock_settings: MagicMock) -> None:
        """Should use rate_limit from settings when not provided."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 15
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        assert client.rate_limiter.requests_per_second == 15

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_init_with_explicit_rate_limit(mock_settings: MagicMock) -> None:
        """Should use explicit rate_limit when provided."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient(rate_limit=25)
        assert client.rate_limiter.requests_per_second == 25

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_init_api_key_is_none(mock_settings: MagicMock) -> None:
        """Should initialize with api_key=None."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        assert client.api_key is None

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_init_stores_settings(mock_settings: MagicMock) -> None:
        """Should store settings instance."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        assert client.settings == mock_settings_instance

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_init_lazy_youtube_client(mock_settings: MagicMock) -> None:
        """Should not initialize _youtube_client on construction."""
        mock_settings_instance = MagicMock()
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        assert client._youtube_client is None


class TestAuthentication:
    """Tests for YouTube OAuth authentication."""

    @staticmethod
    @patch("msc.clients.youtube.pyt.Client")
    @patch("msc.clients.youtube.Credentials")
    @patch("msc.clients.youtube.get_settings")
    def test_authenticate_with_valid_cached_credentials(
            mock_settings: MagicMock, mock_creds_class: MagicMock, mock_client_class: MagicMock
    ) -> None:
        """Should use valid cached credentials without refresh."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.get_youtube_credentials.return_value = {
            "token": "test_token",
            "refresh_token": "test_refresh",
        }
        mock_settings.return_value = mock_settings_instance

        mock_creds = MagicMock()
        mock_creds.expired = False
        mock_creds.client_id = "test_client_id"
        mock_creds.client_secret = "test_client_secret"
        mock_creds.token = "test_token"
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        client = YouTubeClient()
        client._authenticate()

        mock_creds_class.from_authorized_user_info.assert_called_once()
        mock_creds.refresh.assert_not_called()
        mock_client_class.assert_called_once_with(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="test_token",
        )

    @staticmethod
    @patch("msc.clients.youtube.pyt.Client")
    @patch("msc.clients.youtube.GoogleRequest")
    @patch("msc.clients.youtube.Credentials")
    @patch("msc.clients.youtube.get_settings")
    def test_authenticate_with_expired_credentials(
            mock_settings: MagicMock,
            mock_creds_class: MagicMock,
            _mock_request_class: MagicMock,
            mock_client_class: MagicMock,
    ) -> None:
        """Should refresh expired credentials."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.get_youtube_credentials.return_value = {
            "token": "test_token",
            "refresh_token": "test_refresh",
        }
        mock_settings.return_value = mock_settings_instance

        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token = "new_token"
        mock_creds.client_id = "test_client_id"
        mock_creds.client_secret = "test_client_secret"
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        client = YouTubeClient()
        client._authenticate()

        mock_creds.refresh.assert_called_once()
        mock_client_class.assert_called_once_with(
            client_id="test_client_id",
            client_secret="test_client_secret",
            access_token="new_token",
        )

    @staticmethod
    @patch.object(YouTubeClient, "_run_oauth_flow")
    @patch("msc.clients.youtube.pyt.Client")
    @patch("msc.clients.youtube.Credentials")
    @patch("msc.clients.youtube.get_settings")
    def test_authenticate_with_refresh_error(
            mock_settings: MagicMock,
            mock_creds_class: MagicMock,
            _mock_client_class: MagicMock,
            mock_oauth_flow: MagicMock,
    ) -> None:
        """Should run OAuth flow when refresh fails."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.get_youtube_credentials.return_value = {
            "token": "test_token",
            "refresh_token": "test_refresh",
        }
        mock_settings.return_value = mock_settings_instance

        mock_creds = MagicMock()
        mock_creds.expired = True
        mock_creds.refresh_token = "test_refresh"
        mock_creds.refresh.side_effect = RefreshError("Token expired")
        mock_creds_class.from_authorized_user_info.return_value = mock_creds

        new_creds = MagicMock()
        mock_oauth_flow.return_value = None

        client = YouTubeClient()
        client._credentials = new_creds
        client._authenticate()

        mock_oauth_flow.assert_called_once()

    @staticmethod
    @patch.object(YouTubeClient, "_run_oauth_flow")
    @patch("msc.clients.youtube.pyt.Client")
    @patch("msc.clients.youtube.get_settings")
    def test_authenticate_with_no_cached_credentials(
            mock_settings: MagicMock, mock_client_class: MagicMock, mock_oauth_flow: MagicMock
    ) -> None:
        """Should run OAuth flow when no cached credentials exist."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.get_youtube_credentials.return_value = None
        mock_settings.return_value = mock_settings_instance

        new_creds = MagicMock()
        new_creds.client_id = "oauth_client_id"
        new_creds.client_secret = "oauth_client_secret"
        new_creds.token = "oauth_token"
        mock_oauth_flow.return_value = None

        client = YouTubeClient()
        client._credentials = new_creds
        client._authenticate()

        mock_oauth_flow.assert_called_once()
        mock_client_class.assert_called_once_with(
            client_id="oauth_client_id",
            client_secret="oauth_client_secret",
            access_token="oauth_token",
        )

    @staticmethod
    @patch("msc.clients.youtube.InstalledAppFlow")
    @patch("msc.clients.youtube.get_settings")
    def test_run_oauth_flow(mock_settings: MagicMock, mock_flow_class: MagicMock) -> None:
        """Should run OAuth flow and save credentials."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.get_youtube_oauth.return_value = {"installed": {"client_id": "test"}}
        mock_settings.return_value = mock_settings_instance

        mock_flow = MagicMock()
        mock_creds = MagicMock()
        mock_creds.token = "new_token"
        mock_creds.refresh_token = "new_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "test_id"
        mock_creds.client_secret = "test_secret"
        mock_creds.scopes = YouTubeClient.SCOPES

        mock_flow.run_local_server.return_value = mock_creds
        mock_flow_class.from_client_config.return_value = mock_flow

        client = YouTubeClient()
        client._run_oauth_flow()

        mock_flow_class.from_client_config.assert_called_once()
        mock_flow.run_local_server.assert_called_once_with(port=0)
        assert client._credentials == mock_creds

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_save_credentials(mock_settings: MagicMock) -> None:
        """Should save credentials to file via settings."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_creds = MagicMock()
        mock_creds.token = "test_token"
        mock_creds.refresh_token = "test_refresh"
        mock_creds.token_uri = "https://oauth2.googleapis.com/token"
        mock_creds.client_id = "test_id"
        mock_creds.client_secret = "test_secret"
        mock_creds.scopes = YouTubeClient.SCOPES

        client = YouTubeClient()
        client._credentials = mock_creds
        client._save_credentials()

        mock_settings_instance.save_youtube_credentials.assert_called_once()
        saved_dict = mock_settings_instance.save_youtube_credentials.call_args[0][0]
        assert saved_dict["token"] == "test_token"
        assert saved_dict["refresh_token"] == "test_refresh"

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_save_credentials_with_none(mock_settings: MagicMock) -> None:
        """Should not save when credentials are None."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        client._credentials = None
        client._save_credentials()

        mock_settings_instance.save_youtube_credentials.assert_not_called()


class TestHealthCheck:
    """Tests for health_check method."""

    @staticmethod
    @patch.object(YouTubeClient, "get_video_details")
    @patch("msc.clients.youtube.get_settings")
    def test_health_check_success(mock_settings: MagicMock, mock_get_video: MagicMock) -> None:
        """Should return True when API is accessible."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_get_video.return_value = {"video_id": "dQw4w9WgXcQ", "title": "Test Video"}

        client = YouTubeClient()
        assert client.health_check() is True

    @staticmethod
    @patch.object(YouTubeClient, "get_video_details")
    @patch("msc.clients.youtube.get_settings")
    def test_health_check_failure_empty_result(mock_settings: MagicMock, mock_get_video: MagicMock) -> None:
        """Should return False when get_video_details returns empty dict."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_get_video.return_value = {}

        client = YouTubeClient()
        assert client.health_check() is False

    @staticmethod
    @patch.object(YouTubeClient, "get_video_details")
    @patch("msc.clients.youtube.get_settings")
    def test_health_check_failure_exception(mock_settings: MagicMock, mock_get_video: MagicMock) -> None:
        """Should return False when exception is raised."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_get_video.side_effect = Exception("API Error")

        client = YouTubeClient()
        assert client.health_check() is False


class TestGetQuota:
    """Tests for get_quota method."""

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_quota_returns_daily_limit(mock_settings: MagicMock) -> None:
        """Should return daily quota limit from settings."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.youtube_quota_daily = 15000
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        quota = client.get_quota()

        assert quota["daily_limit"] == 15000

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_quota_has_note_field(mock_settings: MagicMock) -> None:
        """Should include note field in quota response."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings_instance.youtube_quota_daily = 10000
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        quota = client.get_quota()

        assert "note" in quota
        assert "YouTube API quota" in quota["note"]


class TestGetVideoDetails:
    """Tests for get_video_details method."""

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_video_details_success(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should return video metadata for valid video ID."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # Setup mock video object
        mock_video = MagicMock()
        mock_video.id = "test123"
        mock_video.snippet.title = "Test Video"
        mock_video.snippet.description = "Test Description"
        mock_video.snippet.channelId = "UC123"
        mock_video.snippet.channelTitle = "Test Channel"
        mock_video.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_video.contentDetails.duration = "PT5M30S"
        mock_video.statistics.viewCount = "1000"
        mock_video.statistics.likeCount = "100"
        mock_video.statistics.commentCount = "10"

        mock_response = MagicMock()
        mock_response.items = [mock_video]

        mock_yt = MagicMock()
        mock_yt.videos.list.return_value = mock_response
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_video_details("test123")

        assert result["video_id"] == "test123"
        assert result["title"] == "Test Video"
        assert result["view_count"] == 1000

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_video_details_empty_video_id(mock_settings: MagicMock) -> None:
        """Should return empty dict for empty video ID."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_video_details("")

        assert result == {}

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_video_details_whitespace_video_id(mock_settings: MagicMock) -> None:
        """Should return empty dict for whitespace-only video ID."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_video_details("   ")

        assert result == {}

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_video_details_api_failure(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should return empty dict on API failure."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_yt = MagicMock()
        mock_yt.videos.list.side_effect = pyt.error.PyYouTubeException("API Error")  # type: ignore[arg-type]
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_video_details("test123")

        assert result == {}

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_video_details_no_results(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should return empty dict when video not found."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_response = MagicMock()
        mock_response.items = []

        mock_yt = MagicMock()
        mock_yt.videos.list.return_value = mock_response
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_video_details("nonexistent")

        assert result == {}


class TestGetVideosDetails:
    """Tests for get_videos_details method."""

    @staticmethod
    @patch.object(YouTubeClient, "_fetch_video_batch")
    @patch("msc.clients.youtube.get_settings")
    def test_get_videos_details_empty_list(mock_settings: MagicMock, mock_fetch: MagicMock) -> None:
        """Should return empty list for empty input."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_videos_details([])

        assert result == []
        mock_fetch.assert_not_called()

    @staticmethod
    @patch.object(YouTubeClient, "_fetch_video_batch")
    @patch("msc.clients.youtube.get_settings")
    def test_get_videos_details_single_video(mock_settings: MagicMock, mock_fetch: MagicMock) -> None:
        """Should fetch single video without chunking."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_fetch.return_value = [{"video_id": "test123", "title": "Test"}]

        client = YouTubeClient()
        result = client.get_videos_details(["test123"])

        assert len(result) == 1
        mock_fetch.assert_called_once_with(["test123"])

    @staticmethod
    @patch.object(YouTubeClient, "_fetch_video_batch")
    @patch("msc.clients.youtube.get_settings")
    def test_get_videos_details_chunking(mock_settings: MagicMock, mock_fetch: MagicMock) -> None:
        """Should chunk large lists into batches of 50."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # 120 videos should result in 3 batches (50, 50, 20)
        video_ids = [f"video_{i}" for i in range(120)]
        mock_fetch.return_value = [{"video_id": f"video_{i}"} for i in range(50)]

        client = YouTubeClient()
        result = client.get_videos_details(video_ids)

        assert mock_fetch.call_count == 3
        assert len(result) == 150  # 3 batches × 50 results

    @staticmethod
    @patch.object(YouTubeClient, "_fetch_video_batch")
    @patch("msc.clients.youtube.get_settings")
    def test_get_videos_details_filters_empty_ids(mock_settings: MagicMock, mock_fetch: MagicMock) -> None:
        """Should filter out empty and whitespace-only IDs."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_fetch.return_value = [{"video_id": "valid1"}, {"video_id": "valid2"}]

        client = YouTubeClient()
        client.get_videos_details(["valid1", "", "valid2", "   "])

        mock_fetch.assert_called_once_with(["valid1", "valid2"])

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_videos_details_all_empty_ids(mock_settings: MagicMock) -> None:
        """Should return empty list when all IDs are empty/whitespace."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_videos_details(["", "   ", ""])

        assert result == []


class TestGetPlaylistVideos:
    """Tests for get_playlist_videos method."""

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_playlist_videos_empty_playlist_id(mock_settings: MagicMock) -> None:
        """Should return empty list for empty playlist ID."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_playlist_videos("")

        assert result == []

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_playlist_videos_pagination(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should handle pagination with nextPageToken."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # First page
        mock_item1 = MagicMock()
        mock_item1.contentDetails.videoId = "video1"
        mock_item1.snippet.title = "Video 1"
        mock_item1.snippet.description = "Description 1"
        mock_item1.snippet.channelId = "UC123"
        mock_item1.snippet.channelTitle = "Channel"
        mock_item1.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_item1.snippet.position = 0

        # Second page
        mock_item2 = MagicMock()
        mock_item2.contentDetails.videoId = "video2"
        mock_item2.snippet.title = "Video 2"
        mock_item2.snippet.description = "Description 2"
        mock_item2.snippet.channelId = "UC123"
        mock_item2.snippet.channelTitle = "Channel"
        mock_item2.snippet.publishedAt = "2024-01-02T00:00:00Z"
        mock_item2.snippet.position = 1

        mock_response1 = MagicMock()
        mock_response1.items = [mock_item1]
        mock_response1.nextPageToken = "token123"

        mock_response2 = MagicMock()
        mock_response2.items = [mock_item2]
        mock_response2.nextPageToken = None

        mock_yt = MagicMock()
        mock_yt.playlistItems.list.side_effect = [mock_response1, mock_response2]
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_playlist_videos("PL123")

        assert len(result) == 2
        assert result[0]["video_id"] == "video1"
        assert result[1]["video_id"] == "video2"

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_playlist_videos_single_page(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should handle single page response."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_item = MagicMock()
        mock_item.contentDetails.videoId = "video1"
        mock_item.snippet.title = "Video 1"
        mock_item.snippet.description = "Description"
        mock_item.snippet.channelId = "UC123"
        mock_item.snippet.channelTitle = "Channel"
        mock_item.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_item.snippet.position = 0

        mock_response = MagicMock()
        mock_response.items = [mock_item]
        mock_response.nextPageToken = None

        mock_yt = MagicMock()
        mock_yt.playlistItems.list.return_value = mock_response
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_playlist_videos("PL123")

        assert len(result) == 1
        assert result[0]["video_id"] == "video1"

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_get_playlist_videos_api_failure(mock_settings: MagicMock, mock_client_prop: PropertyMock) -> None:
        """Should return empty list on API failure."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_yt = MagicMock()
        mock_yt.playlistItems.list.side_effect = pyt.error.PyYouTubeException("API Error")  # type: ignore[arg-type]
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client.get_playlist_videos("PL123")

        assert result == []

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_get_playlist_videos_whitespace_id(mock_settings: MagicMock) -> None:
        """Should return empty list for whitespace-only playlist ID."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        result = client.get_playlist_videos("   ")

        assert result == []


class TestHelperMethods:
    """Tests for static helper methods."""

    @staticmethod
    def test_parse_video_data() -> None:
        """Should parse video object to dictionary."""
        mock_video = MagicMock()
        mock_video.id = "test123"
        mock_video.snippet.title = "Test Video"
        mock_video.snippet.description = "Test Description"
        mock_video.snippet.channelId = "UC123"
        mock_video.snippet.channelTitle = "Test Channel"
        mock_video.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_video.contentDetails.duration = "PT5M30S"
        mock_video.statistics.viewCount = "1000"
        mock_video.statistics.likeCount = "100"
        mock_video.statistics.commentCount = "10"

        result = YouTubeClient._parse_video_data(mock_video)

        assert result["video_id"] == "test123"
        assert result["title"] == "Test Video"
        assert result["view_count"] == 1000
        assert result["like_count"] == 100
        assert result["comment_count"] == 10

    @staticmethod
    def test_parse_playlist_item() -> None:
        """Should parse playlist item to dictionary."""
        mock_item = MagicMock()
        mock_item.contentDetails.videoId = "video123"
        mock_item.snippet.title = "Playlist Video"
        mock_item.snippet.description = "Video from playlist"
        mock_item.snippet.channelId = "UC456"
        mock_item.snippet.channelTitle = "Playlist Channel"
        mock_item.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_item.snippet.position = 5

        result = YouTubeClient._parse_playlist_item(mock_item)

        assert result["video_id"] == "video123"
        assert result["title"] == "Playlist Video"
        assert result["position"] == 5

    @staticmethod
    def test_parse_video_data_view_count_conversion() -> None:
        """Should convert view_count string to int."""
        mock_video = MagicMock()
        mock_video.id = "test123"
        mock_video.snippet = None
        mock_video.contentDetails = None
        mock_video.statistics.viewCount = "999999"
        mock_video.statistics.likeCount = "0"
        mock_video.statistics.commentCount = "0"

        result = YouTubeClient._parse_video_data(mock_video)

        assert result["view_count"] == 999999
        assert isinstance(result["view_count"], int)

    @staticmethod
    def test_parse_video_data_none_statistics() -> None:
        """Should handle None statistics gracefully."""
        mock_video = MagicMock()
        mock_video.id = "test123"
        mock_video.snippet = None
        mock_video.contentDetails = None
        mock_video.statistics = None

        result = YouTubeClient._parse_video_data(mock_video)

        assert result["view_count"] == 0
        assert result["like_count"] == 0
        assert result["comment_count"] == 0


class TestContextManager:
    """Tests for context manager support."""

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_cleanup_on_exit(mock_settings: MagicMock) -> None:
        """Should cleanup resources on context exit."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        with YouTubeClient() as client:
            client._youtube_client = MagicMock()
            client._credentials = MagicMock()

        assert client._youtube_client is None
        assert client._credentials is None

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_close_sets_youtube_client_to_none(mock_settings: MagicMock) -> None:
        """Should set _youtube_client to None on close."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        client = YouTubeClient()
        client._youtube_client = MagicMock()
        client.close()

        assert client._youtube_client is None


class TestYouTubeClientProperty:
    """Tests for youtube_client property lazy initialization."""

    @staticmethod
    @patch.object(YouTubeClient, "_authenticate")
    @patch("msc.clients.youtube.get_settings")
    def test_youtube_client_lazy_initialization(
            mock_settings: MagicMock, mock_authenticate: MagicMock
    ) -> None:
        """Should call _authenticate on first access to youtube_client property."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # Create a mock pyyoutube client to return after authentication
        mock_yt_client = MagicMock()

        client = YouTubeClient()
        # Manually set for the test
        client._youtube_client = None

        # Simulate the property access triggering authentication
        def mock_auth() -> None:
            """Mock authenticate that sets _youtube_client."""
            client._youtube_client = mock_yt_client

        mock_authenticate.side_effect = mock_auth

        # Access property
        result = client.youtube_client

        # Verify authenticate was called and client was set
        mock_authenticate.assert_called_once()
        assert result == mock_yt_client

    @staticmethod
    @patch("msc.clients.youtube.get_settings")
    def test_youtube_client_already_initialized(mock_settings: MagicMock) -> None:
        """Should return existing client without re-authenticating."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # Create a mock pyyoutube client
        mock_yt_client = MagicMock()

        client = YouTubeClient()
        # Set the client as already initialized
        client._youtube_client = mock_yt_client

        # Access property should return existing client
        result = client.youtube_client

        # Verify it returns the same client without calling _authenticate again
        assert result == mock_yt_client


class TestFetchVideoBatch:
    """Tests for _fetch_video_batch helper method."""

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_fetch_video_batch_success(
            mock_settings: MagicMock, mock_client_prop: PropertyMock
    ) -> None:
        """Should fetch batch of videos successfully."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        # Setup mock videos
        mock_video1 = MagicMock()
        mock_video1.id = "video1"
        mock_video1.snippet.title = "Video 1"
        mock_video1.snippet.description = "Desc 1"
        mock_video1.snippet.channelId = "UC1"
        mock_video1.snippet.channelTitle = "Channel 1"
        mock_video1.snippet.publishedAt = "2024-01-01T00:00:00Z"
        mock_video1.contentDetails.duration = "PT5M"
        mock_video1.statistics.viewCount = "1000"
        mock_video1.statistics.likeCount = "100"
        mock_video1.statistics.commentCount = "10"

        mock_response = MagicMock()
        mock_response.items = [mock_video1]

        mock_yt = MagicMock()
        mock_yt.videos.list.return_value = mock_response
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client._fetch_video_batch(["video1"])

        assert len(result) == 1
        assert result[0]["video_id"] == "video1"
        assert result[0]["title"] == "Video 1"

    @staticmethod
    @patch.object(YouTubeClient, "youtube_client", new_callable=PropertyMock)
    @patch("msc.clients.youtube.get_settings")
    def test_fetch_video_batch_api_failure(
            mock_settings: MagicMock, mock_client_prop: PropertyMock
    ) -> None:
        """Should return empty list on API failure."""
        mock_settings_instance = MagicMock()
        mock_settings_instance.youtube_rate_limit = 10
        mock_settings.return_value = mock_settings_instance

        mock_yt = MagicMock()
        mock_yt.videos.list.side_effect = pyt.error.PyYouTubeException("API Error")  # type: ignore[arg-type]
        mock_client_prop.return_value = mock_yt

        client = YouTubeClient()
        result = client._fetch_video_batch(["video1"])

        assert result == []
