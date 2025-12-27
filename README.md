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

## Status

**Version 1.0.0** ✅ **Ready** - Professional-grade data pipeline with CLI

**Branch:** `feat-V1` → `main`

### Version 1.0.0 Features

- **Legacy-Compatible Scoring Algorithm:** Power rankings now use 0-100 scale with data availability weighting
- **Dynamic Weight Adjustment:** Category weights adapt based on per-metric data availability (ISSUE-017/019)
- **YouTube "Topic Channel" Fallback:** Tracks with only Topic channel videos now correctly capture YouTube data (
  ISSUE-018)
- **UUID5-based Track Identifiers:** Compact 8-character deterministic IDs replacing long string concatenation
- **Songstats Match Validation:** Keyword-based rejection prevents false positives (karaoke, instrumentals)
- **Enhanced Metadata Extraction:** ISRC codes, Songstats artist/label lists for data quality validation
- **Run-based Directory Structure:** Organized output with timestamps for better tracking
- **Clean Console Output:** Minimal logs with file-based verbose logging and enhanced progress bars
- **Manual Review Queue:** Automatic checkpoint resumption with deduplication
- **Comprehensive Query Cleaning:** Advanced text normalization for better Songstats search accuracy
- **Pre-1.0.0 Code Review:** Dead code removal, redundancy fixes, Pythonic improvements, lazy logging compliance

### CLI Features

- **7 CLI commands:** `run`, `billing`, `validate`, `export`, `clean`, `stats`, `init`
- **Error handling infrastructure:** Custom exceptions with helpful multi-line suggestions
- **Display formatters:** Rich tables and panels for quota, validation errors, export summaries
- **File validation:** Auto-detection and validation against Pydantic models
- **Data export:** CSV, ODS (LibreOffice), and HTML formats with statistics
- **Cache management:** Statistics and cleanup with dry-run mode
- **Enhanced progress bars:** ETA, current item display, error visibility

**Architecture (All Phases Complete):**

- Phase 5: CLI & Polish - 7 commands, error handling, export formats
- Phase 4: Pipeline Migration - Full ETL with checkpoints, observers
- Phase 3: Data Models - 17 Pydantic models with validation
- Phase 2: API Clients - MusicBee, Songstats, YouTube (100% coverage)
- Phase 1: Foundation - Config, utils, base classes

**Package Manager:** [uv](https://github.com/astral-sh/uv) for faster dependency resolution and reproducible builds

**Legacy:** Original ETL scripts archived in `_legacy/` for reference

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

### Check API Quota

```bash
# View Songstats API usage and remaining quota
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

### Legacy Pipeline (Archived)

```bash
# Run pipeline stages sequentially (legacy method)
cd _legacy/src && python data-mining-prep.py       # Stage 1: Extract & search
cd _legacy/src && python data-mining-sstats.py     # Stage 2: Fetch platform stats
cd _legacy/src && python data-mining-completion.py # Stage 3: YouTube enrichment
jupyter notebook _legacy/notebooks/power_ranking_2024.ipynb  # Stage 4: Analysis
```

## Project Structure

```
music-charts/
├── _config/                # Runtime configuration
├── _data/                  # Data artifacts (gitignored)
├── _demos/                 # Interactive demo scripts
├── _docs/                  # Documentation and notes
│
├── _legacy/                # Archived original scripts
│   ├── src/                # Original pipeline scripts
│   ├── notebooks/          # Original Jupyter notebooks
│   └── data/               # Legacy data artifacts
│
├── _notebooks/             # Jupyter notebooks
├── _tests/                 # Test suite
├── _tokens/                # Credentials (gitignored)
│
└── msc/                    # Main package (new modular architecture)
    ├── analysis/           # Analytics modules
    ├── clients/            # API clients
    ├── commands/           # CLI utilities
    ├── config/             # Configuration
    ├── models/             # Data models
    ├── pipeline/           # ETL pipeline base classes
    ├── storage/            # Data persistence
    ├── utils/              # Utilities
    └── cli.py              # Typer CLI entry point
```

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
