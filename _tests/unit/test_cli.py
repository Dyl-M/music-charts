"""Unit tests for CLI commands."""

# Standard library
from pathlib import Path
from unittest.mock import Mock, patch

# Third-party
from typer.testing import CliRunner

# Local
from msc import __version__
from msc.cli import app

runner = CliRunner()


class TestVersionFlag:
    """Tests for --version flag."""

    @staticmethod
    def test_version_short_flag() -> None:
        """Should display version with -v flag."""
        result = runner.invoke(app, ["-v"])

        assert result.exit_code == 0
        assert f"msc version {__version__}" in result.stdout

    @staticmethod
    def test_version_long_flag() -> None:
        """Should display version with --version flag."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert f"msc version {__version__}" in result.stdout

    @staticmethod
    def test_version_exits_without_running_command() -> None:
        """Should exit after displaying version."""
        result = runner.invoke(app, ["--version", "init"])

        # Should exit with version, not run init command
        assert result.exit_code == 0
        assert f"msc version {__version__}" in result.stdout
        assert "Directories created" not in result.stdout


class TestInitCommand:
    """Tests for the init command."""

    @staticmethod
    def test_init_creates_directories(tmp_path: Path) -> None:
        """Should create all required directories."""
        # Use a temporary settings instance
        from msc.config.settings import Settings

        settings = Settings(
            data_dir=tmp_path / "data",
            tokens_dir=tmp_path / "tokens",
            config_dir=tmp_path / "config",
        )

        with patch("msc.cli.get_settings", return_value=settings):
            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert "Creating directory structure..." in result.stdout
            assert "Directories created:" in result.stdout
            assert "Initialization complete!" in result.stdout

            # Verify directories were created
            assert settings.data_dir.exists()
            assert settings.input_dir.exists()
            assert settings.output_dir.exists()
            assert settings.cache_dir.exists()
            assert settings.tokens_dir.exists()
            assert settings.config_dir.exists()

    @staticmethod
    def test_init_displays_created_directories(tmp_path: Path) -> None:
        """Should display list of created directories."""
        from msc.config.settings import Settings

        settings = Settings(
            data_dir=tmp_path / "data",
            tokens_dir=tmp_path / "tokens",
            config_dir=tmp_path / "config",
        )

        with patch("msc.cli.get_settings", return_value=settings):
            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert str(settings.data_dir) in result.stdout
            assert str(settings.input_dir) in result.stdout
            assert str(settings.output_dir) in result.stdout
            assert str(settings.cache_dir) in result.stdout
            assert str(settings.tokens_dir) in result.stdout
            assert str(settings.config_dir) in result.stdout

    @staticmethod
    def test_init_idempotent(tmp_path: Path) -> None:
        """Should handle directories that already exist."""
        from msc.config.settings import Settings

        settings = Settings(
            data_dir=tmp_path / "data",
            tokens_dir=tmp_path / "tokens",
            config_dir=tmp_path / "config",
        )

        # Create directories first
        settings.ensure_directories()

        # Run init again - should not fail
        with patch("msc.cli.get_settings", return_value=settings):
            result = runner.invoke(app, ["init"])

            assert result.exit_code == 0
            assert "Initialization complete!" in result.stdout


class TestRunCommand:
    """Tests for the run command."""

    @staticmethod
    def test_run_not_implemented() -> None:
        """Run command is now implemented."""
        # The run command is no longer NotImplementedError - it's implemented in Phase 4
        result = runner.invoke(app, ["run"])
        # Command should show pipeline stages even if execution fails
        assert "Pipeline stages:" in result.stdout

    @staticmethod
    def test_run_with_year() -> None:
        """Should accept year parameter."""
        result = runner.invoke(app, ["run", "--year", "2024"])

        # Should display year in pipeline header
        assert "Year 2024" in result.stdout
        assert "Pipeline stages:" in result.stdout

    @staticmethod
    def test_run_with_stages() -> None:
        """Should accept stage parameters."""
        result = runner.invoke(app, ["run", "--stage", "extract", "--stage", "enrich"])

        # Should display stage selection in output
        assert "Pipeline stages:" in result.stdout
        assert "Extraction:  ✓" in result.stdout
        assert "Enrichment:  ✓" in result.stdout
        assert "Ranking:     ✗" in result.stdout  # Not selected

    @staticmethod
    def test_run_with_reset_confirmed() -> None:
        """Should reset pipeline when confirmed."""
        with patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.reset_pipeline.return_value = None
            mock_orch.run.return_value = None
            mock_orch.get_metrics.return_value = {}
            mock_orch.get_review_queue.return_value = []
            mock_orch.metrics_observer.get_success_rate.return_value = 100.0

            # Simulate user confirming reset
            result = runner.invoke(app, ["run", "--reset"], input="y\n")

            # Should show confirmation prompt and reset message
            assert "This will delete all checkpoints" in result.stdout
            assert "Pipeline reset complete" in result.stdout

    @staticmethod
    def test_run_with_reset_aborted() -> None:
        """Should abort reset when user declines."""
        with patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value

            # Simulate user declining reset
            result = runner.invoke(app, ["run", "--reset"], input="n\n")

            # Should abort without resetting (exit code 1 when confirmation is rejected)
            assert result.exit_code == 1
            # Confirmation prompt should be shown
            assert "This will delete all checkpoints" in result.stdout
            # Should not have called reset
            mock_orch.reset_pipeline.assert_not_called()

    @staticmethod
    def test_run_keyboard_interrupt() -> None:
        """Should handle KeyboardInterrupt gracefully."""
        with patch("msc.pipeline.orchestrator.PipelineOrchestrator") as mock_orch_class:
            mock_orch = mock_orch_class.return_value
            mock_orch.run.side_effect = KeyboardInterrupt()

            result = runner.invoke(app, ["run"])

            # Should show interrupted message
            assert result.exit_code == 1
            assert "interrupted by user" in result.stdout
            assert "Checkpoints have been saved" in result.stdout


class TestBillingCommand:
    """Tests for the billing command."""

    @staticmethod
    def test_billing_success() -> None:
        """Should display quota information successfully."""
        # Mock the settings and client
        with patch("msc.cli.get_settings") as mock_settings, \
                patch("msc.clients.songstats.SongstatsClient") as mock_client_class:
            mock_instance = mock_settings.return_value
            mock_instance.get_songstats_key.return_value = "test_key_12345"

            # Mock the client and its get_quota method
            mock_client = Mock()
            mock_client.get_quota.return_value = {
                "requests_used": 100,
                "requests_limit": 1000,
                "reset_date": "2025-01-01",
            }
            mock_client_class.return_value = mock_client

            result = runner.invoke(app, ["billing"])

            assert result.exit_code == 0
            assert "Songstats API Quota" in result.stdout or "100" in result.stdout

    @staticmethod
    def test_billing_missing_api_key() -> None:
        """Should handle missing API key."""
        with patch("msc.cli.get_settings") as mock_settings:
            mock_instance = mock_settings.return_value
            mock_instance.get_songstats_key.side_effect = ValueError("API key not found")

            result = runner.invoke(app, ["billing"])

            assert result.exit_code == 1
            # Error message might be in stderr or stdout
            output = result.stdout + result.stderr
            assert "Error: API key not found" in output or "API key not found" in output


class TestValidateCommand:
    """Tests for the validate command."""

    @staticmethod
    def test_validate_success(tmp_path: Path) -> None:
        """Should validate a valid file successfully."""
        # Create a valid Track JSON file with required fields
        import json
        test_file = tmp_path / "test.json"
        test_data = [{
            "title": "Test Song",
            "artist_list": ["Artist"],
            "year": 2025,
            "genre": [],
            "label": [],
            "grouping": None,
            "search_query": None,
            "songstats_identifiers": {
                "songstats_id": "",
                "songstats_title": "",
                "isrc": None
            }
        }]
        test_file.write_text(json.dumps(test_data), encoding="utf-8")

        result = runner.invoke(app, ["validate", str(test_file)])

        assert result.exit_code == 0
        assert "Validation passed" in result.stdout or "valid" in result.stdout.lower()

    @staticmethod
    def test_validate_file_not_found() -> None:
        """Should handle non-existent file."""
        result = runner.invoke(app, ["validate", "/nonexistent/file.json"])

        assert result.exit_code != 0
        # Typer will show an error about the file not existing


class TestMainCallback:
    """Tests for the main callback (global options)."""

    @staticmethod
    def test_verbose_flag_sets_debug_logging() -> None:
        """Should set DEBUG log level with --verbose."""
        with patch("msc.cli.setup_logging") as mock_setup:
            # Run with verbose flag
            _result = runner.invoke(app, ["--verbose", "init"])

            # Should have called setup_logging with DEBUG
            mock_setup.assert_called_once_with(level="DEBUG")

    @staticmethod
    def test_default_sets_info_logging() -> None:
        """Should set INFO log level by default."""
        with patch("msc.cli.setup_logging") as mock_setup:
            # Run without verbose flag
            _result = runner.invoke(app, ["init"])

            # Should have called setup_logging with INFO
            mock_setup.assert_called_once_with(level="INFO")

    @staticmethod
    def test_help_flag() -> None:
        """Should display help message."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Music Charts" in result.stdout
        assert "Analyze track performance" in result.stdout


class TestDisplaySummaryHelper:
    """Tests for _display_summary helper function."""

    @staticmethod
    def test_display_summary_basic() -> None:
        """Test _display_summary displays basic metrics."""
        from msc.cli import _display_summary
        from msc.models.track import Track
        from msc.models.ranking import PowerRanking, PowerRankingResults, CategoryScore
        from io import StringIO
        import sys

        # Create mock orchestrator with metrics
        mock_orch = Mock()
        mock_orch.get_metrics.return_value = {
            "stages_completed": 3,
            "items_processed": 100,
            "items_failed": 5,
        }
        mock_orch.metrics_observer.get_success_rate.return_value = 95.0
        mock_orch.get_review_queue.return_value = []

        # Create mock results with rankings
        track = Track(title="Test Track", artist_list=["Test Artist"], year=2024)
        ranking = PowerRanking(
            track=track,
            total_score=10.0,
            rank=1,
            category_scores=[CategoryScore(category="popularity", raw_score=0.9, weight=4, weighted_score=3.6)]
        )
        results = PowerRankingResults(rankings=[ranking], year=2024)

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            _display_summary(mock_orch, results)
            output = captured_output.getvalue()

            # Check that summary components are displayed
            assert "Pipeline Summary" in output
            assert "Stages completed:  3" in output
            assert "Items processed:   100" in output
            assert "Items failed:      5" in output
            assert "Success rate:      95.0%" in output
            assert "Top 5 Rankings:" in output
            assert "Pipeline completed successfully!" in output

        finally:
            sys.stdout = sys.__stdout__

    @staticmethod
    def test_display_summary_with_review_queue() -> None:
        """Test _display_summary displays review queue warning."""
        from msc.cli import _display_summary
        from io import StringIO
        import sys

        mock_orch = Mock()
        mock_orch.get_metrics.return_value = {
            "stages_completed": 2,
            "items_processed": 50,
            "items_failed": 10,
        }
        mock_orch.metrics_observer.get_success_rate.return_value = 80.0
        mock_orch.get_review_queue.return_value = [{"track_id": "1"}, {"track_id": "2"}]  # 2 items in queue

        captured_output = StringIO()
        sys.stdout = captured_output

        try:
            _display_summary(mock_orch, None)
            output = captured_output.getvalue()

            # Should show review queue warning
            assert "2 items need manual review" in output
            assert "manual_review.json" in output

        finally:
            sys.stdout = sys.__stdout__


class TestNoArgs:
    """Tests for running without arguments."""

    @staticmethod
    def test_no_args_shows_help() -> None:
        """Should show help when run without arguments."""
        result = runner.invoke(app, [])

        # Typer may return 0 or 2 depending on version, both are acceptable
        assert result.exit_code in (0, 2)
        # Should show help text or command list
        assert "Usage:" in result.stdout or "Music Charts" in result.stdout or "Commands:" in result.stdout
