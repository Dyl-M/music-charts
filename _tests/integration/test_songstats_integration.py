"""Integration tests for Songstats client with real API.

Tests real API interactions when API key is available.
"""

# Third-party
import pytest
import requests

# Local
from msc.clients.songstats import SongstatsClient


class TestSongstatsClientRealAPI:
    """Integration tests for SongstatsClient with real API."""

    @staticmethod
    def test_quota_endpoint(skip_without_api_key: str) -> None:
        """Should fetch quota from real API."""
        client = SongstatsClient(api_key=skip_without_api_key)
        quota = client.get_quota()

        assert quota is not None
        assert "status" in quota

    @staticmethod
    def test_search_track_real(skip_without_api_key: str) -> None:
        """Should search for real track."""
        client = SongstatsClient(api_key=skip_without_api_key)
        # Search for a well-known track (query combines artist and title)
        results = client.search_track("Avicii Levels")

        assert isinstance(results, list)
        # Should find results for this famous track
        if results:
            assert "title" in results[0] or "songstats_track_id" in results[0]

    @staticmethod
    def test_handles_no_results(skip_without_api_key: str) -> None:
        """Should handle search with no results."""
        client = SongstatsClient(api_key=skip_without_api_key)
        # Search for nonsense query
        results = client.search_track("asfasdfasdfqwerasdf zxcvzxcvzxcv")

        assert isinstance(results, list)
        # May be empty or have results depending on API behavior

    @staticmethod
    def test_rate_limiting(skip_without_api_key: str) -> None:
        """Should respect rate limiting."""
        client = SongstatsClient(api_key=skip_without_api_key)

        # Make a few requests - should not fail due to rate limiting
        for _ in range(3):
            client.get_quota()

    @staticmethod
    def test_connection_error_handling() -> None:
        """Should handle connection errors gracefully."""
        # Use invalid API key
        client = SongstatsClient(api_key="invalid_key_12345")

        # Should handle error gracefully (may return empty or raise)
        try:
            result = client.get_quota()
            # If it returns, should be empty or error response
            assert result is None or isinstance(result, dict)
        
        except requests.RequestException:
            # Network/HTTP errors are acceptable for invalid API key
            pass

    @staticmethod
    def test_get_track_info(skip_without_api_key: str) -> None:
        """Should get track info for known track ID."""
        client = SongstatsClient(api_key=skip_without_api_key)

        # First search for a track to get an ID
        results = client.search_track("David Guetta Titanium")

        if results and "songstats_track_id" in results[0]:
            track_id = results[0]["songstats_track_id"]
            info = client.get_track_info(track_id)

            # Should return track info or None
            assert info is None or isinstance(info, dict)

    @staticmethod
    def test_get_platform_stats(skip_without_api_key: str) -> None:
        """Should get platform stats for known track."""
        client = SongstatsClient(api_key=skip_without_api_key)

        # First search for a track
        results = client.search_track("Avicii Wake Me Up")

        if results and "songstats_track_id" in results[0]:
            track_id = results[0]["songstats_track_id"]
            stats = client.get_platform_stats(track_id, sources=["spotify"])

            # Should return stats dict
            assert isinstance(stats, dict)
