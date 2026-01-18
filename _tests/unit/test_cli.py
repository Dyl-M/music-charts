"""Unit tests for CLI module.

Tests CLI commands and helper functions.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch

# Third-party
import pytest
from typer.testing import CliRunner

# Local
# noinspection PyProtectedMember
from msc.cli import (
    app,
    version_callback,
    _determine_stages,
    _display_pipeline_config,
    _display_summary,
    _has_platform_data,
    _count_platform_tracks,
)

runner = CliRunner()


class TestVersionCallback:
    """Tests for version_callback function."""

    @staticmethod
    def test_raises_exit_when_true() -> None:
        """Should raise SystemExit when value is True."""
        import typer
        with pytest.raises(typer.Exit):
            version_callback(True)

    @staticmethod
    def test_no_exit_when_false() -> None:
        """Should not exit when value is False."""
        version_callback(False)  # Should not raise


class TestDetermineStages:
    """Tests for _determine_stages function."""

    @staticmethod
    def test_all_stages_when_none() -> None:
        """Should run all stages when None provided."""
        extract, enrich, rank = _determine_stages(None)
        assert extract is True
        assert enrich is True
        assert rank is True

    @staticmethod
    def test_all_stages_when_all() -> None:
        """Should run all stages when 'all' specified."""
        extract, enrich, rank = _determine_stages(["all"])
        assert extract is True
        assert enrich is True
        assert rank is True

    @staticmethod
    def test_extract_only() -> None:
        """Should run only extraction when specified."""
        extract, enrich, rank = _determine_stages(["extract"])
        assert extract is True
        assert enrich is False
        assert rank is False

    @staticmethod
    def test_enrich_only() -> None:
        """Should run only enrichment when specified."""
        extract, enrich, rank = _determine_stages(["enrich"])
        assert extract is False
        assert enrich is True
        assert rank is False

    @staticmethod
    def test_rank_only() -> None:
        """Should run only ranking when specified."""
        extract, enrich, rank = _determine_stages(["rank"])
        assert extract is False
        assert enrich is False
        assert rank is True

    @staticmethod
    def test_multiple_stages() -> None:
        """Should run multiple specified stages."""
        extract, enrich, rank = _determine_stages(["extract", "rank"])
        assert extract is True
        assert enrich is False
        assert rank is True


class TestDisplayPipelineConfig:
    """Tests for _display_pipeline_config function."""

    @staticmethod
    def test_outputs_year(capsys) -> None:
        """Should output the target year."""
        _display_pipeline_config(2025, True, True, True, False)
        captured = capsys.readouterr()
        assert "2025" in captured.out

    @staticmethod
    def test_outputs_stage_status(capsys) -> None:
        """Should output stage status with checkmarks."""
        _display_pipeline_config(2025, True, False, True, False)
        captured = capsys.readouterr()
        assert "Extraction" in captured.out
        assert "Enrichment" in captured.out
        assert "Ranking" in captured.out

    @staticmethod
    def test_outputs_youtube_status(capsys) -> None:
        """Should output YouTube status."""
        _display_pipeline_config(2025, True, True, True, True)
        captured = capsys.readouterr()
        assert "YouTube" in captured.out
        assert "disabled" in captured.out


class TestDisplaySummary:
    """Tests for _display_summary function."""

    @staticmethod
    def test_outputs_metrics(capsys) -> None:
        """Should output pipeline metrics."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_metrics.return_value = {
            "stages_completed": 3,
            "items_processed": 100,
            "items_failed": 5,
        }
        mock_orchestrator.metrics_observer.get_success_rate.return_value = 95.0
        mock_orchestrator.get_review_queue.return_value = []

        mock_results = MagicMock()
        mock_results.rankings = []

        with patch("msc.cli.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = Path("/data")
            _display_summary(mock_orchestrator, mock_results)

        captured = capsys.readouterr()
        assert "Summary" in captured.out
        assert "95.0%" in captured.out

    @staticmethod
    def test_shows_review_queue(capsys) -> None:
        """Should show review queue if not empty."""
        mock_orchestrator = MagicMock()
        mock_orchestrator.get_metrics.return_value = {}
        mock_orchestrator.metrics_observer.get_success_rate.return_value = 0
        mock_orchestrator.get_review_queue.return_value = ["item1", "item2"]

        mock_results = MagicMock()
        mock_results.rankings = []

        with patch("msc.cli.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = Path("/data")
            _display_summary(mock_orchestrator, mock_results)

        captured = capsys.readouterr()
        assert "manual review" in captured.out.lower()


class TestHasPlatformData:
    """Tests for _has_platform_data function."""

    @staticmethod
    def test_returns_false_for_none_platform() -> None:
        """Should return False when platform is None."""
        mock_track = MagicMock()
        mock_track.platform_stats.spotify = None

        result = _has_platform_data(mock_track, "spotify")
        assert result is False

    @staticmethod
    def test_returns_true_for_non_none_values() -> None:
        """Should return True when platform has non-None values."""
        mock_track = MagicMock()
        mock_platform = MagicMock()
        mock_platform.model_dump.return_value = {"streams_total": 1000, "popularity": None}
        mock_track.platform_stats.spotify = mock_platform

        result = _has_platform_data(mock_track, "spotify")
        assert result is True

    @staticmethod
    def test_returns_false_for_all_none_values() -> None:
        """Should return False when all platform values are None."""
        mock_track = MagicMock()
        mock_platform = MagicMock()
        mock_platform.model_dump.return_value = {"streams_total": None, "popularity": None}
        mock_track.platform_stats.spotify = mock_platform

        result = _has_platform_data(mock_track, "spotify")
        assert result is False


class TestCountPlatformTracks:
    """Tests for _count_platform_tracks function."""

    @staticmethod
    def test_counts_spotify_tracks() -> None:
        """Should count tracks with Spotify data."""
        mock_track1 = MagicMock()
        mock_platform = MagicMock()
        mock_platform.model_dump.return_value = {"streams_total": 1000}
        mock_track1.platform_stats.spotify = mock_platform
        # All other platforms None
        for attr in ["apple_music", "youtube", "amazon_music", "deezer",
                     "soundcloud", "tidal", "tiktok", "beatport", "tracklists"]:
            setattr(mock_track1.platform_stats, attr, None)

        result = _count_platform_tracks([mock_track1])
        assert result["Spotify"] == 1
        assert result["Apple Music"] == 0

    @staticmethod
    def test_returns_empty_for_empty_list() -> None:
        """Should return zeros for empty list."""
        result = _count_platform_tracks([])
        assert all(count == 0 for count in result.values())


class TestCLIHelp:
    """Tests for CLI help output."""

    @staticmethod
    def test_main_help() -> None:
        """Should show main help text."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Music Charts" in result.output

    @staticmethod
    def test_run_help() -> None:
        """Should show run command help."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "pipeline" in result.output.lower()

    @staticmethod
    def test_billing_help() -> None:
        """Should show billing command help."""
        result = runner.invoke(app, ["billing", "--help"])
        assert result.exit_code == 0
        assert "Songstats" in result.output

    @staticmethod
    def test_validate_help() -> None:
        """Should show validate command help."""
        result = runner.invoke(app, ["validate", "--help"])
        assert result.exit_code == 0
        assert "validate" in result.output.lower()

    @staticmethod
    def test_export_help() -> None:
        """Should show export command help."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "export" in result.output.lower()

    @staticmethod
    def test_clean_help() -> None:
        """Should show clean command help."""
        result = runner.invoke(app, ["clean", "--help"])
        assert result.exit_code == 0
        assert "cache" in result.output.lower()

    @staticmethod
    def test_stats_help() -> None:
        """Should show stats command help."""
        result = runner.invoke(app, ["stats", "--help"])
        assert result.exit_code == 0
        assert "statistics" in result.output.lower()

    @staticmethod
    def test_init_help() -> None:
        """Should show init command help."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0
        assert "directory" in result.output.lower()


class TestCLIVersion:
    """Tests for CLI version output."""

    @staticmethod
    def test_version_option() -> None:
        """Should show version with --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "msc version" in result.output

    @staticmethod
    def test_version_short_option() -> None:
        """Should show version with -v flag."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "msc version" in result.output


class TestCLIInit:
    """Tests for CLI init command."""

    @staticmethod
    def test_creates_directories(tmp_path: Path) -> None:
        """Should create directory structure."""
        with patch("msc.cli.get_settings") as mock_settings:
            mock_settings_instance = MagicMock()
            mock_settings_instance.data_dir = tmp_path / "data"
            mock_settings_instance.input_dir = tmp_path / "input"
            mock_settings_instance.output_dir = tmp_path / "output"
            mock_settings_instance.cache_dir = tmp_path / "cache"
            mock_settings_instance.tokens_dir = tmp_path / "tokens"
            mock_settings_instance.config_dir = tmp_path / "config"
            mock_settings.return_value = mock_settings_instance

            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert "complete" in result.output.lower()
            mock_settings_instance.ensure_directories.assert_called_once()


class TestCLIClean:
    """Tests for CLI clean command."""

    @staticmethod
    def test_dry_run_default(tmp_path: Path) -> None:
        """Should use dry run by default."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.CacheManager") as mock_manager_class, \
                patch("msc.cli.setup_logging"):
            # Setup settings mock with all required paths
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.cache_dir = tmp_path / "cache"
            mock_settings.return_value = mock_settings_obj

            mock_manager = MagicMock()
            mock_stats = MagicMock()
            mock_stats.file_count = 5
            mock_stats.total_size_bytes = 1024
            mock_stats.oldest_file_age_days = 3
            mock_stats.cache_dir = tmp_path / "cache"
            mock_manager.get_stats.return_value = mock_stats
            mock_manager.clean.return_value = 5
            mock_manager.format_size.return_value = "1.0 KB"
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(app, ["clean"])

            assert result.exit_code == 0
            mock_manager.clean.assert_called_once_with(dry_run=True, older_than_days=None)

    @staticmethod
    def test_shows_empty_cache_message(tmp_path: Path) -> None:
        """Should show message for empty cache."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.CacheManager") as mock_manager_class, \
                patch("msc.cli.setup_logging"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.cache_dir = tmp_path / "cache"
            mock_settings.return_value = mock_settings_obj

            mock_manager = MagicMock()
            mock_stats = MagicMock()
            mock_stats.file_count = 0
            mock_manager.get_stats.return_value = mock_stats
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(app, ["clean"])

            assert result.exit_code == 0
            assert "empty" in result.output.lower()


class TestCLIValidate:
    """Tests for CLI validate command."""

    @staticmethod
    def test_validates_existing_file(tmp_path: Path) -> None:
        """Should validate existing JSON file."""
        import json

        test_file = tmp_path / "test.json"
        test_file.write_text(
            json.dumps([{"title": "Test", "artist_list": ["A"], "year": 2024}]),
            encoding="utf-8"
        )

        with patch("msc.cli.FileValidator") as mock_validator_class, \
                patch("msc.cli.ValidationFormatter"):
            mock_validator = MagicMock()
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.model_name = "Track"
            mock_validator.validate_file.return_value = mock_result
            mock_validator_class.return_value = mock_validator

            result = runner.invoke(app, ["validate", str(test_file)])

            assert result.exit_code == 0

    @staticmethod
    def test_fails_for_missing_file() -> None:
        """Should fail for non-existent file."""
        result = runner.invoke(app, ["validate", "/nonexistent/file.json"])
        assert result.exit_code != 0

    @staticmethod
    def test_displays_validation_errors(tmp_path: Path) -> None:
        """Should display validation errors for invalid file."""
        import json

        test_file = tmp_path / "invalid.json"
        test_file.write_text(json.dumps([{"bad": "data"}]), encoding="utf-8")

        with patch("msc.cli.FileValidator") as mock_validator_class, \
                patch("msc.cli.ValidationFormatter") as mock_formatter:
            mock_validator = MagicMock()
            mock_result = MagicMock()
            mock_result.is_valid = False
            mock_result.errors = ["Missing field: title"]
            mock_result.error_count = 1
            mock_validator.validate_file.return_value = mock_result
            mock_validator_class.return_value = mock_validator

            mock_formatter.format_error_list.return_value = "Error list"

            result = runner.invoke(app, ["validate", str(test_file)])

            assert result.exit_code == 1
            assert "failed" in result.output.lower()


class TestCLIBilling:
    """Tests for CLI billing command."""

    @staticmethod
    def test_displays_quota_table(tmp_path: Path) -> None:
        """Should display quota table with billing info."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.clients.songstats.SongstatsClient") as mock_client_class, \
                patch("msc.cli.QuotaFormatter") as mock_formatter, \
                patch("rich.console.Console"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.get_songstats_key.return_value = "test_key"
            mock_settings.return_value = mock_settings_obj

            mock_client = MagicMock()
            mock_client.get_quota.return_value = {
                "used": 100,
                "limit": 1000,
                "remaining": 900,
            }
            mock_client_class.return_value = mock_client

            mock_formatter.format_billing_table.return_value = "Billing Table"

            result = runner.invoke(app, ["billing"])

            assert result.exit_code == 0
            mock_client.get_quota.assert_called_once()

    @staticmethod
    def test_handles_network_error(tmp_path: Path) -> None:
        """Should handle network error gracefully."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.clients.songstats.SongstatsClient") as mock_client_class, \
                patch("msc.cli.ErrorHandler") as mock_handler:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.get_songstats_key.return_value = "test_key"
            mock_settings.return_value = mock_settings_obj

            mock_client = MagicMock()
            mock_client.get_quota.return_value = None
            mock_client_class.return_value = mock_client

            mock_handler.handle.return_value = "Network error occurred"

            result = runner.invoke(app, ["billing"])

            assert result.exit_code == 1

    @staticmethod
    def test_handles_missing_api_key(tmp_path: Path) -> None:
        """Should handle missing API key."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.cli.ErrorHandler") as mock_handler:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.get_songstats_key.side_effect = FileNotFoundError("API key not found")
            mock_settings.return_value = mock_settings_obj

            mock_handler.handle.return_value = "API key not found"

            result = runner.invoke(app, ["billing"])

            assert result.exit_code == 1


class TestCLIExport:
    """Tests for CLI export command."""

    @staticmethod
    def test_export_csv_creates_file(tmp_path: Path) -> None:
        """Should export to CSV format."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class, \
                patch("msc.cli.DataExporter") as mock_exporter_class, \
                patch("msc.cli.ExportFormatter") as mock_formatter, \
                patch("rich.console.Console"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year_output_dir = tmp_path / "output" / "2026"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            # Create fake stats file
            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.count.return_value = 5
            mock_repo_class.return_value = mock_repo

            mock_exporter = MagicMock()
            mock_result = MagicMock()
            mock_result.row_count = 5
            mock_result.file_size_bytes = 1024
            mock_result.duration_seconds = 0.5
            mock_result.file_path = tmp_path / "export.csv"
            mock_exporter.export_csv.return_value = mock_result
            mock_exporter_class.return_value = mock_exporter

            mock_formatter.format_export_summary.return_value = "Export summary"

            result = runner.invoke(app, ["export", "--year", "2026", "--format", "csv"])

            assert result.exit_code == 0
            mock_exporter.export_csv.assert_called_once()

    @staticmethod
    def test_export_ods_creates_file(tmp_path: Path) -> None:
        """Should export to ODS format."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class, \
                patch("msc.cli.DataExporter") as mock_exporter_class, \
                patch("msc.cli.ExportFormatter") as mock_formatter, \
                patch("rich.console.Console"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year_output_dir = tmp_path / "output" / "2026"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.count.return_value = 5
            mock_repo_class.return_value = mock_repo

            mock_exporter = MagicMock()
            mock_result = MagicMock()
            mock_result.row_count = 5
            mock_result.file_size_bytes = 2048
            mock_result.duration_seconds = 0.8
            mock_result.file_path = tmp_path / "export.ods"
            mock_exporter.export_ods.return_value = mock_result
            mock_exporter_class.return_value = mock_exporter

            mock_formatter.format_export_summary.return_value = "Export summary"

            result = runner.invoke(app, ["export", "--year", "2026", "--format", "ods"])

            assert result.exit_code == 0
            mock_exporter.export_ods.assert_called_once()

    @staticmethod
    def test_export_html_creates_file(tmp_path: Path) -> None:
        """Should export to HTML format."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class, \
                patch("msc.cli.DataExporter") as mock_exporter_class, \
                patch("msc.cli.ExportFormatter") as mock_formatter, \
                patch("rich.console.Console"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year_output_dir = tmp_path / "output" / "2026"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.count.return_value = 5
            mock_repo_class.return_value = mock_repo

            mock_exporter = MagicMock()
            mock_result = MagicMock()
            mock_result.row_count = 5
            mock_result.file_size_bytes = 4096
            mock_result.duration_seconds = 1.0
            mock_result.file_path = tmp_path / "export.html"
            mock_exporter.export_html.return_value = mock_result
            mock_exporter_class.return_value = mock_exporter

            mock_formatter.format_export_summary.return_value = "Export summary"

            result = runner.invoke(app, ["export", "--year", "2026", "--format", "html"])

            assert result.exit_code == 0
            mock_exporter.export_html.assert_called_once()

    @staticmethod
    def test_export_handles_missing_data(tmp_path: Path) -> None:
        """Should show error when data file does not exist."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            result = runner.invoke(app, ["export", "--year", "2026"])

            assert result.exit_code == 1
            assert "no data found" in result.output.lower()

    @staticmethod
    def test_export_handles_empty_repository(tmp_path: Path) -> None:
        """Should show error when repository is empty."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.count.return_value = 0
            mock_repo_class.return_value = mock_repo

            result = runner.invoke(app, ["export", "--year", "2026"])

            assert result.exit_code == 1
            assert "empty" in result.output.lower()

    @staticmethod
    def test_export_unsupported_format(tmp_path: Path) -> None:
        """Should show error for unsupported format."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year_output_dir = tmp_path / "output" / "2026"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.count.return_value = 5
            mock_repo_class.return_value = mock_repo

            result = runner.invoke(app, ["export", "--year", "2026", "--format", "pdf"])

            assert result.exit_code == 1
            assert "unsupported" in result.output.lower()


class TestCLIStats:
    """Tests for CLI stats command."""

    @staticmethod
    def test_displays_statistics(tmp_path: Path) -> None:
        """Should display dataset statistics."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class, \
                patch("msc.cli._count_platform_tracks") as mock_count:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_track = MagicMock()
            mock_repo.get_all.return_value = [mock_track]
            mock_repo_class.return_value = mock_repo

            mock_count.return_value = {"Spotify": 1, "Apple Music": 0}

            result = runner.invoke(app, ["stats", "--year", "2026"])

            assert result.exit_code == 0
            assert "statistics" in result.output.lower()

    @staticmethod
    def test_handles_missing_file(tmp_path: Path) -> None:
        """Should show error when stats file does not exist."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            result = runner.invoke(app, ["stats", "--year", "2026"])

            assert result.exit_code == 1
            assert "no data found" in result.output.lower()

    @staticmethod
    def test_handles_empty_data(tmp_path: Path) -> None:
        """Should show error when repository returns empty list."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.storage.json_repository.JSONStatsRepository") as mock_repo_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.output_dir = tmp_path / "output"
            mock_settings_obj.year = 2026
            mock_settings.return_value = mock_settings_obj

            stats_file = tmp_path / "output" / "enriched_tracks.json"
            stats_file.parent.mkdir(parents=True, exist_ok=True)
            stats_file.write_text("[]", encoding="utf-8")

            mock_repo = MagicMock()
            mock_repo.get_all.return_value = []
            mock_repo_class.return_value = mock_repo

            result = runner.invoke(app, ["stats", "--year", "2026"])

            assert result.exit_code == 1
            assert "empty" in result.output.lower()


class TestCLICleanExtended:
    """Extended tests for CLI clean command."""

    @staticmethod
    def test_actual_deletion(tmp_path: Path) -> None:
        """Should actually delete files when --no-dry-run is used."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.CacheManager") as mock_manager_class, \
                patch("msc.cli.setup_logging"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.cache_dir = tmp_path / "cache"
            mock_settings.return_value = mock_settings_obj

            mock_manager = MagicMock()
            mock_stats = MagicMock()
            mock_stats.file_count = 5
            mock_stats.total_size_bytes = 1024
            mock_stats.oldest_file_age_days = 3
            mock_stats.cache_dir = tmp_path / "cache"
            mock_manager.get_stats.return_value = mock_stats
            mock_manager.clean.return_value = 5
            mock_manager.format_size.return_value = "1.0 KB"
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(app, ["clean", "--no-dry-run"])

            assert result.exit_code == 0
            mock_manager.clean.assert_called_once_with(dry_run=False, older_than_days=None)
            assert "deleted" in result.output.lower()

    @staticmethod
    def test_older_than_filter(tmp_path: Path) -> None:
        """Should apply older-than filter."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.CacheManager") as mock_manager_class, \
                patch("msc.cli.setup_logging"):
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.cache_dir = tmp_path / "cache"
            mock_settings.return_value = mock_settings_obj

            mock_manager = MagicMock()
            mock_stats = MagicMock()
            mock_stats.file_count = 10
            mock_stats.total_size_bytes = 2048
            mock_stats.oldest_file_age_days = 30
            mock_stats.cache_dir = tmp_path / "cache"
            mock_manager.get_stats.return_value = mock_stats
            mock_manager.clean.return_value = 3
            mock_manager.format_size.return_value = "2.0 KB"
            mock_manager_class.return_value = mock_manager

            result = runner.invoke(app, ["clean", "--older-than", "7"])

            assert result.exit_code == 0
            mock_manager.clean.assert_called_once_with(dry_run=True, older_than_days=7)
