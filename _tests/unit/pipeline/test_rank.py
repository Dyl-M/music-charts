"""Unit tests for RankingStage.

Tests power ranking computation and export.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest

# Local
from msc.models.ranking import PowerRankingResults
from msc.models.stats import TrackWithStats
from msc.pipeline.rank import RankingStage
from msc.pipeline.observer import EventType


class TestRankingStageInit:
    """Tests for RankingStage initialization."""

    @staticmethod
    def test_sets_scorer(tmp_path: Path) -> None:
        """Should set scorer instance."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.output_dir = tmp_path

            stage = RankingStage(scorer=mock_scorer)

            assert stage.scorer is mock_scorer

    @staticmethod
    def test_uses_settings_output_dir(tmp_path: Path) -> None:
        """Should use output dir from settings by default."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.output_dir = tmp_path

            stage = RankingStage(scorer=mock_scorer)

            assert stage.output_dir == tmp_path

    @staticmethod
    def test_accepts_custom_output_dir(tmp_path: Path) -> None:
        """Should accept custom output directory."""
        mock_scorer = MagicMock()
        custom_dir = tmp_path / "custom"

        stage = RankingStage(scorer=mock_scorer, output_dir=custom_dir)

        assert stage.output_dir == custom_dir

    @staticmethod
    def test_creates_output_dir(tmp_path: Path) -> None:
        """Should create output directory if it doesn't exist."""
        mock_scorer = MagicMock()
        new_dir = tmp_path / "new_output"

        RankingStage(scorer=mock_scorer, output_dir=new_dir)

        assert new_dir.exists()


class TestRankingStageName:
    """Tests for RankingStage.stage_name property."""

    @staticmethod
    def test_returns_ranking(tmp_path: Path) -> None:
        """Should return 'Ranking'."""
        mock_scorer = MagicMock()

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        assert stage.stage_name == "Ranking"


class TestRankingStageExtract:
    """Tests for RankingStage.extract method."""

    @staticmethod
    def test_returns_empty_without_repository(tmp_path: Path) -> None:
        """Should return empty list without stats repository."""
        mock_scorer = MagicMock()

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        result = stage.extract()

        assert result == []

    @staticmethod
    def test_loads_from_stats_repository(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list[TrackWithStats],
    ) -> None:
        """Should load tracks from repository."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        mock_scorer = MagicMock()

        stage = RankingStage(
            scorer=mock_scorer,
            output_dir=tmp_path,
            stats_repository=mock_stats_repository,
        )

        result = stage.extract()

        assert result == sample_tracks_with_stats


class TestRankingStageTransform:
    """Tests for RankingStage.transform method."""

    @staticmethod
    def test_returns_empty_results_for_empty_input(tmp_path: Path) -> None:
        """Should return empty results for empty input."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

            result = stage.transform([])

            assert isinstance(result, PowerRankingResults)
            assert len(result.rankings) == 0

    @staticmethod
    def test_calls_scorer_compute_rankings(
            tmp_path: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should call scorer.compute_rankings."""
        mock_scorer = MagicMock()
        mock_results = MagicMock()
        mock_results.rankings = []
        mock_scorer.compute_rankings.return_value = mock_results

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        stage.transform(sample_tracks_with_stats)

        mock_scorer.compute_rankings.assert_called_once_with(sample_tracks_with_stats)

    @staticmethod
    def test_returns_power_ranking_results(
            tmp_path: Path,
            sample_tracks_with_stats: list[TrackWithStats],
            sample_power_ranking_results: PowerRankingResults,
    ) -> None:
        """Should return PowerRankingResults."""
        mock_scorer = MagicMock()
        mock_scorer.compute_rankings.return_value = sample_power_ranking_results

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        result = stage.transform(sample_tracks_with_stats)

        assert result is sample_power_ranking_results

    @staticmethod
    def test_notifies_stage_completed(
            tmp_path: Path,
            mock_observer,
            sample_tracks_with_stats: list[TrackWithStats],
            sample_power_ranking_results: PowerRankingResults,
    ) -> None:
        """Should notify stage completed event."""
        mock_scorer = MagicMock()
        mock_scorer.compute_rankings.return_value = sample_power_ranking_results

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)
        stage.attach(mock_observer)

        stage.transform(sample_tracks_with_stats)

        event_types = [e.event_type for e in mock_observer.events]
        assert EventType.STAGE_COMPLETED in event_types

    @staticmethod
    def test_raises_on_scorer_failure(
            tmp_path: Path, sample_tracks_with_stats: list[TrackWithStats]
    ) -> None:
        """Should raise exception on scorer failure."""
        mock_scorer = MagicMock()
        mock_scorer.compute_rankings.side_effect = ValueError("Scoring failed")

        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        with pytest.raises(ValueError, match="Scoring failed"):
            stage.transform(sample_tracks_with_stats)


class TestRankingStageLoad:
    """Tests for RankingStage.load method."""

    @staticmethod
    def test_exports_to_json(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should export rankings to JSON."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

            stage.load(sample_power_ranking_results)

            json_path = tmp_path / "power_rankings_2024.json"
            assert json_path.exists()

    @staticmethod
    def test_exports_to_csv(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should export rankings to CSV."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

            stage.load(sample_power_ranking_results)

            csv_path = tmp_path / "power_rankings_2024.csv"
            assert csv_path.exists()

    @staticmethod
    def test_exports_flat_json(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should export flat rankings to JSON."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

            stage.load(sample_power_ranking_results)

            flat_path = tmp_path / "power_rankings_2024_flat.json"
            assert flat_path.exists()

    @staticmethod
    def test_notifies_checkpoint_saved(
            tmp_path: Path,
            mock_observer,
            sample_power_ranking_results: PowerRankingResults,
    ) -> None:
        """Should notify checkpoint saved event."""
        mock_scorer = MagicMock()

        with patch("msc.pipeline.rank.get_settings") as mock_settings:
            mock_settings.return_value.year = 2024

            stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)
            stage.attach(mock_observer)

            stage.load(sample_power_ranking_results)

            event_types = [e.event_type for e in mock_observer.events]
            assert EventType.CHECKPOINT_SAVED in event_types


class TestRankingStageExportJson:
    """Tests for RankingStage._export_rankings_json method."""

    @staticmethod
    def test_writes_valid_json(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should write valid JSON."""
        import json

        mock_scorer = MagicMock()
        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        json_path = tmp_path / "test.json"
        stage._export_rankings_json(sample_power_ranking_results, json_path)

        content = json.loads(json_path.read_text(encoding="utf-8"))
        assert "rankings" in content
        assert "year" in content


class TestRankingStageExportCsv:
    """Tests for RankingStage._export_rankings_csv method."""

    @staticmethod
    def test_writes_headers(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should write CSV headers."""
        mock_scorer = MagicMock()
        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        csv_path = tmp_path / "test.csv"
        stage._export_rankings_csv(sample_power_ranking_results, csv_path)

        content = csv_path.read_text(encoding="utf-8")
        assert "rank" in content
        assert "artist" in content
        assert "title" in content
        assert "total_score" in content

    @staticmethod
    def test_handles_empty_rankings(tmp_path: Path) -> None:
        """Should handle empty rankings."""
        mock_scorer = MagicMock()
        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        results = PowerRankingResults(rankings=[], year=2024)
        csv_path = tmp_path / "empty.csv"

        stage._export_rankings_csv(results, csv_path)

        # File should exist but be empty (no rows)
        assert csv_path.exists()


class TestRankingStageExportFlat:
    """Tests for RankingStage._export_rankings_flat method."""

    @staticmethod
    def test_writes_flat_structure(
            tmp_path: Path, sample_power_ranking_results: PowerRankingResults
    ) -> None:
        """Should write flat JSON structure."""
        import json

        mock_scorer = MagicMock()
        stage = RankingStage(scorer=mock_scorer, output_dir=tmp_path)

        flat_path = tmp_path / "flat.json"
        stage._export_rankings_flat(sample_power_ranking_results, flat_path)

        content = json.loads(flat_path.read_text(encoding="utf-8"))
        assert isinstance(content, list)
        if content:
            assert "rank" in content[0]
            assert "total_score" in content[0]
