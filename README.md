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

**Current:** Phase 3 (Data Models) ✅ **Complete** - All data models implemented with comprehensive test coverage
- **6 model modules** with 17 exported models (Track, PlatformStats, YouTubeVideoData, PowerRanking, etc.)
- **5 model test suites** with extensive validation coverage
- **6 demo scripts** (3 API clients + 5 model demos + 1 integration demo)

**Previous Phases:**
- Phase 2 (API Clients) ✅ Complete - 3 clients with 100% individual coverage (MusicBee, Songstats, YouTube)
- Phase 1 (Foundation) ✅ Complete - Config, utils, base classes (100% coverage)

**Package Manager:** [uv](https://github.com/astral-sh/uv) for faster dependency resolution and reproducible builds

**Legacy:** Original ETL scripts archived in `_legacy/` for reference

**Next:** Phase 4 - Pipeline Migration (Extract, Enrich, Analyze stages)

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

### New CLI (In Development)

```bash
# Initialize directory structure
msc init

# Check Songstats API quota
msc billing

# Run pipeline (not yet implemented)
msc run --year 2025
```

### Legacy Pipeline

```bash
# Run pipeline stages sequentially
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
├── _docs/                  # Documentations and notes
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
