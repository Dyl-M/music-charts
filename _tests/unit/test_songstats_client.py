"""Unit tests for SongstatsClient."""

# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import requests

# Local
from msc.clients.songstats import SongstatsClient
from msc.config.constants import SONGSTATS_ENDPOINTS


class TestSongstatsClientInit:
    """Tests for SongstatsClient initialization."""

    @staticmethod
    def test_init_with_explicit_api_key() -> None:
        """Should initialize with provided API key."""
        client = SongstatsClient(api_key="test_key")
        assert client.api_key == "test_key"

    @staticmethod
    @patch("msc.clients.songstats.get_settings")
    def test_init_loads_api_key_from_settings(mock_settings: MagicMock) -> None:
        """Should load API key from settings when not provided."""
        mock_settings.return_value.get_songstats_key.return_value = "settings_key"
        mock_settings.return_value.songstats_rate_limit = 10

        client = SongstatsClient()
        assert client.api_key == "settings_key"

    @staticmethod
    @patch("msc.clients.songstats.get_settings")
    def test_init_uses_rate_limit_from_settings(mock_settings: MagicMock) -> None:
        """Should use rate limit from settings when not provided."""
        mock_settings.return_value.get_songstats_key.return_value = "key"
        mock_settings.return_value.songstats_rate_limit = 15

        client = SongstatsClient()
        assert client.rate_limiter.requests_per_second == 15

    @staticmethod
    def test_init_with_explicit_rate_limit() -> None:
        """Should use explicit rate_limit when provided."""
        client = SongstatsClient(api_key="test", rate_limit=25)
        assert client.rate_limiter.requests_per_second == 25


class TestHealthCheck:
    """Tests for health_check method."""

    @staticmethod
    @patch.object(SongstatsClient, "get_quota")
    def test_health_check_success(mock_quota: MagicMock) -> None:
        """Should return True when API is accessible."""
        mock_quota.return_value = {"requests_used": 100}

        client = SongstatsClient(api_key="test")
        assert client.health_check() is True

    @staticmethod
    @patch.object(SongstatsClient, "get_quota")
    def test_health_check_failure(mock_quota: MagicMock) -> None:
        """Should return False when API is unreachable."""
        mock_quota.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        assert client.health_check() is False


class TestGetQuota:
    """Tests for get_quota method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_quota_success(mock_get: MagicMock) -> None:
        """Should return quota information."""
        mock_get.return_value = {
            "requests_used": 1500,
            "requests_limit": 10000,
        }

        client = SongstatsClient(api_key="test")
        result = client.get_quota()

        assert result["requests_used"] == 1500
        mock_get.assert_called_once_with(SONGSTATS_ENDPOINTS["status"])

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_quota_api_failure(mock_get: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.get_quota()

        assert result == {}


class TestSearchTrack:
    """Tests for search_track method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_search_track_success(mock_get: MagicMock) -> None:
        """Should return search results."""
        mock_get.return_value = {
            "results": [
                {"songstats_track_id": "abc123", "title": "Test Track"}
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.search_track("artist - track", limit=1)

        assert len(result) == 1
        assert result[0]["songstats_track_id"] == "abc123"

    @staticmethod
    def test_search_track_empty_query() -> None:
        """Should return empty list for empty query."""
        client = SongstatsClient(api_key="test")
        result = client.search_track("")

        assert result == []

    @staticmethod
    def test_search_track_whitespace_query() -> None:
        """Should return empty list for whitespace-only query."""
        client = SongstatsClient(api_key="test")
        result = client.search_track("   ")

        assert result == []

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_search_track_api_failure(mock_get: MagicMock) -> None:
        """Should return empty list on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.search_track("artist - track")

        assert result == []

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_search_track_no_results(mock_get: MagicMock) -> None:
        """Should return empty list when no results found."""
        mock_get.return_value = {"results": []}

        client = SongstatsClient(api_key="test")
        result = client.search_track("nonexistent track")

        assert result == []


class TestGetPlatformStats:
    """Tests for get_platform_stats method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_success(mock_get: MagicMock) -> None:
        """Should return flattened statistics."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "spotify",
                    "data": {"streams": 1000000, "playlist_reach": 500000}
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("abc123")

        assert result["spotify_streams"] == 1000000
        assert result["spotify_playlist_reach"] == 500000

    @staticmethod
    def test_get_platform_stats_missing_id() -> None:
        """Should return empty dict for missing track ID."""
        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("")

        assert result == {}

    @staticmethod
    def test_get_platform_stats_whitespace_id() -> None:
        """Should return empty dict for whitespace-only track ID."""
        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("   ")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_maps_tracklist(mock_get: MagicMock) -> None:
        """Should map tracklist to 1001tracklists."""
        mock_get.return_value = {
            "stats": [
                {"source": "tracklist", "data": {"chart_peak": 5}}
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("abc123")

        assert "1001tracklists_chart_peak" in result
        assert result["1001tracklists_chart_peak"] == 5

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_multiple_platforms(mock_get: MagicMock) -> None:
        """Should flatten stats from multiple platforms."""
        mock_get.return_value = {
            "stats": [
                {"source": "spotify", "data": {"streams": 1000}},
                {"source": "deezer", "data": {"fans": 200}},
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("abc123")

        assert result["spotify_streams"] == 1000
        assert result["deezer_fans"] == 200

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_api_failure(mock_get: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.get_platform_stats("abc123")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_with_list_sources(mock_get: MagicMock) -> None:
        """Should accept sources as list."""
        mock_get.return_value = {"stats": []}

        client = SongstatsClient(api_key="test")
        client.get_platform_stats("abc123", sources=["spotify", "deezer"])

        call_args = mock_get.call_args
        assert call_args[1]["params"]["source"] == "spotify,deezer"

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_platform_stats_with_string_sources(mock_get: MagicMock) -> None:
        """Should accept sources as comma-separated string."""
        mock_get.return_value = {"stats": []}

        client = SongstatsClient(api_key="test")
        client.get_platform_stats("abc123", sources="spotify,deezer")

        call_args = mock_get.call_args
        assert call_args[1]["params"]["source"] == "spotify,deezer"


class TestGetHistoricalPeaks:
    """Tests for get_historical_peaks method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_historical_peaks_success(mock_get: MagicMock) -> None:
        """Should return peak popularity values."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "spotify",
                    "data": {
                        "history": [
                            {"popularity_current": 80},
                            {"popularity_current": 95},
                            {"popularity_current": 85},
                        ]
                    }
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_historical_peaks("abc123", "2024-01-01")

        assert result["spotify_popularity_peak"] == 95

    @staticmethod
    def test_get_historical_peaks_missing_id() -> None:
        """Should return empty dict for missing track ID."""
        client = SongstatsClient(api_key="test")
        result = client.get_historical_peaks("", "2024-01-01")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_historical_peaks_multiple_platforms(mock_get: MagicMock) -> None:
        """Should calculate peaks for multiple platforms."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "spotify",
                    "data": {
                        "history": [
                            {"popularity_current": 90},
                            {"popularity_current": 95},
                        ]
                    }
                },
                {
                    "source": "deezer",
                    "data": {
                        "history": [
                            {"popularity_current": 70},
                            {"popularity_current": 85},
                        ]
                    }
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_historical_peaks("abc123", "2024-01-01")

        assert result["spotify_popularity_peak"] == 95
        assert result["deezer_popularity_peak"] == 85

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_historical_peaks_api_failure(mock_get: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.get_historical_peaks("abc123", "2024-01-01")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_historical_peaks_default_sources(mock_get: MagicMock) -> None:
        """Should use default sources when not provided."""
        mock_get.return_value = {"stats": []}

        client = SongstatsClient(api_key="test")
        client.get_historical_peaks("abc123", "2024-01-01")

        # Verify it uses default sources: spotify, deezer, tidal
        call_args = mock_get.call_args
        assert call_args[1]["params"]["source"] == "spotify,deezer,tidal"

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_historical_peaks_with_explicit_sources(mock_get: MagicMock) -> None:
        """Should use explicit sources when provided."""
        mock_get.return_value = {"stats": []}

        client = SongstatsClient(api_key="test")
        client.get_historical_peaks("abc123", "2024-01-01", sources=["apple_music", "youtube"])

        # Verify it uses the provided sources
        call_args = mock_get.call_args
        assert call_args[1]["params"]["source"] == "apple_music,youtube"


class TestGetYouTubeVideos:
    """Tests for get_youtube_videos method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_youtube_videos_success(mock_get: MagicMock) -> None:
        """Should return YouTube video data."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "youtube",
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid123",
                                "view_count": 1000000,
                                "youtube_channel_name": "Artist Channel"
                            },
                            {
                                "external_id": "vid456",
                                "view_count": 500000,
                                "youtube_channel_name": "Artist - Topic"
                            }
                        ]
                    }
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_youtube_videos("abc123")

        assert result["most_viewed"]["ytb_id"] == "vid123"
        assert result["most_viewed_is_topic"] is False
        assert len(result["all_sources"]) == 2
        assert result["all_sources"][0]["ytb_id"] == "vid123"
        assert result["all_sources"][1]["ytb_id"] == "vid456"

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_youtube_videos_filters_topic_channels(mock_get: MagicMock) -> None:
        """Should filter out Topic channels for most_viewed."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "youtube",
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid1",
                                "view_count": 2000000,
                                "youtube_channel_name": "Artist - Topic"
                            },
                            {
                                "external_id": "vid2",
                                "view_count": 1000000,
                                "youtube_channel_name": "Real Channel"
                            }
                        ]
                    }
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_youtube_videos("abc123")

        # Should pick vid2 even though vid1 has more views
        assert result["most_viewed"]["ytb_id"] == "vid2"
        assert result["most_viewed_is_topic"] is True  # Overall most viewed is Topic

    @staticmethod
    def test_get_youtube_videos_missing_id() -> None:
        """Should return empty dict for missing track ID."""
        client = SongstatsClient(api_key="test")
        result = client.get_youtube_videos("")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_youtube_videos_no_non_topic_videos(mock_get: MagicMock) -> None:
        """Should return empty most_viewed when only Topic channels exist."""
        mock_get.return_value = {
            "stats": [
                {
                    "source": "youtube",
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid1",
                                "view_count": 2000000,
                                "youtube_channel_name": "Artist - Topic"
                            }
                        ]
                    }
                }
            ]
        }

        client = SongstatsClient(api_key="test")
        result = client.get_youtube_videos("abc123")

        assert result["most_viewed"] == {}
        assert result["most_viewed_is_topic"] is True  # Only Topic video available
        assert len(result["all_sources"]) == 1
        assert result["all_sources"][0]["channel_name"] == "Artist - Topic"

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_youtube_videos_api_failure(mock_get: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.get_youtube_videos("abc123")

        assert result == {}


class TestGetTrackInfo:
    """Tests for get_track_info method."""

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_track_info_success(mock_get: MagicMock) -> None:
        """Should return track information."""
        mock_get.return_value = {
            "track_info": {
                "links": [
                    {"source": "spotify", "url": "https://..."}
                ]
            }
        }

        client = SongstatsClient(api_key="test")
        result = client.get_track_info("abc123")

        assert "track_info" in result

    @staticmethod
    def test_get_track_info_missing_id() -> None:
        """Should return empty dict for missing track ID."""
        client = SongstatsClient(api_key="test")
        result = client.get_track_info("")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_track_info_with_videos(mock_get: MagicMock) -> None:
        """Should include videos when requested."""
        mock_get.return_value = {"track_info": {}}

        client = SongstatsClient(api_key="test")
        client.get_track_info("abc123", with_videos=True)

        call_args = mock_get.call_args
        params = call_args[1]["params"]

        assert params["with_videos"] == "true"
        assert params["source"] == "youtube"

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_track_info_without_videos(mock_get: MagicMock) -> None:
        """Should not include video params when with_videos=False."""
        mock_get.return_value = {"track_info": {}}

        client = SongstatsClient(api_key="test")
        client.get_track_info("abc123", with_videos=False)

        call_args = mock_get.call_args
        params = call_args[1]["params"]

        assert "with_videos" not in params
        assert "source" not in params

    @staticmethod
    @patch.object(SongstatsClient, "get")
    def test_get_track_info_api_failure(mock_get: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_get.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.get_track_info("abc123")

        assert result == {}


class TestAddArtistLink:
    """Tests for add_artist_link method."""

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_link_success(mock_post: MagicMock) -> None:
        """Should add artist link successfully."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(
            link="https://example.com",
            songstats_artist_id="artist123"
        )

        assert result["success"] is True
        mock_post.assert_called_once()

    @staticmethod
    def test_add_artist_link_missing_link() -> None:
        """Should return empty dict for missing link."""
        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(link="")

        assert result == {}

    @staticmethod
    def test_add_artist_link_whitespace_link() -> None:
        """Should return empty dict for whitespace-only link."""
        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(link="   ")

        assert result == {}

    @staticmethod
    def test_add_artist_link_missing_artist_id() -> None:
        """Should return empty dict when no artist ID provided."""
        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(link="https://example.com")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_link_with_apple_music_id(mock_post: MagicMock) -> None:
        """Should work with Apple Music artist ID."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(
            link="https://example.com",
            apple_music_artist_id=12345
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["apple_music_artist_id"] == 12345

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_link_with_spotify_id(mock_post: MagicMock) -> None:
        """Should work with Spotify artist ID."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(
            link="https://example.com",
            spotify_artist_id="spotify123"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["spotify_artist_id"] == "spotify123"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_link_trims_whitespace(mock_post: MagicMock) -> None:
        """Should trim whitespace from link."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        client.add_artist_link(
            link="  https://example.com  ",
            songstats_artist_id="artist123"
        )

        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["link"] == "https://example.com"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_link_api_failure(mock_post: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_post.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.add_artist_link(
            link="https://example.com",
            songstats_artist_id="artist123"
        )

        assert result == {}


class TestAddArtistTrack:
    """Tests for add_artist_track method."""

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_track_success(mock_post: MagicMock) -> None:
        """Should add artist track successfully."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(
            songstats_artist_id="artist123",
            isrc="USRC17607839"
        )

        assert result["success"] is True
        mock_post.assert_called_once()

    @staticmethod
    def test_add_artist_track_missing_artist_id() -> None:
        """Should return empty dict when no artist ID provided."""
        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(isrc="USRC17607839")

        assert result == {}

    @staticmethod
    def test_add_artist_track_missing_track_identifier() -> None:
        """Should return empty dict when no track identifier provided."""
        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(songstats_artist_id="artist123")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_track_with_link(mock_post: MagicMock) -> None:
        """Should work with link as track identifier."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(
            spotify_artist_id="spotify123",
            link="https://example.com"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["link"] == "https://example.com"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_track_with_spotify_track_id(mock_post: MagicMock) -> None:
        """Should work with Spotify track ID."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(
            apple_music_artist_id=12345,
            spotify_track_id="track123"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["spotify_track_id"] == "track123"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_track_trims_whitespace(mock_post: MagicMock) -> None:
        """Should trim whitespace from string parameters."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        client.add_artist_track(
            songstats_artist_id="  artist123  ",
            isrc="  USRC17607839  "
        )

        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["songstats_artist_id"] == "artist123"
        assert call_args[1]["json_data"]["isrc"] == "USRC17607839"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_artist_track_api_failure(mock_post: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_post.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.add_artist_track(
            songstats_artist_id="artist123",
            isrc="USRC17607839"
        )

        assert result == {}


class TestAddTrackLink:
    """Tests for add_track_link method."""

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_success(mock_post: MagicMock) -> None:
        """Should add track link successfully."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_track_link(
            link="https://example.com",
            songstats_track_id="track123"
        )

        assert result["success"] is True
        mock_post.assert_called_once()

    @staticmethod
    def test_add_track_link_missing_link() -> None:
        """Should return empty dict for missing link."""
        client = SongstatsClient(api_key="test")
        result = client.add_track_link(link="")

        assert result == {}

    @staticmethod
    def test_add_track_link_whitespace_link() -> None:
        """Should return empty dict for whitespace-only link."""
        client = SongstatsClient(api_key="test")
        result = client.add_track_link(link="   ")

        assert result == {}

    @staticmethod
    def test_add_track_link_missing_track_id() -> None:
        """Should return empty dict when no track ID provided."""
        client = SongstatsClient(api_key="test")
        result = client.add_track_link(link="https://example.com")

        assert result == {}

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_with_apple_music_id(mock_post: MagicMock) -> None:
        """Should work with Apple Music track ID."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_track_link(
            link="https://example.com",
            apple_music_track_id=12345
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["apple_music_track_id"] == 12345

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_with_isrc(mock_post: MagicMock) -> None:
        """Should work with ISRC."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_track_link(
            link="https://example.com",
            isrc="USRC17607839"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["isrc"] == "USRC17607839"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_with_spotify_id(mock_post: MagicMock) -> None:
        """Should work with Spotify track ID."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        result = client.add_track_link(
            link="https://example.com",
            spotify_track_id="spotify123"
        )

        assert result["success"] is True
        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["spotify_track_id"] == "spotify123"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_trims_whitespace(mock_post: MagicMock) -> None:
        """Should trim whitespace from link and string IDs."""
        mock_post.return_value = {"success": True}

        client = SongstatsClient(api_key="test")
        client.add_track_link(
            link="  https://example.com  ",
            songstats_track_id="  track123  "
        )

        call_args = mock_post.call_args
        assert call_args[1]["json_data"]["link"] == "https://example.com"
        assert call_args[1]["json_data"]["songstats_track_id"] == "track123"

    @staticmethod
    @patch.object(SongstatsClient, "post")
    def test_add_track_link_api_failure(mock_post: MagicMock) -> None:
        """Should return empty dict on API failure."""
        mock_post.side_effect = requests.HTTPError()

        client = SongstatsClient(api_key="test")
        result = client.add_track_link(
            link="https://example.com",
            songstats_track_id="track123"
        )

        assert result == {}


class TestHelperMethods:
    """Tests for internal helper methods."""

    @staticmethod
    def test_build_request_data_filters_none_values() -> None:
        """Should filter out None values."""
        result = SongstatsClient._build_request_data(
            link="https://example.com",
            artist_id=None,
            track_id="abc123"
        )

        assert result == {"link": "https://example.com", "track_id": "abc123"}
        assert "artist_id" not in result

    @staticmethod
    def test_build_request_data_strips_strings() -> None:
        """Should strip whitespace from string values."""
        result = SongstatsClient._build_request_data(
            link="  https://example.com  ",
            track_id="  abc123  "
        )

        assert result == {"link": "https://example.com", "track_id": "abc123"}

    @staticmethod
    def test_build_request_data_preserves_integers() -> None:
        """Should preserve integer values without conversion."""
        result = SongstatsClient._build_request_data(
            link="https://example.com",
            apple_music_artist_id=12345,
            artist_id="abc"
        )

        assert result["apple_music_artist_id"] == 12345
        assert isinstance(result["apple_music_artist_id"], int)

    @staticmethod
    def test_build_request_data_empty_kwargs() -> None:
        """Should return empty dict for no arguments."""
        result = SongstatsClient._build_request_data()
        assert result == {}

    @staticmethod
    def test_build_request_data_all_none() -> None:
        """Should return empty dict when all values are None."""
        result = SongstatsClient._build_request_data(
            artist_id=None,
            track_id=None
        )
        assert result == {}

    @staticmethod
    def test_flatten_stats() -> None:
        """Should flatten nested stats structure."""
        client = SongstatsClient(api_key="test")

        stats_list = [
            {"source": "spotify", "data": {"streams": 1000, "followers": 500}},
            {"source": "deezer", "data": {"fans": 200}},
        ]

        result = client._flatten_stats(stats_list)

        assert result["spotify_streams"] == 1000
        assert result["spotify_followers"] == 500
        assert result["deezer_fans"] == 200

    @staticmethod
    def test_flatten_stats_empty_list() -> None:
        """Should return empty dict for empty list."""
        client = SongstatsClient(api_key="test")

        result = client._flatten_stats([])

        assert result == {}

    @staticmethod
    def test_calculate_peaks() -> None:
        """Should calculate maximum popularity values."""
        client = SongstatsClient(api_key="test")

        stats_list = [
            {
                "source": "spotify",
                "data": {
                    "history": [
                        {"popularity_current": 70},
                        {"popularity_current": 95},
                        {"popularity_current": 80},
                    ]
                }
            }
        ]

        result = client._calculate_peaks(stats_list)

        assert result["spotify_popularity_peak"] == 95

    @staticmethod
    def test_calculate_peaks_empty_history() -> None:
        """Should return 0 for empty history."""
        client = SongstatsClient(api_key="test")

        stats_list = [
            {"source": "spotify", "data": {"history": []}}
        ]

        result = client._calculate_peaks(stats_list)

        assert result["spotify_popularity_peak"] == 0

    @staticmethod
    def test_calculate_peaks_missing_data() -> None:
        """Should handle missing data gracefully."""
        client = SongstatsClient(api_key="test")

        stats_list = [
            {"source": "spotify", "data": {}}
        ]

        result = client._calculate_peaks(stats_list)

        assert result["spotify_popularity_peak"] == 0

    @staticmethod
    def test_extract_youtube_videos() -> None:
        """Should extract video data from response."""
        client = SongstatsClient(api_key="test")

        response = {
            "stats": [
                {
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid1",
                                "view_count": 1000,
                                "youtube_channel_name": "Channel 1"
                            },
                            {
                                "external_id": "vid2",
                                "view_count": 500,
                                "youtube_channel_name": "Channel 2 - Topic"
                            }
                        ]
                    }
                }
            ]
        }

        result = client._extract_youtube_videos(response)

        assert result["most_viewed"]["ytb_id"] == "vid1"
        assert result["most_viewed"]["views"] == 1000
        assert result["most_viewed_is_topic"] is False  # Most viewed is not Topic
        assert len(result["all_sources"]) == 2
        assert result["all_sources"][0]["ytb_id"] == "vid1"
        assert result["all_sources"][1]["ytb_id"] == "vid2"
        assert result["all_sources"][1]["channel_name"] == "Channel 2 - Topic"

    @staticmethod
    def test_extract_youtube_videos_topic_is_most_viewed() -> None:
        """Should set most_viewed_is_topic=True when Topic channel is most viewed."""
        client = SongstatsClient(api_key="test")

        response = {
            "stats": [
                {
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid1",
                                "view_count": 5000000,
                                "youtube_channel_name": "Artist - Topic"
                            },
                            {
                                "external_id": "vid2",
                                "view_count": 1000,
                                "youtube_channel_name": "Regular Channel"
                            }
                        ]
                    }
                }
            ]
        }

        result = client._extract_youtube_videos(response)

        assert result["most_viewed"]["ytb_id"] == "vid2"  # Non-Topic video
        assert result["most_viewed_is_topic"] is True  # Overall most viewed IS Topic
        assert len(result["all_sources"]) == 2

    @staticmethod
    def test_extract_youtube_videos_malformed_response() -> None:
        """Should handle malformed response gracefully."""
        client = SongstatsClient(api_key="test")

        response = {"stats": []}

        result = client._extract_youtube_videos(response)

        assert result == {"most_viewed": {}, "most_viewed_is_topic": False, "all_sources": []}
