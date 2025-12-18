"""Integration tests for SongstatsClient with real API."""

# Standard library
import os

# Third-party
import pytest

# Local
from msc.clients.songstats import SongstatsClient


# Skip if no API key available (check both env var and file)
pytestmark = pytest.mark.skipif(
    not (os.getenv("MSC_SONGSTATS_API_KEY") or os.path.exists("_tokens/songstats_key.txt")),
    reason="Songstats API key not configured",
)


class TestSongstatsIntegration:
    """Integration tests with real Songstats API."""

    @staticmethod
    def test_health_check_with_real_api() -> None:
        """Should successfully check API health."""
        client = SongstatsClient()
        assert client.health_check() is True

    @staticmethod
    def test_get_quota_with_real_api() -> None:
        """Should retrieve quota information."""
        client = SongstatsClient()
        quota = client.get_quota()

        assert isinstance(quota, dict)
        assert "status" in quota
        assert "current_month_total_requests" in quota["status"]

    @staticmethod
    def test_search_known_track() -> None:
        """Should find a well-known track."""
        client = SongstatsClient()
        results = client.search_track("deadmau5 strobe", limit=1)

        assert len(results) > 0
        assert "songstats_track_id" in results[0]

    @staticmethod
    def test_full_workflow() -> None:
        """Should complete full track lookup workflow."""
        client = SongstatsClient()

        # Step 1: Search
        results = client.search_track("daft punk one more time", limit=1)
        assert len(results) > 0

        track_id = results[0]["songstats_track_id"]

        # Step 2: Get stats
        stats = client.get_platform_stats(track_id)
        assert isinstance(stats, dict)

        # Step 3: Get historical peaks
        peaks = client.get_historical_peaks(track_id, "2024-01-01")
        assert isinstance(peaks, dict)

        # Step 4: Get YouTube videos
        videos = client.get_youtube_videos(track_id)
        assert "all_sources" in videos

        # Step 5: Get track info
        info = client.get_track_info(track_id)
        assert isinstance(info, dict)

    @staticmethod
    def test_context_manager() -> None:
        """Should work as context manager."""
        with SongstatsClient() as client:
            quota = client.get_quota()
            assert isinstance(quota, dict)

        # Session should be closed after context manager exit
        assert client._session is None

    @staticmethod
    def test_search_no_results() -> None:
        """Should return empty list for nonsense query."""
        client = SongstatsClient()
        results = client.search_track("xyzabc123nonexistent999", limit=1)

        assert results == []

    @staticmethod
    def test_invalid_track_id() -> None:
        """Should return empty dict for invalid track ID."""
        client = SongstatsClient()
        stats = client.get_platform_stats("invalid_id_999999")

        assert stats == {}
