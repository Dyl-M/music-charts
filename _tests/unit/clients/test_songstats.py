"""Unit tests for Songstats client module.

Tests SongstatsClient API functionality with mocked responses.
"""

# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import pytest
import requests

# Local
from msc.clients.songstats import SongstatsClient


@pytest.fixture
def mock_settings():
    """Mock settings with API key."""
    with patch("msc.clients.songstats.get_settings") as mock:
        settings = MagicMock()
        settings.get_songstats_key.return_value = "test_api_key"
        settings.songstats_rate_limit = 10
        mock.return_value = settings
        yield settings


@pytest.fixture
def client(mock_settings):
    """Create a SongstatsClient with mocked settings."""
    return SongstatsClient()


class TestSongstatsClientInit:
    """Tests for SongstatsClient initialization."""

    @staticmethod
    def test_uses_settings_api_key(mock_settings) -> None:
        """Should use API key from settings."""
        client = SongstatsClient()
        assert client.api_key == "test_api_key"

    @staticmethod
    def test_uses_provided_api_key(mock_settings) -> None:
        """Should use provided API key over settings."""
        client = SongstatsClient(api_key="custom_key")
        assert client.api_key == "custom_key"

    @staticmethod
    def test_uses_settings_rate_limit(mock_settings) -> None:
        """Should use rate limit from settings."""
        client = SongstatsClient()
        assert client.rate_limiter is not None


class TestSongstatsClientHealthCheck:
    """Tests for SongstatsClient.health_check method."""

    @staticmethod
    def test_returns_true_on_success(client) -> None:
        """Should return True when API responds."""
        with patch.object(client, "get_quota", return_value={"status": "ok"}):
            assert client.health_check() is True

    @staticmethod
    def test_returns_false_on_error(client) -> None:
        """Should return False when API fails."""
        with patch.object(client, "get_quota", side_effect=requests.HTTPError()):
            assert client.health_check() is False


class TestSongstatsClientGetQuota:
    """Tests for SongstatsClient.get_quota method."""

    @staticmethod
    def test_returns_quota_info(client) -> None:
        """Should return quota information."""
        mock_response = {"requests_used": 100, "requests_limit": 10000}
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_quota()
            assert result["requests_used"] == 100
            assert result["requests_limit"] == 10000

    @staticmethod
    def test_returns_empty_on_error(client) -> None:
        """Should return empty dict on error."""
        with patch.object(client, "get", side_effect=requests.HTTPError()):
            result = client.get_quota()
            assert result == {}


class TestSongstatsClientSearchTrack:
    """Tests for SongstatsClient.search_track method."""

    @staticmethod
    def test_returns_results(client) -> None:
        """Should return search results."""
        mock_response = {
            "results": [
                {"songstats_track_id": "abc123", "title": "Test Track"}
            ]
        }
        with patch.object(client, "get", return_value=mock_response):
            results = client.search_track("test query")
            assert len(results) == 1
            assert results[0]["songstats_track_id"] == "abc123"

    @staticmethod
    def test_returns_empty_for_empty_query(client) -> None:
        """Should return empty list for empty query."""
        results = client.search_track("")
        assert results == []

    @staticmethod
    def test_returns_empty_on_error(client) -> None:
        """Should return empty list on HTTP error."""
        with patch.object(client, "get", side_effect=requests.HTTPError()):
            results = client.search_track("test")
            assert results == []

    @staticmethod
    def test_strips_query(client) -> None:
        """Should strip whitespace from query."""
        mock_response = {"results": []}
        with patch.object(client, "get", return_value=mock_response) as mock_get:
            client.search_track("  test query  ")
            call_args = mock_get.call_args
            assert call_args[1]["params"]["q"] == "test query"


class TestSongstatsClientGetPlatformStats:
    """Tests for SongstatsClient.get_platform_stats method."""

    @staticmethod
    def test_returns_flattened_stats(client) -> None:
        """Should return flattened platform stats."""
        mock_response = {
            "stats": [
                {"source": "spotify", "data": {"streams_total": 1000000}}
            ]
        }
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_platform_stats("abc123")
            assert result["spotify_streams_total"] == 1000000

    @staticmethod
    def test_returns_empty_for_missing_id(client) -> None:
        """Should return empty dict for empty track ID."""
        result = client.get_platform_stats("")
        assert result == {}

    @staticmethod
    def test_returns_empty_on_error(client) -> None:
        """Should return empty dict on error."""
        with patch.object(client, "get", side_effect=requests.HTTPError()):
            result = client.get_platform_stats("abc123")
            assert result == {}


class TestSongstatsClientGetHistoricalPeaks:
    """Tests for SongstatsClient.get_historical_peaks method."""

    @staticmethod
    def test_returns_peak_values(client) -> None:
        """Should return calculated peak values."""
        mock_response = {
            "stats": [
                {
                    "source": "spotify",
                    "data": {
                        "history": [
                            {"popularity_current": 75},
                            {"popularity_current": 80},
                            {"popularity_current": 70},
                        ]
                    }
                }
            ]
        }
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_historical_peaks("abc123", "2024-01-01")
            assert result["spotify_popularity_peak"] == 80

    @staticmethod
    def test_returns_empty_for_missing_id(client) -> None:
        """Should return empty dict for empty track ID."""
        result = client.get_historical_peaks("", "2024-01-01")
        assert result == {}


class TestSongstatsClientGetYouTubeVideos:
    """Tests for SongstatsClient.get_youtube_videos method."""

    @staticmethod
    def test_returns_video_data(client) -> None:
        """Should return YouTube video data."""
        mock_response = {
            "stats": [
                {
                    "data": {
                        "videos": [
                            {
                                "external_id": "abc123",
                                "view_count": 1000000,
                                "youtube_channel_name": "Test Channel"
                            }
                        ]
                    }
                }
            ]
        }
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_youtube_videos("track123")
            assert result["most_viewed"]["ytb_id"] == "abc123"
            assert len(result["all_sources"]) == 1

    @staticmethod
    def test_returns_empty_for_missing_id(client) -> None:
        """Should return empty dict for empty track ID."""
        result = client.get_youtube_videos("")
        assert result == {}

    @staticmethod
    def test_prefers_non_topic_channel(client) -> None:
        """Should prefer non-Topic channel for most_viewed."""
        mock_response = {
            "stats": [
                {
                    "data": {
                        "videos": [
                            {
                                "external_id": "topic123",
                                "view_count": 2000000,
                                "youtube_channel_name": "Artist - Topic"
                            },
                            {
                                "external_id": "official123",
                                "view_count": 1000000,
                                "youtube_channel_name": "Official Artist"
                            }
                        ]
                    }
                }
            ]
        }
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_youtube_videos("track123")
            # Should prefer non-Topic even with fewer views
            assert result["most_viewed"]["ytb_id"] == "official123"
            assert result["most_viewed_is_topic"] is True  # Overall most viewed is Topic


class TestSongstatsClientGetAvailablePlatforms:
    """Tests for SongstatsClient.get_available_platforms method."""

    @staticmethod
    def test_returns_platform_set(client) -> None:
        """Should return set of available platforms."""
        mock_response = {
            "track_info": {
                "links": [
                    {"source": "spotify"},
                    {"source": "youtube"},
                    {"source": "deezer"},
                ]
            }
        }
        with patch.object(client, "get_track_info", return_value=mock_response):
            result = client.get_available_platforms("abc123")
            assert "spotify" in result
            assert "youtube" in result
            assert "deezer" in result

    @staticmethod
    def test_normalizes_platform_names(client) -> None:
        """Should normalize platform names."""
        mock_response = {
            "track_info": {
                "links": [
                    {"source": "tracklist"},
                    {"source": "amazon"},
                ]
            }
        }
        with patch.object(client, "get_track_info", return_value=mock_response):
            result = client.get_available_platforms("abc123")
            assert "1001tracklists" in result
            assert "amazon_music" in result


class TestSongstatsClientAddArtistLink:
    """Tests for SongstatsClient.add_artist_link method."""

    @staticmethod
    def test_returns_empty_for_empty_link(client) -> None:
        """Should return empty dict for empty link."""
        result = client.add_artist_link("")
        assert result == {}

    @staticmethod
    def test_requires_artist_id(client) -> None:
        """Should return empty dict if no artist ID provided."""
        result = client.add_artist_link("https://example.com")
        assert result == {}

    @staticmethod
    def test_calls_post_with_data(client) -> None:
        """Should call POST with correct data."""
        with patch.object(client, "post", return_value={"status": "ok"}) as mock_post:
            client.add_artist_link(
                link="https://example.com",
                spotify_artist_id="artist123"
            )
            mock_post.assert_called_once()


class TestSongstatsClientAddArtistTrack:
    """Tests for SongstatsClient.add_artist_track method."""

    @staticmethod
    def test_requires_artist_id(client) -> None:
        """Should return empty dict if no artist ID provided."""
        result = client.add_artist_track(isrc="USRC12345678")
        assert result == {}

    @staticmethod
    def test_requires_track_identifier(client) -> None:
        """Should return empty dict if no track identifier provided."""
        result = client.add_artist_track(spotify_artist_id="artist123")
        assert result == {}

    @staticmethod
    def test_success_returns_response(client) -> None:
        """Should return response on successful add."""
        mock_response = {"status": "success", "track_id": "new123"}
        with patch.object(client, "post", return_value=mock_response):
            result = client.add_artist_track(
                spotify_artist_id="artist123",
                isrc="US1234567890",
            )
            assert result["status"] == "success"

    @staticmethod
    def test_returns_empty_on_http_error(client) -> None:
        """Should return empty dict on HTTP error."""
        with patch.object(client, "post", side_effect=requests.HTTPError("API Error")):
            result = client.add_artist_track(
                spotify_artist_id="artist123",
                isrc="US1234567890",
            )
            assert result == {}


class TestSongstatsClientAddTrackLink:
    """Tests for SongstatsClient.add_track_link method."""

    @staticmethod
    def test_returns_empty_for_empty_link(client) -> None:
        """Should return empty dict for empty link."""
        result = client.add_track_link("")
        assert result == {}

    @staticmethod
    def test_requires_track_id(client) -> None:
        """Should return empty dict if no track ID provided."""
        result = client.add_track_link("https://example.com")
        assert result == {}


class TestSongstatsClientHelpers:
    """Tests for SongstatsClient helper methods."""

    @staticmethod
    def test_build_request_data_filters_none() -> None:
        """Should filter None values from request data."""
        result = SongstatsClient._build_request_data(
            link="https://example.com",
            artist_id=None,
            track_id="abc123"
        )
        assert "link" in result
        assert "track_id" in result
        assert "artist_id" not in result

    @staticmethod
    def test_build_request_data_strips_strings() -> None:
        """Should strip whitespace from string values."""
        result = SongstatsClient._build_request_data(
            link="  https://example.com  ",
            track_id="  abc123  "
        )
        assert result["link"] == "https://example.com"
        assert result["track_id"] == "abc123"

    @staticmethod
    def test_flatten_stats_creates_prefixed_keys() -> None:
        """Should create platform-prefixed keys."""
        stats_list = [
            {"source": "spotify", "data": {"streams_total": 1000}},
            {"source": "deezer", "data": {"popularity": 80}},
        ]
        result = SongstatsClient._flatten_stats(stats_list)
        assert result["spotify_streams_total"] == 1000
        assert result["deezer_popularity"] == 80

    @staticmethod
    def test_flatten_stats_maps_tracklist() -> None:
        """Should map 'tracklist' to '1001tracklists'."""
        stats_list = [{"source": "tracklist", "data": {"unique_support": 50}}]
        result = SongstatsClient._flatten_stats(stats_list)
        assert result["1001tracklists_unique_support"] == 50

    @staticmethod
    def test_calculate_peaks_finds_max() -> None:
        """Should find maximum popularity value."""
        stats_list = [
            {
                "source": "spotify",
                "data": {
                    "history": [
                        {"popularity_current": 50},
                        {"popularity_current": 80},
                        {"popularity_current": 60},
                    ]
                }
            }
        ]
        result = SongstatsClient._calculate_peaks(stats_list)
        assert result["spotify_popularity_peak"] == 80

    @staticmethod
    def test_calculate_peaks_handles_empty() -> None:
        """Should return 0 for empty history."""
        stats_list = [{"source": "spotify", "data": {"history": []}}]
        result = SongstatsClient._calculate_peaks(stats_list)
        assert result["spotify_popularity_peak"] == 0


class TestSongstatsClientHistoricalPeaksExceptions:
    """Tests for get_historical_peaks exception handling."""

    @staticmethod
    def test_returns_empty_on_http_error(client) -> None:
        """Should return empty dict on HTTP error."""
        with patch.object(client, "get", side_effect=requests.HTTPError("API Error")):
            result = client.get_historical_peaks("test_track_id", "2024-01-01")
            assert result == {}

    @staticmethod
    def test_returns_empty_on_key_error(client) -> None:
        """Should return empty dict on KeyError."""
        with patch.object(client, "get", side_effect=KeyError("missing_key")):
            result = client.get_historical_peaks("test_track_id", "2024-01-01")
            assert result == {}


class TestSongstatsClientYouTubeVideosExceptions:
    """Tests for get_youtube_videos exception handling."""

    @staticmethod
    def test_returns_empty_on_http_error(client) -> None:
        """Should return empty dict on HTTP error."""
        with patch.object(client, "get", side_effect=requests.HTTPError("API Error")):
            result = client.get_youtube_videos("test_track_id")
            assert result == {}

    @staticmethod
    def test_returns_empty_on_key_error(client) -> None:
        """Should return empty dict on KeyError."""
        with patch.object(client, "get", side_effect=KeyError("missing_key")):
            result = client.get_youtube_videos("test_track_id")
            assert result == {}

    @staticmethod
    def test_returns_empty_on_index_error(client) -> None:
        """Should return empty dict on IndexError."""
        with patch.object(client, "get", side_effect=IndexError("out of range")):
            result = client.get_youtube_videos("test_track_id")
            assert result == {}


class TestSongstatsClientGetTrackInfo:
    """Tests for get_track_info method."""

    @staticmethod
    def test_returns_empty_on_empty_id(client) -> None:
        """Should return empty dict when track ID is empty."""
        assert client.get_track_info("") == {}
        assert client.get_track_info("   ") == {}

    @staticmethod
    def test_returns_track_info(client) -> None:
        """Should return raw track info response from API."""
        mock_response = {
            "track_info": {"title": "Test Track", "links": []},
        }
        with patch.object(client, "get", return_value=mock_response):
            result = client.get_track_info("abc123")
            assert "track_info" in result
            assert result["track_info"]["title"] == "Test Track"

    @staticmethod
    def test_returns_empty_on_http_error(client) -> None:
        """Should return empty dict on HTTP error."""
        with patch.object(client, "get", side_effect=requests.HTTPError("API Error")):
            result = client.get_track_info("test_track_id")
            assert result == {}

    @staticmethod
    def test_returns_empty_on_key_error(client) -> None:
        """Should return empty dict on KeyError (malformed response)."""
        with patch.object(client, "get", return_value={}):
            result = client.get_track_info("test_track_id")
            assert result == {}


class TestSongstatsClientExtractYouTubeVideos:
    """Tests for _extract_youtube_videos fallback behavior."""

    @staticmethod
    def test_fallback_to_topic_video_when_no_non_topic(client) -> None:
        """Should use Topic video when no non-Topic videos exist."""
        # Response format: stats[0]["data"]["videos"]
        response = {
            "stats": [
                {
                    "source": "youtube",
                    "data": {
                        "videos": [
                            {
                                "external_id": "vid1",
                                "view_count": 1000000,
                                "youtube_channel_name": "Artist - Topic",
                            }
                        ],
                    },
                }
            ]
        }
        result = client._extract_youtube_videos(response)
        assert result["most_viewed"]["ytb_id"] == "vid1"
        assert result["most_viewed_is_topic"] is True

    @staticmethod
    def test_returns_empty_when_no_videos(client) -> None:
        """Should return empty when no videos exist."""
        response = {
            "stats": [
                {
                    "source": "youtube",
                    "data": {
                        "videos": [],
                    },
                }
            ]
        }
        result = client._extract_youtube_videos(response)
        assert result["most_viewed"] == {}
        assert result["most_viewed_is_topic"] is False
        assert result["all_sources"] == []

    @staticmethod
    def test_handles_key_error(client) -> None:
        """Should return empty on malformed data (KeyError)."""
        response = {"stats": [{"source": "youtube", "data": {}}]}
        result = client._extract_youtube_videos(response)
        assert result["most_viewed"] == {}
        assert result["all_sources"] == []

    @staticmethod
    def test_handles_index_error(client) -> None:
        """Should return empty on index error."""
        response = {"stats": []}
        result = client._extract_youtube_videos(response)
        assert result["most_viewed"] == {}
        assert result["all_sources"] == []


class TestSongstatsClientGetTrackMetadata:
    """Tests for get_track_metadata method."""

    @staticmethod
    def test_returns_empty_on_empty_id(client) -> None:
        """Should return empty dict for empty ID."""
        result = client.get_track_metadata("")
        assert result == {}

    @staticmethod
    def test_returns_empty_on_whitespace_id(client) -> None:
        """Should return empty dict for whitespace-only ID."""
        result = client.get_track_metadata("   ")
        assert result == {}

    @staticmethod
    def test_returns_metadata_from_track_info(client) -> None:
        """Should extract metadata from track_info response."""
        with patch.object(client, "get_track_info") as mock_info:
            mock_info.return_value = {
                "track_info": {
                    "title": "Test Track",
                    "artists": [{"name": "Artist 1"}, {"name": "Artist 2"}],
                    "labels": [{"name": "Label 1"}],
                    "links": [{"source": "spotify", "isrc": "USRC12345678"}],
                }
            }
            result = client.get_track_metadata("test_id")

            assert result["title"] == "Test Track"
            assert result["artists"] == ["Artist 1", "Artist 2"]
            assert result["labels"] == ["Label 1"]
            assert result["isrc"] == "USRC12345678"

    @staticmethod
    def test_handles_string_artists(client) -> None:
        """Should handle artist names as strings."""
        with patch.object(client, "get_track_info") as mock_info:
            mock_info.return_value = {
                "track_info": {
                    "title": "Test Track",
                    "artists": ["Artist 1", "Artist 2"],
                    "labels": [],
                    "links": [],
                }
            }
            result = client.get_track_metadata("test_id")
            assert result["artists"] == ["Artist 1", "Artist 2"]

    @staticmethod
    def test_returns_empty_when_track_info_fails(client) -> None:
        """Should return empty dict when get_track_info returns empty."""
        with patch.object(client, "get_track_info") as mock_info:
            mock_info.return_value = {}
            result = client.get_track_metadata("test_id")
            assert result == {}

    @staticmethod
    def test_handles_missing_fields(client) -> None:
        """Should handle missing fields gracefully."""
        with patch.object(client, "get_track_info") as mock_info:
            mock_info.return_value = {"track_info": {}}
            result = client.get_track_metadata("test_id")

            assert result["title"] == ""
            assert result["artists"] == []
            assert result["labels"] == []
            assert result["isrc"] is None

    @staticmethod
    def test_extracts_isrc_from_first_link(client) -> None:
        """Should extract ISRC from first link that has one."""
        with patch.object(client, "get_track_info") as mock_info:
            mock_info.return_value = {
                "track_info": {
                    "links": [
                        {"source": "deezer"},  # No ISRC
                        {"source": "spotify", "isrc": "FIRST_ISRC"},
                        {"source": "apple_music", "isrc": "SECOND_ISRC"},
                    ],
                }
            }
            result = client.get_track_metadata("test_id")
            assert result["isrc"] == "FIRST_ISRC"
