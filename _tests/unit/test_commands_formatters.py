"""Unit tests for CLI formatters module."""

# Standard library
from pathlib import Path

# Third-party
import pytest
from rich.panel import Panel
from rich.table import Table

# Local
from msc.commands.formatters import ExportFormatter, QuotaFormatter, ValidationFormatter


class TestQuotaFormatter:
    """Tests for quota/billing display formatting."""

    @staticmethod
    def test_format_billing_table_basic() -> None:
        """Should create table with quota information."""
        quota_data = {
            "requests_used": 100,
            "requests_limit": 1000,
            "reset_date": "2025-01-01",
        }

        table = QuotaFormatter.format_billing_table(quota_data)

        assert isinstance(table, Table)
        assert table.title == "🎵 Songstats API Quota"

    @staticmethod
    def test_format_billing_table_zero_limit() -> None:
        """Should handle zero limit gracefully."""
        quota_data = {
            "requests_used": 100,
            "requests_limit": 0,
            "reset_date": "2025-01-01",
        }

        table = QuotaFormatter.format_billing_table(quota_data)

        assert isinstance(table, Table)
        # Should not crash with division by zero

    @staticmethod
    def test_format_billing_table_missing_data() -> None:
        """Should use defaults for missing data."""
        quota_data = {}

        table = QuotaFormatter.format_billing_table(quota_data)

        assert isinstance(table, Table)

    @staticmethod
    def test_get_quota_warning_level_green() -> None:
        """Should return green for low usage."""
        assert QuotaFormatter.get_quota_warning_level(0.0) == "green"
        assert QuotaFormatter.get_quota_warning_level(49.9) == "green"

    @staticmethod
    def test_get_quota_warning_level_yellow() -> None:
        """Should return yellow for medium usage."""
        assert QuotaFormatter.get_quota_warning_level(50.0) == "yellow"
        assert QuotaFormatter.get_quota_warning_level(79.9) == "yellow"

    @staticmethod
    def test_get_quota_warning_level_red() -> None:
        """Should return red for high usage."""
        assert QuotaFormatter.get_quota_warning_level(80.0) == "red"
        assert QuotaFormatter.get_quota_warning_level(100.0) == "red"


class TestValidationFormatter:
    """Tests for validation error formatting."""

    @staticmethod
    def test_format_error_list_with_errors() -> None:
        """Should format validation errors as panel."""
        errors = [
            {"loc": ["field1"], "msg": "Error 1", "type": "value_error"},
            {"loc": ["field2", "nested"], "msg": "Error 2", "type": "type_error"},
        ]

        panel = ValidationFormatter.format_error_list(errors)

        assert isinstance(panel, Panel)
        assert "2 found" in str(panel.title)

    @staticmethod
    def test_format_error_list_empty() -> None:
        """Should handle empty error list."""
        panel = ValidationFormatter.format_error_list([])

        assert isinstance(panel, Panel)

    @staticmethod
    def test_format_success_message() -> None:
        """Should format success message."""
        message = ValidationFormatter.format_success_message(
            Path("test.json"), "Track"
        )

        assert "Validation passed" in message
        assert "test.json" in message
        assert "Track" in message


class TestExportFormatter:
    """Tests for export summary formatting."""

    @staticmethod
    def test_format_file_size_bytes() -> None:
        """Should format bytes correctly."""
        assert ExportFormatter.format_file_size(512) == "512 bytes"
        assert ExportFormatter.format_file_size(1023) == "1023 bytes"

    @staticmethod
    def test_format_file_size_kb() -> None:
        """Should format KB correctly."""
        assert ExportFormatter.format_file_size(1024) == "1.00 KB"
        assert ExportFormatter.format_file_size(2048) == "2.00 KB"

    @staticmethod
    def test_format_file_size_mb() -> None:
        """Should format MB correctly."""
        assert ExportFormatter.format_file_size(1024 * 1024) == "1.00 MB"
        assert ExportFormatter.format_file_size(1024 * 1024 * 2) == "2.00 MB"

    @staticmethod
    def test_format_file_size_gb() -> None:
        """Should format GB correctly."""
        assert ExportFormatter.format_file_size(1024 ** 3) == "1.00 GB"
        assert ExportFormatter.format_file_size(1024 ** 3 * 2) == "2.00 GB"

    @staticmethod
    def test_format_export_summary() -> None:
        """Should format export statistics as panel."""
        stats = {
            "row_count": 100,
            "file_size_bytes": 2048,
            "duration_seconds": 1.5,
        }

        panel = ExportFormatter.format_export_summary(stats)

        assert isinstance(panel, Panel)
        assert "Export Summary" in str(panel.title)

    @staticmethod
    def test_format_export_summary_missing_data() -> None:
        """Should handle missing statistics."""
        stats = {}

        panel = ExportFormatter.format_export_summary(stats)

        assert isinstance(panel, Panel)

    @staticmethod
    def test_render_to_string_table() -> None:
        """Should render table to string."""
        table = Table(title="Test Table")
        table.add_column("Col1")
        table.add_row("Value1")

        result = ExportFormatter.render_to_string(table)

        assert isinstance(result, str)
        assert "Test Table" in result

    @staticmethod
    def test_render_to_string_panel() -> None:
        """Should render panel to string."""
        panel = Panel("Test content", title="Test Panel")

        result = ExportFormatter.render_to_string(panel)

        assert isinstance(result, str)
        assert "Test content" in result
