"""Unit tests for CLI exporters module."""

# Standard library
from pathlib import Path
from unittest.mock import Mock

# Third-party
import pytest

# Local
from msc.commands.exporters import DataExporter, ExportResult
from msc.models.stats import TrackWithStats
from msc.models.track import Track, SongstatsIdentifiers
from msc.storage.json_repository import JSONStatsRepository


class TestExportResult:
    """Tests for ExportResult dataclass."""

    @staticmethod
    def test_create_export_result() -> None:
        """Should create export result."""
        result = ExportResult(
            success=True,
            file_path=Path("output.csv"),
            row_count=100,
            file_size_bytes=2048,
            duration_seconds=1.5,
        )

        assert result.success is True
        assert result.row_count == 100
        assert result.file_size_bytes == 2048
        assert result.duration_seconds == 1.5

    @staticmethod
    def test_export_result_frozen() -> None:
        """Should be immutable (frozen dataclass)."""
        result = ExportResult(
            success=True,
            file_path=Path("output.csv"),
            row_count=100,
            file_size_bytes=2048,
            duration_seconds=1.5,
        )

        with pytest.raises(AttributeError):
            setattr(result, "success", False)


class TestDataExporterCSV:
    """Tests for CSV export."""

    @staticmethod
    def test_export_csv_success(tmp_path: Path) -> None:
        """Should export data to CSV successfully."""
        # Create mock repository with test data
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test Song", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        # Export to CSV
        output_file = tmp_path / "output.csv"
        exporter = DataExporter(mock_repo)
        result = exporter.export_csv(output_file)

        assert result.success is True
        assert result.row_count == 1
        assert result.file_path == output_file
        assert output_file.exists()

    @staticmethod
    def test_export_csv_empty_repository(tmp_path: Path) -> None:
        """Should raise ValueError for empty repository."""
        mock_repo = Mock(spec=JSONStatsRepository)
        mock_repo.get_all.return_value = []

        output_file = tmp_path / "output.csv"
        exporter = DataExporter(mock_repo)

        with pytest.raises(ValueError, match="Repository is empty"):
            exporter.export_csv(output_file)

    @staticmethod
    def test_export_csv_creates_parent_dirs(tmp_path: Path) -> None:
        """Should create parent directories if they don't exist."""
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        # Output to nested directory that doesn't exist
        output_file = tmp_path / "nested" / "dir" / "output.csv"
        exporter = DataExporter(mock_repo)
        result = exporter.export_csv(output_file)

        assert result.success is True
        assert output_file.exists()


class TestDataExporterODS:
    """Tests for ODS (LibreOffice) export."""

    @staticmethod
    def test_export_ods_success(tmp_path: Path) -> None:
        """Should export data to ODS successfully."""
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test Song", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        output_file = tmp_path / "output.ods"
        exporter = DataExporter(mock_repo)
        result = exporter.export_ods(output_file)

        assert result.success is True
        assert result.row_count == 1
        assert output_file.exists()

    @staticmethod
    def test_export_ods_empty_repository(tmp_path: Path) -> None:
        """Should raise ValueError for empty repository."""
        mock_repo = Mock(spec=JSONStatsRepository)
        mock_repo.get_all.return_value = []

        output_file = tmp_path / "output.ods"
        exporter = DataExporter(mock_repo)

        with pytest.raises(ValueError, match="Repository is empty"):
            exporter.export_ods(output_file)

    @staticmethod
    def test_export_ods_custom_sheet_name(tmp_path: Path) -> None:
        """Should allow custom sheet name."""
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        output_file = tmp_path / "output.ods"
        exporter = DataExporter(mock_repo)
        result = exporter.export_ods(output_file, sheet_name="MyData")

        assert result.success is True
        assert output_file.exists()


class TestDataExporterHTML:
    """Tests for HTML export."""

    @staticmethod
    def test_export_html_success(tmp_path: Path) -> None:
        """Should export data to HTML successfully."""
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test Song", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        output_file = tmp_path / "output.html"
        exporter = DataExporter(mock_repo)
        result = exporter.export_html(output_file)

        assert result.success is True
        assert result.row_count == 1
        assert output_file.exists()

        # Check HTML content
        content = output_file.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert "test123" in content  # songstats_id is in flat export

    @staticmethod
    def test_export_html_empty_repository(tmp_path: Path) -> None:
        """Should raise ValueError for empty repository."""
        mock_repo = Mock(spec=JSONStatsRepository)
        mock_repo.get_all.return_value = []

        output_file = tmp_path / "output.html"
        exporter = DataExporter(mock_repo)

        with pytest.raises(ValueError, match="Repository is empty"):
            exporter.export_html(output_file)

    @staticmethod
    def test_export_html_custom_title(tmp_path: Path) -> None:
        """Should allow custom HTML title."""
        mock_repo = Mock(spec=JSONStatsRepository)
        track = TrackWithStats(
            track=Track(title="Test", artist_list=["Artist"], year=2025),
            songstats_identifiers=SongstatsIdentifiers(songstats_id="test123", songstats_title="Test"),
        )
        mock_repo.get_all.return_value = [track]

        output_file = tmp_path / "output.html"
        exporter = DataExporter(mock_repo)
        result = exporter.export_html(output_file, title="My Custom Title")

        assert result.success is True

        content = output_file.read_text(encoding="utf-8")
        assert "My Custom Title" in content
