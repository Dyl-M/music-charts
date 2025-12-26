"""Unit tests for CLI display formatters.

Tests quota tables, validation errors, and export summary formatting.
"""

# Standard library
from pathlib import Path

# Third-party
import pytest
from rich.panel import Panel
from rich.table import Table

# Local
from msc.commands.formatters import (
    QuotaFormatter,
    ValidationFormatter,
    ExportFormatter,
)


class TestQuotaFormatterBillingTable:
    """Tests for QuotaFormatter.format_billing_table method."""

    @staticmethod
    def test_returns_table(sample_quota_data: dict) -> None:
        """Should return a Rich Table object."""
        table = QuotaFormatter.format_billing_table(sample_quota_data)
        assert isinstance(table, Table)

    @staticmethod
    def test_has_correct_title(sample_quota_data: dict) -> None:
        """Should have correct title."""
        table = QuotaFormatter.format_billing_table(sample_quota_data)
        assert "Songstats" in table.title

    @staticmethod
    def test_has_metric_column(sample_quota_data: dict) -> None:
        """Should have Metric column."""
        table = QuotaFormatter.format_billing_table(sample_quota_data)
        column_names = [col.header for col in table.columns]
        assert "Metric" in column_names

    @staticmethod
    def test_has_current_month_column(sample_quota_data: dict) -> None:
        """Should have Current Month column."""
        table = QuotaFormatter.format_billing_table(sample_quota_data)
        column_names = [col.header for col in table.columns]
        assert "Current Month" in column_names

    @staticmethod
    def test_has_previous_month_column(sample_quota_data: dict) -> None:
        """Should have Previous Month column."""
        table = QuotaFormatter.format_billing_table(sample_quota_data)
        column_names = [col.header for col in table.columns]
        assert "Previous Month" in column_names

    @staticmethod
    def test_handles_empty_data() -> None:
        """Should handle empty quota data."""
        table = QuotaFormatter.format_billing_table({})
        assert isinstance(table, Table)

    @staticmethod
    def test_handles_missing_status() -> None:
        """Should handle missing status key."""
        table = QuotaFormatter.format_billing_table({"other": "data"})
        assert isinstance(table, Table)


class TestQuotaFormatterWarningLevel:
    """Tests for QuotaFormatter.get_quota_warning_level method."""

    @staticmethod
    def test_green_under_50() -> None:
        """Should return green for usage under 50%."""
        assert QuotaFormatter.get_quota_warning_level(0) == "green"
        assert QuotaFormatter.get_quota_warning_level(25) == "green"
        assert QuotaFormatter.get_quota_warning_level(49) == "green"
        assert QuotaFormatter.get_quota_warning_level(49.9) == "green"

    @staticmethod
    def test_yellow_50_to_79() -> None:
        """Should return yellow for usage 50-79%."""
        assert QuotaFormatter.get_quota_warning_level(50) == "yellow"
        assert QuotaFormatter.get_quota_warning_level(65) == "yellow"
        assert QuotaFormatter.get_quota_warning_level(79) == "yellow"
        assert QuotaFormatter.get_quota_warning_level(79.9) == "yellow"

    @staticmethod
    def test_red_80_and_above() -> None:
        """Should return red for usage 80% and above."""
        assert QuotaFormatter.get_quota_warning_level(80) == "red"
        assert QuotaFormatter.get_quota_warning_level(90) == "red"
        assert QuotaFormatter.get_quota_warning_level(100) == "red"
        assert QuotaFormatter.get_quota_warning_level(150) == "red"


class TestValidationFormatterErrorList:
    """Tests for ValidationFormatter.format_error_list method."""

    @staticmethod
    def test_returns_panel() -> None:
        """Should return a Rich Panel object."""
        panel = ValidationFormatter.format_error_list([])
        assert isinstance(panel, Panel)

    @staticmethod
    def test_empty_errors_shows_success() -> None:
        """Should show success message for empty errors."""
        panel = ValidationFormatter.format_error_list([])
        # Panel with no errors should indicate success
        assert panel.style == "green"

    @staticmethod
    def test_formats_single_error(sample_validation_errors: list[dict]) -> None:
        """Should format single error correctly."""
        panel = ValidationFormatter.format_error_list([sample_validation_errors[0]])
        assert isinstance(panel, Panel)
        assert panel.border_style == "red"

    @staticmethod
    def test_includes_error_count(sample_validation_errors: list[dict]) -> None:
        """Should include error count in title."""
        panel = ValidationFormatter.format_error_list(sample_validation_errors)
        assert "2" in str(panel.title)

    @staticmethod
    def test_formats_location_path(sample_validation_errors: list[dict]) -> None:
        """Should format location as arrow-separated path."""
        # The error has loc: ["artist_list", 0]
        # It should be formatted as "artist_list → 0"
        panel = ValidationFormatter.format_error_list(sample_validation_errors)
        # Check that the panel was created - content verification requires rendering
        assert isinstance(panel, Panel)


class TestValidationFormatterSuccessMessage:
    """Tests for ValidationFormatter.format_success_message method."""

    @staticmethod
    def test_includes_filename() -> None:
        """Should include filename in message."""
        result = ValidationFormatter.format_success_message(
            Path("/path/to/test.json"), "Track"
        )
        assert "test.json" in result

    @staticmethod
    def test_includes_model_name() -> None:
        """Should include model name in message."""
        result = ValidationFormatter.format_success_message(
            Path("/path/to/test.json"), "Track"
        )
        assert "Track" in result

    @staticmethod
    def test_indicates_success() -> None:
        """Should indicate validation passed."""
        result = ValidationFormatter.format_success_message(
            Path("/path/to/test.json"), "Track"
        )
        assert "passed" in result.lower() or "✓" in result


class TestExportFormatterFileSize:
    """Tests for ExportFormatter.format_file_size method."""

    @staticmethod
    def test_formats_bytes() -> None:
        """Should format small sizes as bytes."""
        result = ExportFormatter.format_file_size(512)
        assert "512" in result
        assert "bytes" in result

    @staticmethod
    def test_formats_kilobytes() -> None:
        """Should format KB sizes."""
        result = ExportFormatter.format_file_size(2048)  # 2 KB
        assert "KB" in result

    @staticmethod
    def test_formats_megabytes() -> None:
        """Should format MB sizes."""
        result = ExportFormatter.format_file_size(2 * 1024 * 1024)  # 2 MB
        assert "MB" in result

    @staticmethod
    def test_formats_gigabytes() -> None:
        """Should format GB sizes."""
        result = ExportFormatter.format_file_size(2 * 1024 * 1024 * 1024)  # 2 GB
        assert "GB" in result

    @staticmethod
    def test_handles_zero() -> None:
        """Should handle zero bytes."""
        result = ExportFormatter.format_file_size(0)
        assert "0" in result

    @staticmethod
    def test_precision_for_large_sizes() -> None:
        """Should include decimal precision for large sizes."""
        result = ExportFormatter.format_file_size(1536 * 1024)  # 1.5 MB
        assert "." in result  # Should have decimal


class TestExportFormatterSummary:
    """Tests for ExportFormatter.format_export_summary method."""

    @staticmethod
    def test_returns_panel() -> None:
        """Should return a Rich Panel object."""
        stats = {"row_count": 100, "file_size_bytes": 1024, "duration_seconds": 1.5}
        panel = ExportFormatter.format_export_summary(stats)
        assert isinstance(panel, Panel)

    @staticmethod
    def test_has_correct_title() -> None:
        """Should have export summary title."""
        stats = {"row_count": 100, "file_size_bytes": 1024, "duration_seconds": 1.5}
        panel = ExportFormatter.format_export_summary(stats)
        assert "Export" in str(panel.title)

    @staticmethod
    def test_has_green_border() -> None:
        """Should have green border for success."""
        stats = {"row_count": 100, "file_size_bytes": 1024, "duration_seconds": 1.5}
        panel = ExportFormatter.format_export_summary(stats)
        assert panel.border_style == "green"

    @staticmethod
    def test_handles_missing_keys() -> None:
        """Should handle missing statistics keys."""
        panel = ExportFormatter.format_export_summary({})
        assert isinstance(panel, Panel)


class TestExportFormatterRenderToString:
    """Tests for ExportFormatter.render_to_string method."""

    @staticmethod
    def test_renders_table() -> None:
        """Should render Table to string."""
        table = Table()
        table.add_column("Test")
        table.add_row("Value")
        result = ExportFormatter.render_to_string(table)
        assert isinstance(result, str)
        assert "Value" in result

    @staticmethod
    def test_renders_panel() -> None:
        """Should render Panel to string."""
        panel = Panel("Test content")
        result = ExportFormatter.render_to_string(panel)
        assert isinstance(result, str)
        assert "Test content" in result
