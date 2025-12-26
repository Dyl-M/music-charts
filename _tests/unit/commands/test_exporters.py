"""Unit tests for data export utilities.

Tests CSV, ODS, and HTML export functionality.
"""

# Standard library
from pathlib import Path
from unittest.mock import MagicMock

# Third-party
import pytest

# Local
from msc.commands.exporters import ExportResult, DataExporter


class TestExportResult:
    """Tests for ExportResult dataclass."""

    @staticmethod
    def test_creates_successful_result() -> None:
        """Should create successful export result."""
        result = ExportResult(
            success=True,
            file_path=Path("output.csv"),
            row_count=100,
            file_size_bytes=1024,
            duration_seconds=0.5,
        )
        assert result.success is True
        assert result.row_count == 100
        assert result.file_size_bytes == 1024

    @staticmethod
    def test_is_frozen() -> None:
        """Should be immutable."""
        result = ExportResult(
            success=True,
            file_path=Path("output.csv"),
            row_count=100,
            file_size_bytes=1024,
            duration_seconds=0.5,
        )
        with pytest.raises(AttributeError):
            # noinspection PyDataclass
            result.success = False


class TestDataExporterInit:
    """Tests for DataExporter initialization."""

    @staticmethod
    def test_stores_repository(mock_stats_repository: MagicMock) -> None:
        """Should store repository reference."""
        exporter = DataExporter(mock_stats_repository)
        assert exporter.repository is mock_stats_repository


class TestDataExporterExportCsv:
    """Tests for DataExporter.export_csv method."""

    @staticmethod
    def test_creates_csv_file(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should create CSV file."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.csv"

        exporter = DataExporter(mock_stats_repository)
        result = exporter.export_csv(output_path)

        assert output_path.exists()
        assert result.success is True

    @staticmethod
    def test_returns_export_result(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should return ExportResult with statistics."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.csv"

        exporter = DataExporter(mock_stats_repository)
        result = exporter.export_csv(output_path)

        assert isinstance(result, ExportResult)
        assert result.row_count == len(sample_tracks_with_stats)
        assert result.file_size_bytes > 0
        assert result.duration_seconds >= 0

    @staticmethod
    def test_raises_for_empty_repository(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
    ) -> None:
        """Should raise ValueError for empty repository."""
        mock_stats_repository.get_all.return_value = []
        output_path = tmp_path / "export.csv"

        exporter = DataExporter(mock_stats_repository)
        with pytest.raises(ValueError, match="empty"):
            exporter.export_csv(output_path)

    @staticmethod
    def test_creates_parent_directory(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should create parent directory if needed."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "nested" / "dir" / "export.csv"

        exporter = DataExporter(mock_stats_repository)
        exporter.export_csv(output_path)

        assert output_path.exists()

    @staticmethod
    def test_csv_contains_headers(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should include column headers in CSV."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.csv"

        exporter = DataExporter(mock_stats_repository)
        exporter.export_csv(output_path)

        content = output_path.read_text(encoding="utf-8")
        # Should have header row with field names
        first_line = content.split("\n")[0]
        assert "," in first_line  # CSV format


class TestDataExporterExportOds:
    """Tests for DataExporter.export_ods method."""

    @staticmethod
    def test_raises_for_empty_repository(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
    ) -> None:
        """Should raise ValueError for empty repository."""
        mock_stats_repository.get_all.return_value = []
        output_path = tmp_path / "export.ods"

        exporter = DataExporter(mock_stats_repository)
        with pytest.raises(ValueError, match="empty"):
            exporter.export_ods(output_path)

    @staticmethod
    def test_creates_parent_directory(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should create parent directory if needed."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "nested" / "export.ods"

        exporter = DataExporter(mock_stats_repository)
        try:
            exporter.export_ods(output_path)
            assert output_path.parent.exists()
        except ImportError:
            # odfpy not installed, skip test
            pytest.skip("odfpy package not installed")


class TestDataExporterExportHtml:
    """Tests for DataExporter.export_html method."""

    @staticmethod
    def test_creates_html_file(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should create HTML file."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.html"

        exporter = DataExporter(mock_stats_repository)
        result = exporter.export_html(output_path)

        assert output_path.exists()
        assert result.success is True

    @staticmethod
    def test_html_has_valid_structure(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should create valid HTML structure."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.html"

        exporter = DataExporter(mock_stats_repository)
        exporter.export_html(output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "<html>" in content
        assert "</html>" in content
        assert "<table" in content

    @staticmethod
    def test_html_includes_custom_title(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should include custom title in HTML."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.html"

        exporter = DataExporter(mock_stats_repository)
        exporter.export_html(output_path, title="Custom Title")

        content = output_path.read_text(encoding="utf-8")
        assert "Custom Title" in content

    @staticmethod
    def test_html_includes_row_count(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
            sample_tracks_with_stats: list,
    ) -> None:
        """Should include row count in HTML."""
        mock_stats_repository.get_all.return_value = sample_tracks_with_stats
        output_path = tmp_path / "export.html"

        exporter = DataExporter(mock_stats_repository)
        exporter.export_html(output_path)

        content = output_path.read_text(encoding="utf-8")
        assert "Total rows:" in content

    @staticmethod
    def test_raises_for_empty_repository(
            tmp_path: Path,
            mock_stats_repository: MagicMock,
    ) -> None:
        """Should raise ValueError for empty repository."""
        mock_stats_repository.get_all.return_value = []
        output_path = tmp_path / "export.html"

        exporter = DataExporter(mock_stats_repository)
        with pytest.raises(ValueError, match="empty"):
            exporter.export_html(output_path)


class TestDataExporterToDataframe:
    """Tests for DataExporter._to_dataframe method."""

    @staticmethod
    def test_creates_dataframe(sample_tracks_with_stats: list) -> None:
        """Should create pandas DataFrame."""
        import pandas as pd

        df = DataExporter._to_dataframe(sample_tracks_with_stats)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == len(sample_tracks_with_stats)

    @staticmethod
    def test_flat_mode_uses_flat_dict(sample_tracks_with_stats: list) -> None:
        """Should use to_flat_dict in flat mode."""
        df = DataExporter._to_dataframe(sample_tracks_with_stats, flat=True)
        # Flat dict should have flattened column names
        assert len(df.columns) > 0

    @staticmethod
    def test_non_flat_mode_uses_model_dump(sample_tracks_with_stats: list) -> None:
        """Should use model_dump in non-flat mode."""
        df = DataExporter._to_dataframe(sample_tracks_with_stats, flat=False)
        assert len(df.columns) > 0
