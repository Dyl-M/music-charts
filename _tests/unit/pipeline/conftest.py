"""Fixtures for pipeline tests."""

# Standard library
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

# Third-party
import pytest

# Local
from msc.models.track import Track, SongstatsIdentifiers
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.platforms import SpotifyStats, DeezerStats
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.pipeline.observer import EventType, PipelineEvent, PipelineObserver


@pytest.fixture
def sample_track() -> Track:
    """Create a sample track for testing."""
    return Track(
        title="Test Track",
        artist_list=["Test Artist"],
        year=2024,
    )


@pytest.fixture
def sample_track_with_songstats_id() -> Track:
    """Create a sample track with Songstats ID."""
    return Track(
        title="Test Track",
        artist_list=["Test Artist"],
        year=2024,
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test Track",
        ),
    )


@pytest.fixture
def sample_tracks() -> list[Track]:
    """Create sample tracks for testing."""
    return [
        Track(
            title="Track A",
            artist_list=["Artist 1"],
            year=2024,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id1",
                songstats_title="Track A",
            ),
        ),
        Track(
            title="Track B",
            artist_list=["Artist 2"],
            year=2024,
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id2",
                songstats_title="Track B",
            ),
        ),
    ]


@pytest.fixture
def sample_track_with_stats() -> TrackWithStats:
    """Create a sample track with stats for testing."""
    return TrackWithStats(
        track=Track(
            title="Test Track",
            artist_list=["Test Artist"],
            year=2024,
        ),
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="abc123",
            songstats_title="Test Track",
        ),
        platform_stats=PlatformStats(
            spotify=SpotifyStats(streams_total=1000000, popularity_current=80),
        ),
    )


@pytest.fixture
def sample_tracks_with_stats() -> list[TrackWithStats]:
    """Create sample tracks with stats for testing."""
    return [
        TrackWithStats(
            track=Track(title="Track A", artist_list=["Artist 1"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id1", songstats_title="Track A"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=1000000, popularity_current=80),
                deezer=DeezerStats(popularity_peak=75),
            ),
        ),
        TrackWithStats(
            track=Track(title="Track B", artist_list=["Artist 2"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id2", songstats_title="Track B"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=500000, popularity_current=60),
                deezer=DeezerStats(popularity_peak=50),
            ),
        ),
        TrackWithStats(
            track=Track(title="Track C", artist_list=["Artist 3"], year=2024),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="id3", songstats_title="Track C"
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(streams_total=2000000, popularity_current=95),
                deezer=DeezerStats(popularity_peak=90),
            ),
        ),
    ]


@pytest.fixture
def sample_power_ranking_results(
    sample_tracks_with_stats: list[TrackWithStats],
) -> PowerRankingResults:
    """Create sample power ranking results."""
    rankings = []
    for idx, track_with_stats in enumerate(sample_tracks_with_stats):
        ranking = PowerRanking(
            track=track_with_stats.track,
            total_score=100.0 - (idx * 10),
            rank=idx + 1,
            category_scores=[
                CategoryScore(
                    category="streams",
                    raw_score=80.0 - (idx * 5),
                    weight=4.0,
                    weighted_score=320.0 - (idx * 20),
                ),
            ],
        )
        rankings.append(ranking)

    return PowerRankingResults(rankings=rankings, year=2024)


@pytest.fixture
def sample_event() -> PipelineEvent:
    """Create a sample pipeline event."""
    return PipelineEvent(
        event_type=EventType.STAGE_STARTED,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        stage_name="TestStage",
        message="Test message",
    )


@pytest.fixture
def mock_musicbee_client() -> MagicMock:
    """Create a mock MusicBee client."""
    mock = MagicMock()
    mock.find_playlist_by_name.return_value = "12345"
    mock.get_playlist_tracks.return_value = [
        {
            "title": "Test Track",
            "artist_list": ["Test Artist"],
            "year": 2024,
            "genre": "Electronic",
            "grouping": ["Test Label"],
        }
    ]
    return mock


@pytest.fixture
def mock_songstats_client() -> MagicMock:
    """Create a mock Songstats client."""
    mock = MagicMock()
    mock.search_track.return_value = [
        {
            "songstats_track_id": "abc123",
            "title": "Test Track",
            "artists": [{"name": "Test Artist"}],
            "labels": [{"name": "Test Label"}],
        }
    ]
    mock.get_track_info.return_value = {
        "track_info": {
            "links": [{"platform": "spotify", "isrc": "USRC12345678"}]
        }
    }
    mock.get_available_platforms.return_value = {"spotify", "deezer"}
    mock.get_platform_stats.return_value = {
        "spotify_streams_total": 1000000,
        "spotify_popularity_current": 80,
    }
    mock.get_historical_peaks.return_value = {}
    mock.get_youtube_videos.return_value = None
    return mock


@pytest.fixture
def mock_track_repository() -> MagicMock:
    """Create a mock track repository."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.get_all.return_value = []
    return mock


@pytest.fixture
def mock_stats_repository() -> MagicMock:
    """Create a mock stats repository."""
    mock = MagicMock()
    mock.get.return_value = None
    mock.get_all.return_value = []
    return mock


@pytest.fixture
def mock_checkpoint_manager() -> MagicMock:
    """Create a mock checkpoint manager."""
    from msc.storage.checkpoint import CheckpointState

    mock = MagicMock()
    mock.load_checkpoint.return_value = None
    now = datetime.now()
    mock.create_checkpoint.return_value = CheckpointState(
        stage_name="test",
        created_at=now,
        last_updated=now,
        processed_ids=set(),
        failed_ids=set(),
    )
    return mock


@pytest.fixture
def mock_review_queue() -> MagicMock:
    """Create a mock review queue."""
    mock = MagicMock()
    return mock


class MockObserver(PipelineObserver):
    """Mock observer for testing."""

    def __init__(self) -> None:
        """Initialize mock observer."""
        self.events: list[PipelineEvent] = []

    def on_event(self, event: PipelineEvent) -> None:
        """Record event."""
        self.events.append(event)


@pytest.fixture
def mock_observer() -> MockObserver:
    """Create a mock observer."""
    return MockObserver()


@pytest.fixture
def temp_category_config(tmp_path: Path) -> Path:
    """Create temporary category config file."""
    config_path = tmp_path / "categories.json"
    config_path.write_text(
        '{"popularity": ["spotify_popularity_current", "deezer_popularity_peak"],'
        ' "streams": ["spotify_streams_total"]}',
        encoding="utf-8",
    )
    return config_path
