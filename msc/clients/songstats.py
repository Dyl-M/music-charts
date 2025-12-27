"""Songstats API client for track data and statistics."""

# Standard library
from collections import ChainMap
from typing import Any

# Third-party
import requests

# Local
from msc.clients.base import BaseClient
from msc.config.constants import Platform, SONGSTATS_ENDPOINTS
from msc.config.settings import get_settings


class SongstatsClient(BaseClient):
    """Client for interacting with the Songstats Enterprise API.

    Provides methods for searching tracks, fetching multi-platform statistics,
    historical data, and YouTube video information.

    Inherits retry logic, rate limiting, and session management from BaseClient.
    """

    def __init__(
            self,
            api_key: str | None = None,
            rate_limit: int | None = None,
            timeout: int = 30,
    ):
        """Initialize the Songstats client.

        Args:
            api_key: Songstats API key. If None, loaded from settings.
            rate_limit: Requests per second. If None, loaded from settings.
            timeout: Request timeout in seconds.
        """
        settings = get_settings()

        if api_key is None:
            api_key = settings.get_songstats_key()

        if rate_limit is None:
            rate_limit = settings.songstats_rate_limit

        super().__init__(api_key=api_key, rate_limit=rate_limit, timeout=timeout)

    # =========================================================================
    # Abstract method implementations (required by BaseClient)
    # =========================================================================

    def health_check(self) -> bool:
        """Verify API connectivity.

        Returns:
            True if the API is reachable and responding, False otherwise.
        """
        try:
            response = self.get_quota()
            return bool(response)

        except requests.HTTPError:
            self.logger.error("Health check failed: API unreachable")
            return False

    def get_quota(self) -> dict[str, Any]:
        """Get current API quota and billing status.

        Returns:
            Dictionary with quota information:
            - requests_used: Number of requests consumed
            - requests_limit: Total monthly quota
            - reset_date: Next billing cycle date

        Example:
            >>> client.get_quota()
            {
                'requests_used': 1523,
                'requests_limit': 10000,
                'reset_date': '2025-01-01T00:00:00Z'
            }
        """
        try:
            response = self.get(SONGSTATS_ENDPOINTS["status"])
            self.logger.debug("Quota check successful")
            return response

        except requests.HTTPError as e:
            self.logger.error("Failed to retrieve quota: %s", e)
            return {}

    # =========================================================================
    # Track search
    # =========================================================================

    def search_track(
            self,
            query: str,
            limit: int = 1,
    ) -> list[dict[str, Any]]:
        """Search for tracks by title and artist.

        Args:
            query: Search query string (typically "artist - title").
            limit: Maximum number of results to return.

        Returns:
            List of matching tracks with metadata:
            - songstats_track_id: Unique Songstats identifier
            - title: Track title
            - artists: List of artist names
            - isrc: International Standard Recording Code

        Example:
            >>> client.search_track("deadmau5 strobe", limit=1)
            [{'songstats_track_id': 'abc123', 'title': 'Strobe', ...}]
        """
        if not query or not query.strip():
            self.logger.error("Search query is empty")
            return []

        try:
            params = {"q": query.strip(), "limit": limit}
            response = self.get(SONGSTATS_ENDPOINTS["search"], params=params)

            results = response.get("results", [])
            self.logger.debug("Search returned %d results", len(results))
            return results

        except requests.HTTPError as e:
            self.logger.error("Search failed for query '%s': %s", query, e)
            return []

    # =========================================================================
    # Statistics endpoints
    # =========================================================================

    def get_platform_stats(
            self,
            songstats_track_id: str,
            sources: str | list[str] | None = None,
    ) -> dict[str, Any]:
        """Fetch current statistics across streaming platforms.

        Args:
            songstats_track_id: Songstats track identifier.
            sources: Platform sources to query. Can be:
                - None: Query all platforms (default)
                - str: Comma-separated platform names
                - list[str]: List of platform names

        Returns:
            Dictionary with flattened statistics:
            - {platform}_{metric}: Metric values per platform
            - Example: 'spotify_streams', 'apple_music_playlist_reach'

        Notes:
            - Returns empty dict if songstats_track_id is missing
            - Automatically maps 'tracklist' → '1001tracklists'
        """
        if not songstats_track_id or not songstats_track_id.strip():
            self.logger.error("Songstats track ID is required")
            return {}

        # Prepare sources parameter
        if sources is None:
            sources = Platform.songstats_sources()

        sources_str = ",".join(sources) if isinstance(sources, (list, tuple)) else sources

        try:
            params = {
                "songstats_track_id": songstats_track_id.strip(),
                "source": sources_str,
            }
            response = self.get(SONGSTATS_ENDPOINTS["stats"], params=params)

            # Flatten response (legacy pattern: ChainMap)
            flattened = self._flatten_stats(response.get("stats", []))
            self.logger.debug("Retrieved stats for %d platforms", len(flattened))
            return flattened

        except (requests.HTTPError, KeyError) as e:
            self.logger.error(
                "Failed to retrieve stats for track %s: %s",
                songstats_track_id,
                e,
            )
            return {}

    def get_historical_peaks(
            self,
            songstats_track_id: str,
            start_date: str,
            sources: str | list[str] | None = None,
    ) -> dict[str, int]:
        """Fetch historical peak popularity metrics.

        Args:
            songstats_track_id: Songstats track identifier.
            start_date: ISO date string (YYYY-MM-DD) for history start.
            sources: Platform sources to query. Defaults to (spotify, deezer, tidal).

        Returns:
            Dictionary with peak values:
            - {platform}_popularity_peak: Maximum popularity score

        Example:
            >>> client.get_historical_peaks('abc123', '2024-01-01')
            {'spotify_popularity_peak': 85, 'deezer_popularity_peak': 72}
        """
        if not songstats_track_id or not songstats_track_id.strip():
            self.logger.error("Songstats track ID is required")
            return {}

        # Default to platforms with popularity metrics (legacy pattern)
        if sources is None:
            sources = ["spotify", "deezer", "tidal"]

        sources_str = ",".join(sources) if isinstance(sources, (list, tuple)) else sources

        try:
            params = {
                "songstats_track_id": songstats_track_id.strip(),
                "start_date": start_date,
                "source": sources_str,
            }
            response = self.get(SONGSTATS_ENDPOINTS["historic"], params=params)

            # Calculate peaks from historical data
            peaks = self._calculate_peaks(response.get("stats", []))
            self.logger.debug("Calculated %d peak values", len(peaks))
            return peaks

        except (requests.HTTPError, KeyError) as e:
            self.logger.error(
                "Failed to retrieve historical data for track %s: %s",
                songstats_track_id,
                e,
            )
            return {}

    # =========================================================================
    # YouTube-specific endpoints
    # =========================================================================

    def get_youtube_videos(
            self,
            songstats_track_id: str,
    ) -> dict[str, Any]:
        """Fetch YouTube video data for a track.

        Args:
            songstats_track_id: Songstats track identifier.

        Returns:
            Dictionary with YouTube video information:
            - most_viewed: Most viewed video (prefers non-Topic, falls back to Topic)
            - most_viewed_is_topic: True if overall most viewed video is from a Topic channel
            - all_sources: List of all videos with full metadata (including Topic channels)

        Notes:
            - Topic channels are auto-generated channels (ending with ' - Topic')
            - most_viewed prefers non-Topic videos but falls back to Topic if none exist
            - Returns empty dict if no videos found
        """
        if not songstats_track_id or not songstats_track_id.strip():
            self.logger.error("Songstats track ID is required")
            return {}

        try:
            params = {
                "songstats_track_id": songstats_track_id.strip(),
                "with_videos": "true",
                "source": "youtube",
            }
            response = self.get(SONGSTATS_ENDPOINTS["stats"], params=params)

            # Extract video data from nested structure
            videos = self._extract_youtube_videos(response)
            self.logger.debug("Found %d YouTube videos", len(videos.get("all_sources", [])))
            return videos

        except (requests.HTTPError, KeyError, IndexError) as e:
            self.logger.error(
                "Failed to retrieve YouTube videos for track %s: %s",
                songstats_track_id,
                e,
            )
            return {}

    def get_track_info(
            self,
            songstats_track_id: str,
            with_videos: bool = False,
    ) -> dict[str, Any]:
        """Fetch track source information and links.

        Args:
            songstats_track_id: Songstats track identifier.
            with_videos: Include YouTube video data.

        Returns:
            Dictionary with track info:
            - track_info: Metadata and platform links
            - links: List of platform URLs
            - videos: YouTube videos (if with_videos=True)
        """
        if not songstats_track_id or not songstats_track_id.strip():
            self.logger.error("Songstats track ID is required")
            return {}

        try:
            params = {
                "songstats_track_id": songstats_track_id.strip(),
            }

            if with_videos:
                params["with_videos"] = "true"
                params["source"] = "youtube"

            response = self.get(SONGSTATS_ENDPOINTS["info"], params=params)
            self.logger.debug("Retrieved track info for %s", songstats_track_id)
            return response

        except requests.HTTPError as e:
            self.logger.error(
                "Failed to retrieve track info for %s: %s",
                songstats_track_id,
                e,
            )
            return {}

    def get_available_platforms(self, songstats_track_id: str) -> set[str]:
        """Get list of platforms where track is available.

        Args:
            songstats_track_id: Songstats track identifier.

        Returns:
            Set of platform names where track exists (e.g., {'spotify', 'youtube', 'tracklist'})

        Examples:
            >>> client.get_available_platforms("2kuc1bpm")
            {'tracklist'}
        """
        track_info = self.get_track_info(songstats_track_id)

        if not track_info:
            return set()

        # Extract platform sources from links array
        links = track_info.get("track_info", {}).get("links", [])
        platforms = {link.get("source") for link in links if link.get("source")}

        # Normalize platform names to match model field names
        platform_name_map = {
            "tracklist": "1001tracklists",
            "amazon": "amazon_music",
        }

        normalized = {platform_name_map.get(platform, platform) for platform in platforms}

        self.logger.debug(
            "Track %s available on platforms: %s",
            songstats_track_id,
            ", ".join(sorted(normalized))
        )

        return normalized

    # =========================================================================
    # Data modification endpoints (POST)
    # =========================================================================

    def add_artist_link(
            self,
            link: str,
            apple_music_artist_id: int | None = None,
            songstats_artist_id: str | None = None,
            spotify_artist_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a link to an artist profile.

        Args:
            link: URL to be added to the artist profile.
            apple_music_artist_id: Apple Music artist ID (one of the IDs required).
            songstats_artist_id: Songstats artist ID (one of the IDs required).
            spotify_artist_id: Spotify artist ID (one of the IDs required).

        Returns:
            Dictionary with request status and details.

        Notes:
            - At least one artist ID must be provided
            - Link should be a valid URL (e.g., SoundCloud, website)

        Example:
            >>> client.add_artist_link(
            ...     link="https://soundcloud.com/artist",
            ...     spotify_artist_id="28j8lBWDdDSHSSt5oPlsX2"
            ... )
        """
        if not link or not link.strip():
            self.logger.error("Link is required")
            return {}

        if not any([apple_music_artist_id, songstats_artist_id, spotify_artist_id]):
            self.logger.error("At least one artist ID must be provided")
            return {}

        try:
            data = self._build_request_data(
                link=link,
                apple_music_artist_id=apple_music_artist_id,
                songstats_artist_id=songstats_artist_id,
                spotify_artist_id=spotify_artist_id,
            )

            response = self.post(SONGSTATS_ENDPOINTS["artist_link"], json_data=data)
            self.logger.debug("Artist link added successfully")
            return response

        except requests.HTTPError as e:
            self.logger.error("Failed to add artist link: %s", e)
            return {}

    def add_artist_track(
            self,
            apple_music_artist_id: int | None = None,
            songstats_artist_id: str | None = None,
            spotify_artist_id: str | None = None,
            isrc: str | None = None,
            link: str | None = None,
            spotify_track_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a track to an artist's profile.

        Args:
            apple_music_artist_id: Apple Music artist ID (one required).
            songstats_artist_id: Songstats artist ID (one required).
            spotify_artist_id: Spotify artist ID (one required).
            isrc: Track ISRC code (one of track identifiers required).
            link: Track URL from supported platforms (one of track identifiers required).
            spotify_track_id: Spotify track ID (one of track identifiers required).

        Returns:
            Dictionary with request status and details.

        Notes:
            - At least one artist ID must be provided
            - At least one track identifier (ISRC, link, or Spotify ID) must be provided
            - Supported link platforms: Spotify, Apple Music, Amazon, Deezer,
              1001Tracklists, Beatport, Traxsource, TIDAL

        Example:
            >>> client.add_artist_track(
            ...     spotify_artist_id="28j8lBWDdDSHSSt5oPlsX2",
            ...     spotify_track_id="3yYqfGNpGlIyZJvWEcXgnF"
            ... )
        """
        if not any([apple_music_artist_id, songstats_artist_id, spotify_artist_id]):
            self.logger.error("At least one artist ID must be provided")
            return {}

        if not any([isrc, link, spotify_track_id]):
            self.logger.error("At least one track identifier must be provided")
            return {}

        try:
            data = self._build_request_data(
                apple_music_artist_id=apple_music_artist_id,
                songstats_artist_id=songstats_artist_id,
                spotify_artist_id=spotify_artist_id,
                isrc=isrc,
                link=link,
                spotify_track_id=spotify_track_id,
            )

            response = self.post(SONGSTATS_ENDPOINTS["artist_track"], json_data=data)
            self.logger.debug("Artist track added successfully")
            return response

        except requests.HTTPError as e:
            self.logger.error("Failed to add artist track: %s", e)
            return {}

    def add_track_link(
            self,
            link: str,
            apple_music_track_id: int | None = None,
            isrc: str | None = None,
            spotify_track_id: str | None = None,
            songstats_track_id: str | None = None,
    ) -> dict[str, Any]:
        """Add a link to a track.

        Args:
            link: URL to be added to the track.
            apple_music_track_id: Apple Music track ID (one required).
            isrc: Track ISRC code (one required).
            spotify_track_id: Spotify track ID (one required).
            songstats_track_id: Songstats track ID (one required).

        Returns:
            Dictionary with request status and details.

        Notes:
            - At least one track ID must be provided
            - Link should be a valid URL (e.g., SoundCloud, website)

        Example:
            >>> client.add_track_link(
            ...     link="https://soundcloud.com/track",
            ...     spotify_track_id="1YLGtZjDKyY0Qkv4QlX31b"
            ... )
        """
        if not link or not link.strip():
            self.logger.error("Link is required")
            return {}

        if not any([apple_music_track_id, isrc, spotify_track_id, songstats_track_id]):
            self.logger.error("At least one track ID must be provided")
            return {}

        try:
            data = self._build_request_data(
                link=link,
                apple_music_track_id=apple_music_track_id,
                isrc=isrc,
                spotify_track_id=spotify_track_id,
                songstats_track_id=songstats_track_id,
            )

            response = self.post(SONGSTATS_ENDPOINTS["track_link"], json_data=data)
            self.logger.debug("Track link added successfully")
            return response

        except requests.HTTPError as e:
            self.logger.error("Failed to add track link: %s", e)
            return {}

    # =========================================================================
    # Helper methods (internal)
    # =========================================================================

    @staticmethod
    def _build_request_data(**kwargs: Any) -> dict[str, Any]:
        """Build request data dictionary by filtering None values and stripping strings.

        Args:
            **kwargs: Key-value pairs to include in the request.

        Returns:
            Dictionary with non-None values, with strings stripped.

        Example:
            >>> _build_request_data(
            ...     link="  https://example.com  ",
            ...     artist_id=None,
            ...     track_id="abc123  "
            ... )
            {'link': 'https://example.com', 'track_id': 'abc123'}
        """
        return {
            key: value.strip() if isinstance(value, str) else value
            for key, value in kwargs.items()
            if value is not None
        }

    @staticmethod
    def _flatten_stats(stats_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Flatten nested platform statistics into a single dict.

        Args:
            stats_list: List of platform stats from API response.

        Returns:
            Flattened dictionary with {platform}_{metric}: value format.

        Notes:
            - Maps 'tracklist' → '1001tracklists' for consistency
        """
        flattened_dicts = []

        for stats in stats_list:
            source = stats.get("source", "unknown")
            data = stats.get("data", {})

            # Platform name mapping (legacy pattern)
            if source == "tracklist":
                source = "1001tracklists"

            # Create prefixed keys
            prefixed = {f"{source}_{key}": value for key, value in data.items()}
            flattened_dicts.append(prefixed)

        # Merge all dicts (ChainMap pattern from legacy code)
        return dict(ChainMap(*flattened_dicts))

    @staticmethod
    def _calculate_peaks(stats_list: list[dict[str, Any]]) -> dict[str, int]:
        """Calculate peak popularity from historical data.

        Args:
            stats_list: List of historical stats from API response.

        Returns:
            Dictionary with {platform}_popularity_peak: max_value.
        """
        peaks = {}

        for history in stats_list:
            source = history.get("source", "unknown")
            history_data = history.get("data", {}).get("history", [])

            # Extract all popularity values
            popularity_values = [
                item.get("popularity_current", 0)
                for item in history_data
            ]

            # Calculate max (0 if empty)
            peak_value = max(popularity_values) if popularity_values else 0
            peaks[f"{source}_popularity_peak"] = peak_value

        return peaks

    def _extract_youtube_videos(
            self,
            response: dict[str, Any],
    ) -> dict[str, Any]:
        """Extract YouTube video data from API response.

        Args:
            response: Raw API response with video data.

        Returns:
            Dictionary with keys:
            - most_viewed: Most viewed video (prefers non-Topic, falls back to Topic)
            - most_viewed_is_topic: True if overall most viewed is from Topic channel
            - all_sources: All videos with full metadata (including Topic channels)
        """
        try:
            videos = response["stats"][0]["data"]["videos"]

            # Build video list with metadata
            video_list = [
                {
                    "ytb_id": item["external_id"],
                    "views": item["view_count"],
                    "channel_name": item["youtube_channel_name"],
                }
                for item in videos
            ]

            # Find most viewed non-Topic video, fall back to Topic video if none
            non_topic_videos = [
                vid for vid in video_list
                if " - Topic" not in vid["channel_name"]
            ]

            if non_topic_videos:
                most_viewed = non_topic_videos[0]

            elif video_list:
                # Fallback to most viewed Topic video if no non-Topic videos exist
                most_viewed = video_list[0]

            else:
                most_viewed = {}

            # Check if overall most viewed video is from a Topic channel
            most_viewed_is_topic = (
                " - Topic" in video_list[0]["channel_name"]
                if video_list else False
            )

            return {
                "most_viewed": most_viewed,
                "most_viewed_is_topic": most_viewed_is_topic,
                "all_sources": video_list,
            }

        except (KeyError, IndexError) as e:
            self.logger.error("Failed to parse YouTube video data: %s", e)
            return {"most_viewed": {}, "most_viewed_is_topic": False, "all_sources": []}
