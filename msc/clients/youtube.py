"""YouTube Data API client for video metadata and playlist management."""

# Standard library
from typing import Any, Optional

# Third-party
import pyyoutube as pyt
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Local
from msc.clients.base import BaseClient
from msc.config.settings import get_settings


class YouTubeClient(BaseClient):
    """Client for interacting with YouTube Data API v3.

    Provides OAuth2-authenticated access to YouTube video metadata and
    playlist management using the pyyoutube library wrapper.

    Examples:
        >>> with YouTubeClient() as client:
        ...     video = client.get_video_details("dQw4w9WgXcQ")
        ...     print(video["title"])
    """

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl",
    ]

    def __init__(self, rate_limit: int | None = None, timeout: int = 30) -> None:
        """Initialize YouTube client with OAuth credentials.

        Args:
            rate_limit: Maximum requests per second (default: from settings).
            timeout: Request timeout in seconds (default: 30).
        """
        settings = get_settings()
        if rate_limit is None:
            rate_limit = settings.youtube_rate_limit

        super().__init__(api_key=None, rate_limit=rate_limit, timeout=timeout)
        self.settings = settings
        self._youtube_client: Optional[pyt.Client] = None
        self._credentials: Optional[Credentials] = None

    @property
    def youtube_client(self) -> pyt.Client:
        """Get or create authenticated pyyoutube.Client.

        Lazy initialization of the YouTube API client. Authenticates on first access.

        Returns:
            pyyoutube.Client: Authenticated YouTube API client.
        """
        if self._youtube_client is None:
            self._authenticate()

        return self._youtube_client  # type: ignore[return-value]

    def _authenticate(self) -> None:
        """Authenticate with YouTube API using OAuth2 flow.

        Attempts to use cached credentials first. If credentials are expired,
        refreshes them. If no valid credentials exist, runs OAuth flow.
        """
        cached_creds = self.settings.get_youtube_credentials()

        if cached_creds:
            self._credentials = Credentials.from_authorized_user_info(cached_creds, self.SCOPES)

            if self._credentials.expired and self._credentials.refresh_token:
                try:
                    self._credentials.refresh(GoogleRequest())
                    self._save_credentials()
                    self.logger.info("Refreshed expired YouTube credentials")
                except RefreshError:
                    self.logger.warning("Failed to refresh credentials, running OAuth flow")
                    self._run_oauth_flow()
        else:
            self._run_oauth_flow()

        self._youtube_client = pyt.Client(
            client_id=self._credentials.client_id,
            client_secret=self._credentials.client_secret,
            access_token=self._credentials.token,
        )

    def _run_oauth_flow(self) -> None:
        """Run OAuth2 authorization flow via browser.

        Opens browser for user consent, exchanges authorization code for tokens.
        """
        oauth_config = self.settings.get_youtube_oauth()
        flow = InstalledAppFlow.from_client_config(oauth_config, self.SCOPES)
        self._credentials = flow.run_local_server(port=0)
        self._save_credentials()
        self.logger.info("Completed OAuth flow for YouTube credentials")

    def _save_credentials(self) -> None:
        """Save credentials to cache file for future use."""
        if self._credentials:
            creds_dict = {
                "token": self._credentials.token,
                "refresh_token": self._credentials.refresh_token,
                "token_uri": self._credentials.token_uri,
                "client_id": self._credentials.client_id,
                "client_secret": self._credentials.client_secret,
                "scopes": self._credentials.scopes,
            }
            self.settings.save_youtube_credentials(creds_dict)

    def health_check(self) -> bool:
        """Check if YouTube API is accessible.

        Returns:
            bool: True if API is accessible, False otherwise.
        """
        try:
            result = self.get_video_details("dQw4w9WgXcQ")
            return bool(result)

        except Exception as e:
            self.logger.error("Health check failed: %s", e)
            return False

    def get_quota(self) -> dict[str, Any]:
        """Get YouTube API quota information.

        Returns:
            dict[str, Any]: Quota information including daily limit.
        """
        return {
            "daily_limit": self.settings.youtube_quota_daily,
            "note": "YouTube API quota is 10,000 units/day by default",
        }

    def get_video_details(self, video_id: str) -> dict[str, Any]:
        """Fetch metadata for a single YouTube video.

        Args:
            video_id: YouTube video ID (e.g., "dQw4w9WgXcQ").

        Returns:
            dict[str, Any]: Video metadata or empty dict if not found/failed.

        Examples:
            >>> client = YouTubeClient()
            >>> video = client.get_video_details("dQw4w9WgXcQ")
            >>> print(video["title"])
            'Rick Astley - Never Gonna Give You Up'
        """
        if not video_id or not video_id.strip():
            self.logger.error("Video ID is empty")
            return {}

        video_id = video_id.strip()

        try:
            with self.rate_limiter:
                response = self.youtube_client.videos.list(
                    video_id=video_id,
                    parts=["id", "snippet", "statistics", "contentDetails"],
                )

            if not response.items:
                self.logger.warning("Video not found: %s", video_id)
                return {}

            return self._parse_video_data(response.items[0])

        except pyt.error.PyYouTubeException as e:
            self.logger.error("Failed to fetch video %s: %s", video_id, e)
            return {}

    def get_videos_details(self, video_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch metadata for multiple YouTube videos in batches.

        Args:
            video_ids: List of YouTube video IDs.

        Returns:
            list[dict[str, Any]]: List of video metadata dicts.

        Examples:
            >>> client = YouTubeClient()
            >>> videos = client.get_videos_details(["dQw4w9WgXcQ", "9bZkp7q19f0"])
            >>> len(videos)
            2
        """
        if not video_ids:
            return []

        # Filter out empty/whitespace IDs
        valid_ids = [vid.strip() for vid in video_ids if vid and vid.strip()]
        if not valid_ids:
            return []

        # Batch into groups of 50 (YouTube API limit)
        results = []
        for i in range(0, len(valid_ids), 50):
            batch = valid_ids[i: i + 50]
            results.extend(self._fetch_video_batch(batch))

        return results

    def _fetch_video_batch(self, video_ids: list[str]) -> list[dict[str, Any]]:
        """Fetch a batch of up to 50 videos.

        Args:
            video_ids: List of up to 50 video IDs.

        Returns:
            list[dict[str, Any]]: List of video metadata dicts.
        """
        try:
            with self.rate_limiter:
                response = self.youtube_client.videos.list(
                    video_id=",".join(video_ids),
                    parts=["id", "snippet", "statistics", "contentDetails"],
                )

            return [self._parse_video_data(video) for video in response.items]

        except pyt.error.PyYouTubeException as e:
            self.logger.error("Failed to fetch video batch: %s", e)
            return []

    def get_playlist_videos(self, playlist_id: str) -> list[dict[str, Any]]:
        """Fetch all videos from a YouTube playlist.

        Handles pagination automatically to retrieve all videos.

        Args:
            playlist_id: YouTube playlist ID.

        Returns:
            list[dict[str, Any]]: List of video metadata dicts.

        Examples:
            >>> client = YouTubeClient()
            >>> videos = client.get_playlist_videos("PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf")
            >>> len(videos)
            15
        """
        if not playlist_id or not playlist_id.strip():
            self.logger.error("Playlist ID is empty")
            return []

        playlist_id = playlist_id.strip()
        results = []
        next_page_token = None

        try:
            while True:
                with self.rate_limiter:
                    response = self.youtube_client.playlistItems.list(
                        playlist_id=playlist_id,
                        parts=["snippet", "contentDetails"],
                        max_results=50,
                        page_token=next_page_token,
                    )

                results.extend([self._parse_playlist_item(item) for item in response.items])

                next_page_token = response.nextPageToken
                if not next_page_token:
                    break

            self.logger.debug("Fetched %d videos from playlist %s", len(results), playlist_id)
            return results

        except pyt.error.PyYouTubeException as e:
            self.logger.error("Failed to fetch playlist %s: %s", playlist_id, e)
            return []

    @staticmethod
    def _parse_video_data(video: Any) -> dict[str, Any]:
        """Parse pyyoutube.Video object to dictionary.

        Args:
            video: pyyoutube.Video object.

        Returns:
            dict[str, Any]: Parsed video metadata.
        """
        return {
            "video_id": video.id,
            "title": video.snippet.title if video.snippet else None,
            "description": video.snippet.description if video.snippet else None,
            "channel_id": video.snippet.channelId if video.snippet else None,
            "channel_name": video.snippet.channelTitle if video.snippet else None,
            "published_at": video.snippet.publishedAt if video.snippet else None,
            "duration": video.contentDetails.duration if video.contentDetails else None,
            "view_count": int(video.statistics.viewCount) if video.statistics and video.statistics.viewCount else 0,
            "like_count": int(video.statistics.likeCount) if video.statistics and video.statistics.likeCount else 0,
            "comment_count": (
                int(video.statistics.commentCount) if video.statistics and video.statistics.commentCount else 0
            ),
        }

    @staticmethod
    def _parse_playlist_item(item: Any) -> dict[str, Any]:
        """Parse pyyoutube.PlaylistItem object to dictionary.

        Args:
            item: pyyoutube.PlaylistItem object.

        Returns:
            dict[str, Any]: Parsed playlist item metadata.
        """
        return {
            "video_id": item.contentDetails.videoId if item.contentDetails else None,
            "title": item.snippet.title if item.snippet else None,
            "description": item.snippet.description if item.snippet else None,
            "channel_id": item.snippet.channelId if item.snippet else None,
            "channel_name": item.snippet.channelTitle if item.snippet else None,
            "published_at": item.snippet.publishedAt if item.snippet else None,
            "position": item.snippet.position if item.snippet else None,
        }

    def close(self) -> None:
        """Close client and cleanup resources."""
        super().close()
        self._youtube_client = None
        self._credentials = None
