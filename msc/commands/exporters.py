"""Export utilities for rankings and track data.

Provides adapters for exporting data to CSV, ODS (LibreOffice), and HTML formats
with proper error handling and statistics collection.
"""

# Standard library
import time
from dataclasses import dataclass
from pathlib import Path

# Third-party
import pandas as pd

# Local
from msc.storage.json_repository import JSONStatsRepository


@dataclass(frozen=True)
class ExportResult:
    """Immutable export operation result.

    Attributes:
        success: Whether export completed successfully
        file_path: Path to exported file
        row_count: Number of rows exported
        file_size_bytes: Size of output file in bytes
        duration_seconds: Time taken for export operation
    """
    success: bool
    file_path: Path
    row_count: int
    file_size_bytes: int
    duration_seconds: float


class DataExporter:
    """Adapter for exporting track and statistics data to various formats.

    Integrates with JSONStatsRepository to load data and export to
    CSV, ODS (LibreOffice), or HTML formats using pandas.
    """

    def __init__(self, repository: JSONStatsRepository) -> None:
        """Initialize exporter with data repository.

        Args:
            repository: Repository containing track/stats data
        """
        self.repository = repository

    def export_csv(self, output_path: Path, flat: bool = True) -> ExportResult:
        """Export data to CSV format.

        Args:
            output_path: Path for output CSV file
            flat: Whether to flatten nested structures (default True)

        Returns:
            ExportResult with export statistics

        Raises:
            ValueError: If repository is empty
        """
        start_time = time.time()

        # Load data
        data = self.repository.get_all()
        if not data:
            raise ValueError("Repository is empty - no data to export")

        # Convert to DataFrame
        df = self._to_dataframe(data, flat=flat)

        # Write CSV
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding="utf-8")

        # Calculate statistics
        duration = time.time() - start_time
        file_size = output_path.stat().st_size

        return ExportResult(
            success=True,
            file_path=output_path,
            row_count=len(df),
            file_size_bytes=file_size,
            duration_seconds=duration,
        )

    def export_ods(
            self,
            output_path: Path,
            flat: bool = True,
            sheet_name: str = "Rankings",
    ) -> ExportResult:
        """Export data to ODS (LibreOffice) format.

        Args:
            output_path: Path for output ODS file
            flat: Whether to flatten nested structures (default True)
            sheet_name: Name for spreadsheet sheet (default "Rankings")

        Returns:
            ExportResult with export statistics

        Raises:
            ValueError: If repository is empty
            ImportError: If odfpy package is not installed
        """
        start_time = time.time()

        # Load data
        data = self.repository.get_all()
        if not data:
            raise ValueError("Repository is empty - no data to export")

        # Convert to DataFrame
        df = self._to_dataframe(data, flat=flat)

        # Write ODS
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            df.to_excel(output_path, index=False, sheet_name=sheet_name, engine="odf")
        except ImportError as e:
            raise ImportError(
                "ODS export requires the 'odfpy' package. "
                "Install it with: pip install odfpy"
            ) from e

        # Calculate statistics
        duration = time.time() - start_time
        file_size = output_path.stat().st_size

        return ExportResult(
            success=True,
            file_path=output_path,
            row_count=len(df),
            file_size_bytes=file_size,
            duration_seconds=duration,
        )

    def export_html(
            self,
            output_path: Path,
            flat: bool = True,
            title: str = "Music Charts Export",
    ) -> ExportResult:
        """Export data to interactive HTML table.

        Args:
            output_path: Path for output HTML file
            flat: Whether to flatten nested structures (default True)
            title: Title for HTML page (default "Music Charts Export")

        Returns:
            ExportResult with export statistics

        Raises:
            ValueError: If repository is empty
        """
        start_time = time.time()

        # Load data
        data = self.repository.get_all()
        if not data:
            raise ValueError("Repository is empty - no data to export")

        # Convert to DataFrame
        df = self._to_dataframe(data, flat=flat)

        # Write HTML with styling
        output_path.parent.mkdir(parents=True, exist_ok=True)
        html = df.to_html(index=False, classes="table table-striped", border=0)

        # Wrap in HTML template
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        h1 {{
            color: #333;
        }}
        table {{
            width: 100%;
            background-color: white;
            border-collapse: collapse;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f2f2f2;
        }}
    </style>
</head>
<body>
    <h1>{title}</h1>
    <p>Total rows: {len(df)}</p>
    {html}
</body>
</html>
        """.strip()

        output_path.write_text(full_html, encoding="utf-8")

        # Calculate statistics
        duration = time.time() - start_time
        file_size = output_path.stat().st_size

        return ExportResult(
            success=True,
            file_path=output_path,
            row_count=len(df),
            file_size_bytes=file_size,
            duration_seconds=duration,
        )

    @staticmethod
    def _to_dataframe(data: list, flat: bool = True) -> pd.DataFrame:
        """Convert track data to pandas DataFrame.

        Args:
            data: List of TrackWithStats objects
            flat: Whether to flatten nested structures

        Returns:
            pandas DataFrame with track data
        """
        if flat:
            # Use model's to_flat_dict() method for flattening
            rows = [item.to_flat_dict() for item in data]

        else:
            # Use model_dump() for nested structure
            rows = [item.model_dump() for item in data]

        return pd.DataFrame(rows)
