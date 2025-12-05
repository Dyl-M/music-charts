"""Command-line interface for the Music Charts pipeline."""

from pathlib import Path
from typing import Annotated

import typer

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
    version: Annotated[
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
    log_level = "DEBUG" if verbose else "INFO"
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
            help="Stages to run (extract, enrich, youtube, rank). Use multiple times for multiple stages.",
        ),
    ] = None,
) -> None:
    """Run the music charts pipeline.

    Examples:
        msc run --year 2025
        msc run --year 2025 --stage extract --stage enrich
    """
    if stages is None:
        stages = ["all"]
    settings = get_settings()
    settings.year = year

    typer.echo(f"Running pipeline for year {year}")
    typer.echo(f"Stages: {', '.join(stages)}")

    # TODO: Implement pipeline execution
    typer.echo("Pipeline execution not yet implemented.")
    typer.echo("Use legacy scripts in src/ for now.")


@app.command()
def billing() -> None:
    """Check Songstats API billing and quota status."""
    settings = get_settings()

    try:
        api_key = settings.get_songstats_key()
        typer.echo("Checking Songstats API status...")

        # TODO: Implement billing check using SongstatsClient
        typer.echo(f"API key loaded: {api_key[:8]}...")
        typer.echo("Billing check not yet implemented.")

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

    # TODO: Implement schema validation
    typer.echo("Validation not yet implemented.")


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
