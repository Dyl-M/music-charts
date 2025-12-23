"""Command-line interface for the Music Charts pipeline."""

# Standard library
from pathlib import Path
from typing import Annotated, Literal

# Third-party
import typer

# Local
from msc import __version__
from msc.commands.cache import CacheManager
from msc.commands.errors import ErrorHandler, NetworkError
from msc.commands.exporters import DataExporter
from msc.commands.formatters import ExportFormatter, QuotaFormatter, ValidationFormatter
from msc.commands.validators import FileValidator
from msc.config.settings import get_settings
from msc.utils.logging import setup_logging

app = typer.Typer(
    name="msc",
    help="Music Charts - Analyze track performance across streaming platforms",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"msc version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
        _version: Annotated[
            bool,
            typer.Option(
                "--version",
                "-v",
                help="Show version and exit.",
                callback=version_callback,
                is_eager=True,
            ),
        ] = False,
        verbose: Annotated[
            bool,
            typer.Option(
                "--verbose",
                "-V",
                help="Enable verbose output.",
            ),
        ] = False,
) -> None:
    """Music Charts CLI - Analyze track performance across streaming platforms."""
    log_level: Literal["DEBUG", "INFO"] = "DEBUG" if verbose else "INFO"
    setup_logging(level=log_level)


def _determine_stages(stages: list[str] | None) -> tuple[bool, bool, bool]:
    """Determine which pipeline stages to run.

    Args:
        stages: List of stage names or None

    Returns:
        Tuple of (run_extraction, run_enrichment, run_ranking)
    """
    if stages is None:
        stages = ["all"]

    run_all = "all" in stages
    run_extraction = run_all or "extract" in stages
    run_enrichment = run_all or "enrich" in stages
    run_ranking = run_all or "rank" in stages

    return run_extraction, run_enrichment, run_ranking


def _display_pipeline_config(
        year: int,
        run_extraction: bool,
        run_enrichment: bool,
        run_ranking: bool,
        no_youtube: bool,
) -> None:
    """Display pipeline configuration.

    Args:
        year: Target year
        run_extraction: Whether extraction stage is enabled
        run_enrichment: Whether enrichment stage is enabled
        run_ranking: Whether ranking stage is enabled
        no_youtube: Whether YouTube enrichment is disabled
    """
    typer.echo(f"🎵 Music Charts Pipeline - Year {year}\n")
    typer.echo("Pipeline stages:")
    typer.echo(f"  • Extraction:  {'✓' if run_extraction else '✗'}")
    typer.echo(f"  • Enrichment:  {'✓' if run_enrichment else '✗'}")
    typer.echo(f"  • Ranking:     {'✓' if run_ranking else '✗'}")
    typer.echo(f"  • YouTube:     {'✗ (disabled)' if no_youtube else '✓'}\n")


def _display_summary(orchestrator, results) -> None:
    """Display pipeline execution summary.

    Args:
        orchestrator: Pipeline orchestrator instance
        results: Pipeline execution results
    """
    settings = get_settings()
    metrics = orchestrator.get_metrics()

    typer.echo("")
    typer.echo("=" * 60)
    typer.echo("Pipeline Summary")
    typer.echo("=" * 60)
    typer.echo(f"Stages completed:  {metrics.get('stages_completed', 0)}")
    typer.echo(f"Items processed:   {metrics.get('items_processed', 0)}")
    typer.echo(f"Items failed:      {metrics.get('items_failed', 0)}")
    typer.echo(f"Success rate:      {orchestrator.metrics_observer.get_success_rate():.1f}%")

    # Show manual review queue if not empty
    review_items = orchestrator.get_review_queue()
    if review_items:
        typer.echo("")
        typer.echo(f"⚠️  {len(review_items)} items need manual review")
        typer.echo(f"    See: {settings.data_dir / 'manual_review.json'}")

    # Show rankings summary if available
    if results and results.rankings:
        typer.echo("")
        typer.echo("Top 5 Rankings:")
        for ranking in results.rankings[:5]:
            typer.echo(
                f"  {ranking.rank}. {ranking.track.all_artists_string} - {ranking.track.title} "
                f"(score: {ranking.total_score:.2f})"
            )

    typer.echo("")
    typer.echo("✓ Pipeline completed successfully!")


@app.command()
def run(
        year: Annotated[
            int,
            typer.Option(
                "--year",
                "-y",
                help="Target year for analysis.",
            ),
        ] = 2025,

        stages: Annotated[
            list[str],
            typer.Option(
                "--stage",
                "-s",
                help="Stages to run (extract, enrich, rank, all). Use multiple times for multiple stages.",
            ),
        ] = None,

        no_youtube: Annotated[
            bool,
            typer.Option(
                "--no-youtube",
                help="Skip YouTube video data enrichment.",
            ),
        ] = False,

        reset: Annotated[
            bool,
            typer.Option(
                "--reset",
                help="Reset pipeline (clear all checkpoints and data).",
            ),
        ] = False,

        playlist: Annotated[
            str,
            typer.Option(
                "--playlist",
                "-p",
                help="Playlist name to extract (default: '✅ {year} Selection').",
            ),
        ] = None,
) -> None:
    """Run the music charts pipeline.

    Examples:
        msc run --year 2025
        msc run --year 2025 --stage extract --stage enrich
        msc run --year 2025 --reset  # Start from scratch
    """
    # Local import to avoid circular dependencies
    from msc.pipeline.orchestrator import PipelineOrchestrator

    settings = get_settings()
    settings.year = year

    # Determine which stages to run
    run_extraction, run_enrichment, run_ranking = _determine_stages(stages)

    # Display configuration
    _display_pipeline_config(year, run_extraction, run_enrichment, run_ranking, no_youtube)

    try:
        # Initialize orchestrator
        orchestrator = PipelineOrchestrator(
            include_youtube=not no_youtube,
            verbose=False,
        )

        # Reset if requested
        if reset:
            typer.confirm("⚠️  This will delete all checkpoints and processed data. Continue?", abort=True)
            orchestrator.reset_pipeline()
            typer.echo("✓ Pipeline reset complete")
            typer.echo("")

        # Run pipeline
        typer.echo("Starting pipeline execution...")
        typer.echo("")

        results = orchestrator.run(
            run_extraction=run_extraction,
            run_enrichment=run_enrichment,
            run_ranking=run_ranking,
            playlist_name=playlist,
        )

        # Display summary
        _display_summary(orchestrator, results)

    except KeyboardInterrupt:
        typer.echo("")
        typer.echo("⚠️  Pipeline interrupted by user")
        typer.echo("   Checkpoints have been saved - you can resume later")
        raise typer.Exit(1)

    except Exception as error:
        typer.echo("")
        typer.echo(f"✗ Pipeline failed: {error!s}", err=True)
        raise typer.Exit(1)


@app.command()
def billing() -> None:
    """Check Songstats API billing and quota status.

    Displays current API usage, remaining quota, and reset date.
    Warns if usage exceeds 80% of monthly limit.

    Examples:
        msc billing
    """
    try:
        # Import client locally to avoid circular dependencies
        from msc.clients.songstats import SongstatsClient
        from rich.console import Console

        settings = get_settings()
        api_key = settings.get_songstats_key()

        # Fetch quota data
        client = SongstatsClient(api_key=api_key)
        quota_data = client.get_quota()

        if not quota_data:
            raise NetworkError("Failed to retrieve quota data from Songstats API")

        # Format and display quota table
        table = QuotaFormatter.format_billing_table(quota_data)
        console = Console()
        console.print(table)

        # Warn if usage is high (>= 80%)
        requests_used = quota_data.get("requests_used", 0)
        requests_limit = quota_data.get("requests_limit", 0)
        usage_pct = (requests_used / requests_limit) * 100 if requests_limit > 0 else 0.0

        if usage_pct >= 80:
            console.print(
                f"\n⚠️  [bold yellow]Warning: {usage_pct:.1f}% of monthly quota used[/bold yellow]"
            )

    except Exception as error:
        help_text = ErrorHandler.handle(error)
        typer.echo(help_text, err=True)
        raise typer.Exit(1)


@app.command()
def validate(
        input_file: Annotated[
            Path,
            typer.Argument(
                help="Path to data file to validate.",
                exists=True,
                readable=True,
            ),
        ],
) -> None:
    """Validate a data file against the expected schema.

    Automatically detects file type (Track, TrackWithStats, PowerRankingResults)
    and validates against the appropriate Pydantic model.

    Examples:
        msc validate _data/output/2025/stats.json
        msc validate _data/output/2025/rankings.json
    """
    try:
        from rich.console import Console

        typer.echo(f"Validating: {input_file}")

        # Validate file
        validator = FileValidator()
        result = validator.validate_file(input_file)

        console = Console()

        if result.is_valid:
            # Display success message
            msg = ValidationFormatter.format_success_message(input_file, result.model_name)
            console.print(msg)

        else:
            # Display validation errors
            panel = ValidationFormatter.format_error_list(result.errors)
            console.print(panel)
            typer.echo(
                f"\n✗ Validation failed: {result.error_count} errors found",
                err=True,
            )
            raise typer.Exit(1)

    except Exception as error:
        help_text = ErrorHandler.handle(error)
        typer.echo(help_text, err=True)
        raise typer.Exit(1)


@app.command()
def export(
        year: Annotated[
            int,
            typer.Option(
                "--year",
                "-y",
                help="Year to export.",
            ),
        ] = 2025,
        export_format: Annotated[
            str,
            typer.Option(
                "--format",
                "-f",
                help="Export format (csv, ods, html).",
            ),
        ] = "csv",
        output: Annotated[
            Path | None,
            typer.Option(
                "--output",
                "-o",
                help="Output file path (optional).",
            ),
        ] = None,
) -> None:
    """Export enriched track data to CSV, ODS (LibreOffice), or HTML format.

    Examples:
        msc export --year 2025 --format csv
        msc export --year 2025 --format ods --output rankings.ods
        msc export --year 2025 --format html --output report.html
    """
    try:
        from msc.storage.json_repository import JSONStatsRepository
        from rich.console import Console

        settings = get_settings()
        settings.year = year

        # Determine stats file path
        stats_file = settings.year_output_dir / "stats.json"

        if not stats_file.exists():
            typer.echo(
                f"Error: No data found for {year}. Run pipeline first: msc run --year {year}",
                err=True,
            )
            raise typer.Exit(1)

        # Load repository
        repo = JSONStatsRepository(stats_file)

        if repo.count() == 0:
            typer.echo(
                f"Error: Stats file is empty. Run pipeline first: msc run --year {year}",
                err=True,
            )
            raise typer.Exit(1)

        # Determine output path
        if output is None:
            extension_map = {"csv": "csv", "ods": "ods", "html": "html"}
            extension = extension_map.get(export_format, "csv")
            output = settings.year_output_dir / f"export.{extension}"

        # Export using DataExporter
        exporter = DataExporter(repo)

        # Dispatch to appropriate export method
        export_methods = {
            "csv": exporter.export_csv,
            "ods": exporter.export_ods,
            "html": exporter.export_html,
        }

        export_method = export_methods.get(export_format)

        if export_method is None:
            typer.echo(f"Error: Unsupported format '{export_format}'", err=True)
            typer.echo(f"Supported formats: {', '.join(export_methods.keys())}")
            raise typer.Exit(1)

        result = export_method(output, flat=True)

        # Display export summary
        console = Console()
        stats_d = {
            "row_count": result.row_count,
            "file_size_bytes": result.file_size_bytes,
            "duration_seconds": result.duration_seconds,
        }
        panel = ExportFormatter.format_export_summary(stats_d)
        console.print(panel)

        typer.echo(f"\n✓ Exported to: {result.file_path}")

    except Exception as error:
        help_text = ErrorHandler.handle(error)
        typer.echo(help_text, err=True)
        raise typer.Exit(1)


@app.command()
def clean(
        dry_run: Annotated[
            bool,
            typer.Option(
                "--dry-run",
                help="Show what would be deleted without actually deleting.",
            ),
        ] = True,
        older_than: Annotated[
            int | None,
            typer.Option(
                "--older-than",
                help="Only delete files older than N days.",
            ),
        ] = None,
) -> None:
    """Clean cached data files.

    By default, runs in dry-run mode to show what would be deleted.
    Use --no-dry-run to actually delete files.

    Examples:
        msc clean                              # Dry run (show what would be deleted)
        msc clean --no-dry-run                 # Actually delete all cache files
        msc clean --no-dry-run --older-than 7  # Delete files older than 7 days
    """
    try:
        settings = get_settings()
        manager = CacheManager(settings.cache_dir)

        # Get initial cache stats
        stats_req = manager.get_stats()

        if stats_req.file_count == 0:
            typer.echo("Cache is empty - nothing to clean")
            return

        # Display cache information
        size_str = manager.format_size(stats_req.total_size_bytes)
        typer.echo(f"\nCache directory: {stats_req.cache_dir}")
        typer.echo(f"Files: {stats_req.file_count}")
        typer.echo(f"Total size: {size_str}")
        typer.echo(f"Oldest file: {stats_req.oldest_file_age_days} days old\n")

        if older_than:
            typer.echo(f"Filtering: Files older than {older_than} days")

        # Clean cache
        deleted_count = manager.clean(dry_run=dry_run, older_than_days=older_than)

        if dry_run:
            typer.echo(f"[DRY RUN] Would delete {deleted_count} files")
            typer.echo("\nTo actually delete, run: msc clean --no-dry-run")

        else:
            typer.echo(f"✓ Deleted {deleted_count} files")

    except Exception as error:
        help_text = ErrorHandler.handle(error)
        typer.echo(help_text, err=True)
        raise typer.Exit(1)


@app.command()
def stats(
        year: Annotated[
            int,
            typer.Option(
                "--year",
                "-y",
                help="Year to analyze.",
            ),
        ] = 2025,
) -> None:
    """Display statistics about processed track data.

    Examples:
        msc stats --year 2025
    """
    try:
        from msc.storage.json_repository import JSONStatsRepository

        settings = get_settings()
        settings.year = year

        # Load stats file
        stats_file = settings.year_output_dir / "stats.json"

        if not stats_file.exists():
            typer.echo(
                f"Error: No data found for {year}. Run pipeline first: msc run --year {year}",
                err=True,
            )
            raise typer.Exit(1)

        repo = JSONStatsRepository(stats_file)
        data = repo.get_all()

        if not data:
            typer.echo(
                f"Error: Stats file is empty. Run pipeline first: msc run --year {year}",
                err=True,
            )
            raise typer.Exit(1)

        # Calculate basic statistics
        total_tracks = len(data)

        # Count tracks with data on each platform
        platform_counts = {
            "Spotify": sum(
                1 for t in data if t.platform_stats.spotify is not None and t.platform_stats.spotify.streams),
            "Apple Music": sum(
                1 for t in data if t.platform_stats.apple_music is not None and t.platform_stats.apple_music.streams),
            "YouTube": sum(1 for t in data if t.platform_stats.youtube is not None and t.platform_stats.youtube.views),
            "Deezer": sum(1 for t in data if t.platform_stats.deezer is not None and t.platform_stats.deezer.fans),
            "TikTok": sum(1 for t in data if t.platform_stats.tiktok is not None and t.platform_stats.tiktok.views),
        }

        # Display statistics
        typer.echo(f"\n=== Dataset Statistics - {year} ===\n")
        typer.echo(f"Total Tracks: {total_tracks}\n")
        typer.echo("Platform Coverage:")
        for platform, count in platform_counts.items():
            pct = (count / total_tracks * 100) if total_tracks > 0 else 0
            typer.echo(f"  {platform:15} {count:4} tracks ({pct:5.1f}%)")

    except Exception as error:
        help_text = ErrorHandler.handle(error)
        typer.echo(help_text, err=True)
        raise typer.Exit(1)


@app.command()
def init() -> None:
    """Initialize the project directory structure."""
    settings = get_settings()

    typer.echo("Creating directory structure...")
    settings.ensure_directories()

    typer.echo("Directories created:")
    typer.echo(f"  - {settings.data_dir}")
    typer.echo(f"  - {settings.input_dir}")
    typer.echo(f"  - {settings.output_dir}")
    typer.echo(f"  - {settings.cache_dir}")
    typer.echo(f"  - {settings.tokens_dir}")
    typer.echo(f"  - {settings.config_dir}")

    typer.echo("\nInitialization complete!")


if __name__ == "__main__":
    app()
