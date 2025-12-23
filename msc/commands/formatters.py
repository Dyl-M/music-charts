"""Display formatting utilities for CLI output.

Provides formatters for quota tables, validation errors, and export summaries
using rich library components for professional terminal output.
"""

# Standard library
from pathlib import Path
from typing import Any, Union

# Third-party
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class QuotaFormatter:
    """Formatter for API quota and billing information."""

    @staticmethod
    def format_billing_table(quota_data: dict[str, Any]) -> Table:
        """Create rich table for Songstats quota display.

        Args:
            quota_data: Dictionary with quota information:
                - requests_used: Number of requests consumed
                - requests_limit: Total monthly quota
                - reset_date: Next billing cycle date

        Returns:
            Rich Table object with formatted quota data
        """
        table = Table(title="🎵 Songstats API Quota", show_header=True)

        table.add_column("Metric", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        # Extract quota data
        requests_used = quota_data.get("requests_used", 0)
        requests_limit = quota_data.get("requests_limit", 0)
        reset_date = quota_data.get("reset_date", "Unknown")

        # Calculate usage percentage and remaining
        if requests_limit > 0:
            usage_pct = (requests_used / requests_limit) * 100
            remaining = requests_limit - requests_used

        else:
            usage_pct = 0.0
            remaining = 0

        # Determine color based on usage
        usage_color = QuotaFormatter.get_quota_warning_level(usage_pct)

        # Add rows
        table.add_row("Requests Used", f"{requests_used:,}")
        table.add_row("Requests Limit", f"{requests_limit:,}")
        table.add_row("Remaining", f"{remaining:,}")
        table.add_row("Usage", f"[{usage_color}]{usage_pct:.1f}%[/{usage_color}]")
        table.add_row("Resets On", reset_date)

        return table

    @staticmethod
    def get_quota_warning_level(usage_pct: float) -> str:
        """Return color code based on quota usage percentage.

        Args:
            usage_pct: Usage percentage (0-100)

        Returns:
            Color name for rich styling:
            - 'green' if usage < 50%
            - 'yellow' if usage 50-79%
            - 'red' if usage >= 80%
        """
        if usage_pct < 50:
            return "green"

        if usage_pct < 80:
            return "yellow"

        return "red"


class ValidationFormatter:
    """Formatter for file validation results."""

    @staticmethod
    def format_error_list(errors: list[dict[str, Any]]) -> Panel:
        """Format Pydantic validation errors as rich panel.

        Args:
            errors: List of error dictionaries with:
                - loc: Location of error (field path)
                - msg: Error message
                - type: Error type

        Returns:
            Rich Panel with formatted errors
        """
        if not errors:
            return Panel("No errors found", style="green")

        error_lines = []
        for i, error in enumerate(errors, 1):
            loc = " → ".join(str(x) for x in error.get("loc", []))
            msg = error.get("msg", "Unknown error")
            error_lines.append(f"[red]{i}.[/red] [yellow]{loc}[/yellow]: {msg}")

        content = "\n".join(error_lines)
        return Panel(
            content,
            title=f"❌ Validation Errors ({len(errors)} found)",
            border_style="red",
        )

    @staticmethod
    def format_success_message(file_path: Path, model_name: str) -> str:
        """Format success message for valid files.

        Args:
            file_path: Path to validated file
            model_name: Name of model that validated successfully

        Returns:
            Formatted success message
        """
        return f"✓ [green]Validation passed[/green]: {file_path.name} is a valid {model_name} file"


class ExportFormatter:
    """Formatter for export operation summaries."""

    # File size formatting rules: (threshold, divisor, unit, precision)
    # Checked in order from largest to smallest
    _SIZE_UNITS: list[tuple[int, int, str, int]] = [
        (1024 ** 3, 1024 ** 3, "GB", 2),  # >= 1 GB
        (1024 ** 2, 1024 ** 2, "MB", 2),  # >= 1 MB
        (1024, 1024, "KB", 2),  # >= 1 KB
        (0, 1, "bytes", 0),  # < 1 KB
    ]

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format byte size as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 GB", "234.56 KB", "512 bytes")
        """
        for threshold, divisor, unit, precision in ExportFormatter._SIZE_UNITS:
            if size_bytes >= threshold:
                value = size_bytes / divisor
                return f"{value:.{precision}f} {unit}"

        # Fallback (should never reach here due to final rule with threshold=0)
        return f"{size_bytes} bytes"

    @staticmethod
    def format_export_summary(stats: dict[str, int | float]) -> Panel:
        """Display export statistics as rich panel.

        Args:
            stats: Dictionary with export statistics:
                - row_count: Number of rows exported
                - file_size_bytes: Size of output file
                - duration_seconds: Time taken for export

        Returns:
            Rich Panel with formatted statistics
        """
        row_count = stats.get("row_count", 0)
        file_size = stats.get("file_size_bytes", 0)
        duration = stats.get("duration_seconds", 0.0)

        # Format file size using helper method
        size_str = ExportFormatter.format_file_size(file_size)

        content = f"""
[cyan]Rows Exported:[/cyan] {row_count:,}
[cyan]File Size:[/cyan] {size_str}
[cyan]Duration:[/cyan] {duration:.2f}s
        """.strip()

        return Panel(
            content,
            title="📊 Export Summary",
            border_style="green",
        )

    @staticmethod
    def render_to_string(renderable: Union[Table, Panel]) -> str:
        """Render a rich object to a string for testing or capture.

        Args:
            renderable: Rich Table or Panel object

        Returns:
            Rendered string output
        """
        console = Console()
        with console.capture() as capture:
            console.print(renderable)
        return capture.get()
