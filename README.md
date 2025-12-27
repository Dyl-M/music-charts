# music-charts

[![DeepSource](https://app.deepsource.com/gh/Dyl-M/music-charts.svg/?label=code+coverage&show_trend=true&token=w0Cma8yAE6F5DyZ3EUjnGCfH)](https://app.deepsource.com/gh/Dyl-M/music-charts/)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/music-charts.svg/?label=active+issues&show_trend=true&token=w0Cma8yAE6F5DyZ3EUjnGCfH)](https://app.deepsource.com/gh/Dyl-M/music-charts/)
[![GitHub last commit](https://img.shields.io/github/last-commit/Dyl-M/music-charts?label=Last%20Commit&style=flat-square&logo=git&logoColor=white)](https://github.com/Dyl-M/music-charts/branches)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/Dyl-M/music-charts?label=Commit%20Activity&style=flat-square&logo=git&logoColor=white)](https://github.com/Dyl-M/music-charts/branches)

Data pipeline for analyzing track performance across streaming platforms and generating power rankings.

## Overview

Music-charts processes electronic music tracks from a MusicBee library, enriches them with data from
the [Songstats API](https://songstats.com/), and generates power rankings based on weighted metrics across 10 platforms:
Spotify, Apple Music, YouTube, Deezer, TikTok, Beatport, Tidal, SoundCloud, Amazon Music, and 1001Tracklists.

## Features

The `msc` CLI provides a complete ETL pipeline with 7 commands: `run`, `billing`, `validate`, `export`, `clean`,
`stats`, and `init`. It extracts tracks from MusicBee playlists, enriches them with cross-platform statistics via the
Songstats API, and generates power rankings using a weighted scoring algorithm (0-100 scale with data availability
weighting).

Key capabilities include checkpoint-based resumption for long-running jobs, automatic validation to filter out false
positives, and export to multiple formats (CSV, ODS, HTML). The pipeline features rich console output with progress
bars, structured logging, and a manual review queue for unmatched tracks.

## Installation

```bash
# Clone the repository
git clone https://github.com/Dyl-M/music-charts.git
cd music-charts

# Install the package with dependencies (using uv)
uv sync

# Or with development tools (pytest, ruff, mypy)
uv sync --extra dev

# Alternative: Using pip
pip install -e .
pip install -e ".[dev]"
```

## Quick Start

### Initialize Project

```bash
# Create directory structure
msc init
```

### Run Full Pipeline

```bash
# Run all stages (extract, enrich, rank)
msc run --year 2025

# Run specific stages only
msc run --year 2025 --stage extract --stage enrich

# Skip YouTube enrichment
msc run --year 2025 --no-youtube

# Reset and start fresh
msc run --year 2025 --reset

# Custom playlist
msc run --year 2025 --playlist "My Custom Playlist"
```

### Check API billing

```bash
# View Songstats API usage
msc billing
```

### Export Data

```bash
# Export to CSV (default)
msc export --year 2025

# Export to ODS (LibreOffice/OpenOffice)
msc export --year 2025 --format ods --output rankings.ods

# Export to HTML
msc export --year 2025 --format html --output report.html
```

### Validate Data Files

```bash
# Validate any JSON data file (auto-detects format)
msc validate _data/output/2025/stats.json
msc validate _data/output/2025/rankings.json
```

### View Statistics

```bash
# Display dataset statistics
msc stats --year 2025
```

### Clean Cache

```bash
# Dry run (shows what would be deleted)
msc clean

# Actually delete cache files
msc clean --no-dry-run

# Delete files older than 7 days
msc clean --no-dry-run --older-than 7
```

## Project Structure

```
music-charts/
├── .github/                # GitHub Actions & Dependabot configurations
├── _config/                # Runtime configuration
├── _data/                  # Data artifacts (gitignored)
├── _tests/                 # Test suite
├── _tokens/                # Credentials (gitignored)
└── msc/                    # Main package
    ├── analysis/           # Normalization strategies & power ranking scorer
    ├── clients/            # MusicBee, Songstats, YouTube API clients
    ├── commands/           # CLI utilities (errors, validators, exporters)
    ├── config/             # Pydantic settings & constants
    ├── models/             # Pydantic models (tracks, stats, rankings)
    ├── pipeline/           # ETL stages & orchestrator with observers
    ├── storage/            # Repository pattern & checkpointing
    ├── utils/              # Logging, retry, text processing, path security
    └── cli.py              # Typer CLI entry point
```

Each submodule contains a `README_*.md` file with detailed documentation and code examples.

## Development

### Running Tests

```bash
pytest                      # Run all tests
pytest _tests/unit/         # Unit tests only
pytest _tests/integration/  # Integration tests only
pytest --cov=msc            # With coverage report
pytest -v --tb=short        # Verbose with short traceback
```

### Code Quality

```bash
ruff check msc/             # Linting
ruff format msc/            # Formatting
mypy msc/                   # Type checking (when available)
```

## License

This project is licensed under the [MIT License](LICENSE) - Copyright (c) 2024-2025 Dylan "Dyl-M" Monfret.
