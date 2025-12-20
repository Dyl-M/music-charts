"""Unit tests for CLI commands."""

# Standard library
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest
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


class TestBillingCommand:
    """Tests for the billing command."""

    @staticmethod
    def test_billing_not_implemented() -> None:
        """Should raise NotImplementedError after loading key."""
        # Mock the API key loading
        with patch("msc.cli.get_settings") as mock_settings:
            mock_instance = mock_settings.return_value
            mock_instance.get_songstats_key.return_value = "test_key_12345"

            with pytest.raises(NotImplementedError, match="Billing check not yet implemented"):
                runner.invoke(app, ["billing"], catch_exceptions=False)

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
    def test_validate_not_implemented(tmp_path: Path) -> None:
        """Should raise NotImplementedError."""
        # Create a test file
        test_file = tmp_path / "test.json"
        test_file.write_text('{"test": "data"}', encoding="utf-8")

        with pytest.raises(NotImplementedError, match="Schema validation not yet implemented"):
            runner.invoke(app, ["validate", str(test_file)], catch_exceptions=False)

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
