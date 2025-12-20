"""Command-line interface for the Music Charts pipeline."""

# Standard library
from pathlib import Path
from typing import Annotated, Literal

# Third-party
import typer

# Local
from msc import __version__
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

    if stages is None:
        stages = ["all"]

    settings = get_settings()
    settings.year = year

    # Determine which stages to run
    run_all = "all" in stages
    run_extraction = run_all or "extract" in stages
    run_enrichment = run_all or "enrich" in stages
    run_ranking = run_all or "rank" in stages

    typer.echo(f"🎵 Music Charts Pipeline - Year {year}\n")
    typer.echo("Pipeline stages:")
    typer.echo(f"  • Extraction:  {'✓' if run_extraction else '✗'}")
    typer.echo(f"  • Enrichment:  {'✓' if run_enrichment else '✗'}")
    typer.echo(f"  • Ranking:     {'✓' if run_ranking else '✗'}")
    typer.echo(f"  • YouTube:     {'✗ (disabled)' if no_youtube else '✓'}\n")

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
                    f"  {ranking.rank}. {ranking.track.artist} - {ranking.track.title} "
                    f"(score: {ranking.total_score:.2f})"
                )

        typer.echo("")
        typer.echo("✓ Pipeline completed successfully!")

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
    """Check Songstats API billing and quota status."""
    settings = get_settings()

    try:
        api_key = settings.get_songstats_key()
        typer.echo("Checking Songstats API status...")
        typer.echo(f"API key loaded: {api_key[:8]}...")

        raise NotImplementedError(
            "Billing check not yet implemented. "
            "This will be available in Phase 2 after SongstatsClient is implemented."
        )

    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
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

    Examples:
        msc validate _data/output/2025/selection.json
    """
    typer.echo(f"Validating: {input_file}")

    raise NotImplementedError(
        "Schema validation not yet implemented. "
        "This will be available in Phase 3 after data models are defined."
    )


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
