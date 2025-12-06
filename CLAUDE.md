# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music-charts is a data pipeline for analyzing track performance across streaming platforms (Spotify, Apple Music, YouTube, Deezer, TikTok, Beatport, Tidal, SoundCloud, Amazon Music, 1001Tracklists). It processes electronic music tracks from a MusicBee library, enriches them with Songstats API data, and generates power rankings based on weighted metrics.

**Status:** Phase 1 (Foundation) complete - modular `msc` package established with 53% test coverage (83 tests). Legacy scripts archived in `_legacy/`.

## Commands

### New Package (msc)

```bash
# Install the package
pip install -e .

# Install with dev dependencies (pytest, ruff, mypy)
pip install -e ".[dev]"

# CLI commands (via Typer)
msc --help              # Show available commands
msc init                # Initialize directory structure
msc billing             # Check Songstats API quota
msc run --year 2025     # Run pipeline (not yet implemented)
msc validate <file>     # Validate data file (not yet implemented)

# Run tests
pytest

# Linting and type checking
ruff check msc/
mypy msc/
```

### Legacy Pipeline (in `_legacy/`)

```bash
# Stage 1: Extract tracks from MusicBee, search via Songstats API
cd _legacy/src && python data-mining-prep.py

# Stage 2: Fetch comprehensive stats from Songstats API
cd _legacy/src && python data-mining-sstats.py

# Stage 3: Enrich with YouTube data (requires browser OAuth on first run)
cd _legacy/src && python data-mining-completion.py

# Stage 4: Run analysis notebook
jupyter notebook _legacy/notebooks/power_ranking_2024.ipynb
```

## Architecture

### Current Structure

```
music-charts/
├── msc/                        # Main package
│   ├── __init__.py             # Package version
│   ├── cli.py                  # Typer CLI entry point
│   ├── config/
│   │   ├── settings.py         # Pydantic settings (env vars, paths)
│   │   └── constants.py        # Enums (Platform, StatCategory), weights
│   ├── clients/
│   │   └── base.py             # Abstract BaseClient with retry/rate limiting
│   ├── models/                 # Data models (skeleton)
│   ├── pipeline/
│   │   └── base.py             # Abstract PipelineStage (ETL pattern)
│   ├── analysis/               # Analytics modules (skeleton)
│   ├── storage/                # Data persistence (skeleton)
│   └── utils/
│       ├── logging.py          # Structured logging, PipelineLogger
│       ├── retry.py            # retry_with_backoff decorator, RateLimiter
│       └── text.py             # format_title, remove_remixer, etc.
│
├── _legacy/                    # Archived original scripts (to be removed after migration)
│   ├── src/
│   │   ├── billing.py
│   │   ├── data-mining-prep.py
│   │   ├── data-mining-sstats.py
│   │   └── data-mining-completion.py
│   ├── notebooks/
│   │   └── power_ranking_2024.ipynb
│   ├── data/                   # Legacy data artifacts
│   └── notes/
│
├── _tests/                     # Pytest test suite (83 tests, 53% coverage)
│   ├── conftest.py             # Shared fixtures
│   ├── unit/
│   │   ├── test_config.py      # 19 tests (settings, constants)
│   │   ├── test_logging.py     # 18 tests (logging utilities)
│   │   ├── test_retry.py       # 22 tests (retry, rate limiting)
│   │   └── test_text.py        # 24 tests (text utilities)
│   └── integration/
│
├── _config/                    # Runtime configuration (YAML files)
├── _data/                      # Data artifacts (gitignored)
│   ├── input/
│   ├── output/
│   └── cache/
├── _tokens/                    # Credentials (gitignored)
├── _notebooks/                 # Exploratory notebooks
│
├── pyproject.toml              # Modern Python packaging (hatchling)
├── .env.example                # Environment variable template
└── _docs/
    └── IMPROVEMENTS.md         # Modular architecture roadmap
```

### Key Modules

| Module | Purpose | Status | Coverage |
|--------|---------|--------|----------|
| `msc/config/settings.py` | Pydantic settings with `MSC_` env prefix | ✅ Complete | 100% (19 tests) |
| `msc/config/constants.py` | Platform enum, StatCategory, weights | ✅ Complete | 100% (in test_config) |
| `msc/utils/logging.py` | setup_logging, PipelineLogger | ✅ Complete | 100% (18 tests) |
| `msc/utils/retry.py` | retry_with_backoff, RateLimiter | ✅ Complete | 96% (22 tests) |
| `msc/utils/text.py` | Title formatting, query building | ✅ Complete | 100% (24 tests) |
| `msc/clients/base.py` | Abstract client with session management | ✅ Base class | 0% (NotImplementedError) |
| `msc/pipeline/base.py` | Abstract ETL stage, Pipeline orchestrator | ✅ Base class | 0% (NotImplementedError) |
| `msc/cli.py` | Typer CLI skeleton | ✅ Skeleton | 0% (NotImplementedError) |
| `msc/clients/songstats.py` | Songstats API client | 🔲 Phase 2 | - |
| `msc/clients/youtube.py` | YouTube API client | 🔲 Phase 2 | - |
| `msc/clients/musicbee.py` | MusicBee library reader | 🔲 Phase 2 | - |
| `msc/models/*` | Track, Stats, Ranking dataclasses | 🔲 Phase 3 | - |
| `msc/pipeline/extract.py` | ExtractionStage | 🔲 Phase 4 | - |
| `msc/pipeline/enrich.py` | EnrichmentStage | 🔲 Phase 4 | - |
| `msc/analysis/scorer.py` | PowerRankingScorer | 🔲 Phase 4 | - |

### Data Flow

1. MusicBee library XML → filtered by playlist ID
2. Songstats API → track search + multi-platform statistics
3. YouTube Data API → video validation + view counts
4. Analysis → MinMaxScaler normalization + weighted scoring

### Weighted Scoring System

- **Negligible (×1):** Charts, Engagement, Shorts
- **Low (×2):** Reach, Playlists, Professional Support
- **High (×4):** Popularity, Streams

## Configuration

### Environment Variables (MSC_ prefix)

```bash
MSC_MUSICBEE_LIBRARY=E:/Musique/MusicBee/iTunes Music Library.xml
MSC_YEAR=2025
MSC_PLAYLIST_ID=4361
MSC_SONGSTATS_RATE_LIMIT=10
MSC_YOUTUBE_QUOTA_DAILY=10000
MSC_SONGSTATS_API_KEY=your_key  # Or use _tokens/songstats_key.txt
```

### Required Credentials

All stored in `_tokens/` (gitignored):
- `songstats_key.txt` - Songstats Enterprise API key
- `oauth.json` - Google OAuth 2.0 client secrets
- `credentials.json` - Cached Google API tokens (auto-generated)

## Key Conventions

- **Package name:** `msc` (Music Stats Charts)
- **Settings:** Pydantic with `MSC_` environment prefix
- **Logging:** Structured via `msc.utils.logging`
- **Retry:** `@retry_with_backoff` decorator with exponential backoff
- **Rate limiting:** `RateLimiter` class for API calls
- **ETL pattern:** `PipelineStage.extract() → transform() → load()`
- **API failures:** Return empty dicts/lists (defensive coding)
- **File encoding:** UTF-8 explicit on all operations
- **Support folders:** Underscore prefix (`_config/`, `_data/`, `_tests/`, `_tokens/`)
- **Placeholders:** Use `NotImplementedError` for incomplete code (excluded from coverage)

## Development

### Running Tests

```bash
pytest                      # Run all tests
pytest _tests/unit/         # Unit tests only
pytest -v --tb=short        # Verbose with short traceback
pytest --cov=msc            # With coverage report
```

### Test Conventions

- Tests use pytest with class-based grouping
- Test methods use `@staticmethod` decorator (no `self` parameter)
- Fixtures defined in `_tests/conftest.py`
- Current coverage: 53% overall (83 tests)
  - `config/`: 100% (19 tests for settings + constants)
  - `utils/logging.py`: 100% (18 tests)
  - `utils/retry.py`: 96% (22 tests)
  - `utils/text.py`: 100% (24 tests)
  - Base classes, CLI: 0% (NotImplementedError excluded from coverage)

### Code Quality

```bash
ruff check msc/             # Linting
ruff format msc/            # Formatting
mypy msc/                   # Type checking
```

## Refactoring Roadmap

See `_docs/IMPROVEMENTS.md` for detailed phases:

- **Phase 1 (Foundation):** ✅ Complete - pyproject.toml, config, utils, base classes
- **Phase 2 (API Clients):** Next - SongstatsClient, YouTubeClient, MusicBeeClient
- **Phase 3 (Data Models):** Track, PlatformStats, Ranking dataclasses
- **Phase 4 (Pipeline Migration):** Migrate legacy scripts to pipeline stages
- **Phase 5 (CLI & Polish):** Full CLI implementation, progress bars, documentation
