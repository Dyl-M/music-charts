"""Tests for power ranking scorer.

Tests PowerRankingScorer algorithm correctness, model schema compliance,
weighting calculations, and edge cases.
"""

# Standard library
import json
from pathlib import Path

# Local
from msc.analysis.normalizers import MinMaxNormalizer, RobustNormalizer
from msc.analysis.scorer import PLATFORM_NAME_MAP, PowerRankingScorer
from msc.models.platforms import SpotifyStats
from msc.models.ranking import CategoryScore, PowerRanking, PowerRankingResults
from msc.models.stats import PlatformStats, TrackWithStats
from msc.models.track import SongstatsIdentifiers, Track


class TestPowerRankingScorer:
    """Tests for PowerRankingScorer."""

    @staticmethod
    def test_init_default_normalizer(tmp_path: Path) -> None:
        """Test scorer initializes with default MinMax normalizer."""
        # Create minimal category config
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        assert scorer.normalizer is not None
        assert isinstance(scorer.normalizer, MinMaxNormalizer)

    @staticmethod
    def test_init_custom_normalizer(tmp_path: Path) -> None:
        """Test scorer initializes with custom normalizer."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        normalizer = RobustNormalizer()
        scorer = PowerRankingScorer(
            category_config_path=config_file, normalizer=normalizer
        )

        assert scorer.normalizer is normalizer

    @staticmethod
    def test_load_category_config(tmp_path: Path) -> None:
        """Test loading category configuration from JSON."""
        config_file = tmp_path / "categories.json"
        config_data = {
            "popularity": ["spotify_popularity_peak", "apple_music_popularity"],
            "streams": ["spotify_streams_total"],
        }

        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        assert "popularity" in scorer.category_config
        assert len(scorer.category_config["popularity"]) == 2

    @staticmethod
    def test_platform_name_mapping() -> None:
        """Test platform name mapping for special cases."""
        assert PLATFORM_NAME_MAP["1001tracklists"] == "tracklists"
        assert PLATFORM_NAME_MAP["amazon"] == "amazon_music"

    @staticmethod
    def test_get_metric_value_spotify(tmp_path: Path) -> None:
        """Test extracting Spotify metric value."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85, streams_total=1000000)
            ),
        )

        value = scorer._get_metric_value(track, "spotify_popularity_peak_peak")
        assert value == 85

    @staticmethod
    def test_get_metric_value_with_platform_mapping(tmp_path: Path) -> None:
        """Test metric extraction with platform name mapping."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["amazon_popularity"]}, f)

        _scorer = PowerRankingScorer(category_config_path=config_file)

        # Note: amazon → amazon_music mapping in PLATFORM_NAME_MAP
        # The scorer should handle this mapping

    @staticmethod
    def test_get_metric_value_missing_platform(tmp_path: Path) -> None:
        """Test extracting metric from missing platform."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test",
            ),
            platform_stats=PlatformStats(),  # No Spotify stats
        )

        value = scorer._get_metric_value(track, "spotify_popularity_peak")
        assert value is None

    @staticmethod
    def test_compute_rankings_empty_tracks(tmp_path: Path) -> None:
        """Test computing rankings with empty track list."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)
        results = scorer.compute_rankings([])

        assert isinstance(results, PowerRankingResults)
        assert results.rankings == []

    @staticmethod
    def test_compute_rankings_single_track(tmp_path: Path) -> None:
        """Test computing rankings with single track."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85, streams_total=1000000)
            ),
        )

        results = scorer.compute_rankings([track])

        assert len(results.rankings) == 1
        ranking = results.rankings[0]
        assert ranking.rank == 1
        assert ranking.track.title == "Test Track"
        assert ranking.total_score >= 0

    @staticmethod
    def test_compute_rankings_model_schema_compliance(tmp_path: Path) -> None:
        """Test that rankings use correct model schema."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "popularity": ["spotify_popularity_peak"],
                    "streams": ["spotify_streams_total"],
                },
                f
            )

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Test Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85, streams_total=1000000)
            ),
        )

        results = scorer.compute_rankings([track])
        ranking = results.rankings[0]

        # Check PowerRanking schema
        assert isinstance(ranking, PowerRanking)
        assert hasattr(ranking, "track")  # Not track_id, title, artist
        assert hasattr(ranking, "total_score")  # Not power_score
        assert hasattr(ranking, "rank")
        assert hasattr(ranking, "category_scores")
        assert isinstance(ranking.category_scores, list)

        # Check CategoryScore schema
        assert len(ranking.category_scores) == 2  # popularity + streams
        for cat_score in ranking.category_scores:
            assert isinstance(cat_score, CategoryScore)
            assert hasattr(cat_score, "category")
            assert hasattr(cat_score, "raw_score")  # 0-1 normalized
            assert hasattr(cat_score, "weight")
            assert hasattr(cat_score, "weighted_score")
            # Should NOT have normalized_score or data_availability
            assert not hasattr(cat_score, "normalized_score")
            assert not hasattr(cat_score, "data_availability")

    @staticmethod
    def test_compute_rankings_sorts_descending(tmp_path: Path) -> None:
        """Test that rankings are sorted by score descending."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        tracks = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=["Artist"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(
                    spotify=SpotifyStats(popularity_peak=pop)
                ),
            )
            for i, pop in enumerate([50, 90, 70, 30, 85])  # Mixed order
        ]

        results = scorer.compute_rankings(tracks)

        # Check that scores are in descending order
        for i in range(len(results.rankings) - 1):
            assert results.rankings[i].total_score >= results.rankings[i + 1].total_score

        # Check that ranks are assigned correctly
        for i, ranking in enumerate(results.rankings, start=1):
            assert ranking.rank == i

    @staticmethod
    def test_compute_rankings_raw_scores_normalized(tmp_path: Path) -> None:
        """Test that raw_score in CategoryScore is 0-1 normalized."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        tracks = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=["Artist"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(
                    spotify=SpotifyStats(popularity_peak=pop)
                ),
            )
            for i, pop in enumerate([10, 50, 90])
        ]

        results = scorer.compute_rankings(tracks)

        # Check that all raw_scores are in [0, 1] range
        for ranking in results.rankings:
            for cat_score in ranking.category_scores:
                assert 0.0 <= cat_score.raw_score <= 1.0

    @staticmethod
    def test_compute_rankings_weighted_scores(tmp_path: Path) -> None:
        """Test that weighted_score = raw_score × weight."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85)
            ),
        )

        results = scorer.compute_rankings([track])
        cat_score = results.rankings[0].category_scores[0]

        # weighted_score should equal raw_score × weight
        expected_weighted = cat_score.raw_score * cat_score.weight
        assert abs(cat_score.weighted_score - expected_weighted) < 0.001

    @staticmethod
    def test_compute_rankings_total_score(tmp_path: Path) -> None:
        """Test that total_score is sum of weighted category scores."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "popularity": ["spotify_popularity_peak"],
                    "streams": ["spotify_streams_total"],
                },
                f
            )

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85, streams_total=1000000)
            ),
        )

        results = scorer.compute_rankings([track])
        ranking = results.rankings[0]

        # Total score should be sum of all weighted scores
        expected_total = sum(cs.weighted_score for cs in ranking.category_scores)
        assert abs(ranking.total_score - expected_total) < 0.001

    @staticmethod
    def test_compute_rankings_handles_missing_data(tmp_path: Path) -> None:
        """Test that scorer handles tracks with missing metrics."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "popularity": ["spotify_popularity_peak", "apple_music_popularity"],
                },
                f
            )

        scorer = PowerRankingScorer(category_config_path=config_file)

        # Track with only Spotify data (Apple Music missing)
        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85)
                # No apple_music stats
            ),
        )

        results = scorer.compute_rankings([track])

        # Should still produce ranking (missing values treated as 0)
        assert len(results.rankings) == 1
        assert results.rankings[0].total_score >= 0

    @staticmethod
    def test_compute_rankings_multiple_tracks(tmp_path: Path) -> None:
        """Test computing rankings with multiple tracks."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        tracks = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=[f"Artist {i}"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(
                    spotify=SpotifyStats(popularity_peak=pop)
                ),
            )
            for i, pop in enumerate([50, 90, 70, 30, 85])
        ]

        results = scorer.compute_rankings(tracks)

        assert len(results.rankings) == 5
        # Top track should have highest popularity (90)
        assert results.rankings[0].track.title == "Track 1"
        assert results.rankings[0].rank == 1

    @staticmethod
    def test_compute_rankings_year_field(tmp_path: Path) -> None:
        """Test that PowerRankingResults includes year field."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test Track",
                artist_list=["Artist"],
                year=2025,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test Track",
            ),
            platform_stats=PlatformStats(
                spotify=SpotifyStats(popularity_peak=85)
            ),
        )

        results = scorer.compute_rankings([track])

        # Should have both year field and total_tracks property
        assert hasattr(results, "year")
        assert hasattr(results, "total_tracks")
        assert results.year == 2025
        assert results.total_tracks == 1

    @staticmethod
    def test_compute_rankings_all_zeros(tmp_path: Path) -> None:
        """Test computing rankings when all tracks have zero metrics."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"popularity": ["spotify_popularity_peak"]}, f)

        scorer = PowerRankingScorer(category_config_path=config_file)

        tracks = [
            TrackWithStats(
                track=Track(
                    title=f"Track {i}",
                    artist_list=["Artist"],
                    year=2024,
                ),
                songstats_identifiers=SongstatsIdentifiers(
                    songstats_id=f"{i}",
                    songstats_title=f"Track {i}",
                ),
                platform_stats=PlatformStats(
                    spotify=SpotifyStats(popularity_peak=0)
                ),
            )
            for i in range(3)
        ]

        results = scorer.compute_rankings(tracks)

        # All tracks have same value (0), so normalizer returns 0.5
        # 0.5 * weight(4) = 2.0 for all tracks
        for ranking in results.rankings:
            assert ranking.total_score == 2.0

    @staticmethod
    def test_load_missing_category_config(tmp_path: Path) -> None:
        """Test loading missing category config file."""
        config_file = tmp_path / "nonexistent.json"

        scorer = PowerRankingScorer(category_config_path=config_file)

        # Should create empty config
        assert scorer.category_config == {}

    @staticmethod
    def test_invalid_metric_name_format(tmp_path: Path) -> None:
        """Test handling metric name without underscore."""
        config_file = tmp_path / "categories.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump({"invalid": ["badmetricname"]}, f)  # No underscore

        scorer = PowerRankingScorer(category_config_path=config_file)

        track = TrackWithStats(
            track=Track(
                title="Test",
                artist_list=["Artist"],
                year=2024,
            ),
            songstats_identifiers=SongstatsIdentifiers(
                songstats_id="123",
                songstats_title="Test",
            ),
            platform_stats=PlatformStats(),
        )

        value = scorer._get_metric_value(track, "badmetricname")
        assert value is None
