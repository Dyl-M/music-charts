"""Integration tests for CLI commands.

Tests CLI commands with test mode and mocked dependencies.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner

# Local
from msc.cli import app

runner = CliRunner()


class TestRunCommandIntegration:
    """Integration tests for 'msc run' command with new flags."""

    @staticmethod
    def test_run_help_shows_test_mode_flag() -> None:
        """Should show --test-mode flag in help output."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--test-mode" in result.output
        assert "-t" in result.output

    @staticmethod
    def test_run_help_shows_limit_flag() -> None:
        """Should show --limit flag in help output."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--limit" in result.output
        assert "-l" in result.output

    @staticmethod
    def test_run_help_shows_cleanup_flag() -> None:
        """Should show --cleanup flag in help output."""
        result = runner.invoke(app, ["run", "--help"])
        assert result.exit_code == 0
        assert "--cleanup" in result.output

    @staticmethod
    def test_run_with_test_mode_displays_message(tmp_path: Path) -> None:
        """Should display test mode message when --test-mode is used."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = None
            mock_orchestrator.return_value = mock_orch

            result = runner.invoke(app, ["run", "--test-mode"])

            assert "Test mode enabled" in result.output

    @staticmethod
    def test_run_with_limit_displays_message(tmp_path: Path) -> None:
        """Should display track limit when --limit is used with --test-mode."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = None
            mock_orchestrator.return_value = mock_orch

            result = runner.invoke(app, ["run", "--test-mode", "--limit", "5"])

            assert "Test mode enabled" in result.output
            assert "Track limit: 5" in result.output

    @staticmethod
    def test_run_passes_test_mode_to_orchestrator(tmp_path: Path) -> None:
        """Should pass test_mode=True to orchestrator when flag is set."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = None
            mock_orchestrator_class.return_value = mock_orch

            runner.invoke(app, ["run", "--test-mode"])

            # Verify orchestrator was called with test_mode=True
            call_kwargs = mock_orchestrator_class.call_args.kwargs
            assert call_kwargs.get("test_mode") is True

    @staticmethod
    def test_run_passes_limit_to_orchestrator(tmp_path: Path) -> None:
        """Should pass track_limit to orchestrator when --limit is set."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = None
            mock_orchestrator_class.return_value = mock_orch

            runner.invoke(app, ["run", "--limit", "10"])

            call_kwargs = mock_orchestrator_class.call_args.kwargs
            assert call_kwargs.get("track_limit") == 10

    @staticmethod
    def test_run_cleanup_deletes_run_directory(tmp_path: Path) -> None:
        """Should delete run directory when --cleanup flag is set."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            # Create a fake run directory
            run_dir = tmp_path / "runs" / "2025_test"
            run_dir.mkdir(parents=True)
            (run_dir / "test_file.json").write_text("{}", encoding="utf-8")

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = run_dir
            mock_orchestrator_class.return_value = mock_orch

            result = runner.invoke(app, ["run", "--cleanup"])

            assert "Cleaning up run directory" in result.output
            assert "Cleanup complete" in result.output
            assert not run_dir.exists()

    @staticmethod
    def test_run_no_cleanup_when_flag_not_set(tmp_path: Path) -> None:
        """Should not delete run directory when --cleanup is not set."""
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.cli.setup_logging"), \
                patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orchestrator_class:
            mock_settings_obj = MagicMock()
            mock_settings_obj.data_dir = tmp_path
            mock_settings_obj.year = 2025
            mock_settings.return_value = mock_settings_obj

            run_dir = tmp_path / "runs" / "2025_test"
            run_dir.mkdir(parents=True)
            (run_dir / "test_file.json").write_text("{}", encoding="utf-8")

            mock_orch = MagicMock()
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.metrics_observer.get_success_rate.return_value = 0
            mock_orch.get_review_queue.return_value = []
            mock_orch.run_dir = run_dir
            mock_orchestrator_class.return_value = mock_orch

            result = runner.invoke(app, ["run"])

            assert "Cleaning up" not in result.output
            assert run_dir.exists()


class TestSettingsTestLibraryPath:
    """Tests for settings.test_library_path property."""

    @staticmethod
    def test_test_library_path_returns_valid_path() -> None:
        """Should return path to test library fixture."""
        from msc.config.settings import Settings

        settings = Settings()
        path = settings.test_library_path

        assert isinstance(path, Path)
        assert path.name == "test_library.xml"
        assert "_tests" in str(path)
        assert "fixtures" in str(path)

    @staticmethod
    def test_test_library_path_exists() -> None:
        """Should point to existing test library file."""
        from msc.config.settings import Settings

        settings = Settings()
        path = settings.test_library_path

        assert path.exists(), f"Test library not found at {path}"
