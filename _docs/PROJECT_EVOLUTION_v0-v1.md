# Project Evolution: From Legacy Scripts to msc 1.0.0

This document chronicles the development of **music-charts** from its origins as a collection of standalone Python
scripts (December 2024) to its current form as a professional-grade CLI tool (msc 1.0.0, December 2025).

## Introduction

Music-charts is a data pipeline for analyzing track performance across 10 streaming platforms: Spotify, Apple Music,
YouTube, Deezer, TikTok, Beatport, Tidal, SoundCloud, Amazon Music, and 1001Tracklists. The project processes
electronic music tracks from a MusicBee library, enriches them with data from the Songstats API, and generates power
rankings based on weighted metrics.

### The Transformation

| Aspect             | Legacy (2024)           | msc 1.0.0 (2025)                   |
|--------------------|-------------------------|------------------------------------|
| **Architecture**   | 4 standalone scripts    | Modular package with 12 submodules |
| **Entry Point**    | Manual script execution | Unified CLI with 7 commands        |
| **Testing**        | None                    | 1097 tests (94% coverage)          |
| **Data Models**    | Raw dictionaries        | 17 Pydantic models                 |
| **Error Handling** | Basic try/except        | Custom exception hierarchy         |
| **Resumability**   | Partial (Stage 1 only)  | Full checkpoint-based recovery     |
| **Configuration**  | Hard-coded paths        | Pydantic settings with env vars    |
| **Logging**        | Print statements        | Structured dual-level logging      |

### Timeline

The refactoring effort spanned approximately 11 weeks of focused development:

- **December 2024**: Project initialization and legacy pipeline operation
- **December 5-6, 2025**: Phase 1 - Foundation
- **December 16-19, 2025**: Phase 2 - API Clients
- **December 19, 2025**: Phase 3 - Data Models
- **December 20, 2025**: Phase 4 - Pipeline & Storage
- **December 23-27, 2025**: Phase 5 - CLI & Polish + V1 Release

---

## The Legacy Pipeline

The original implementation consisted of four Python scripts and a Jupyter notebook, designed for manual sequential
execution.

### Architecture

```
legacy/
├── src/
│   ├── data-mining-prep.py       # Stage 1: Extract & Search
│   ├── data-mining-sstats.py     # Stage 2: Enrich with Platform Stats
│   ├── data-mining-completion.py # Stage 3: YouTube Enhancement
│   └── billing.py                # Utility: Check API quota
├── notebooks/
│   └── power_ranking_2024.ipynb  # Stage 4: Analysis & Visualization
└── data/
    ├── selection_2024.json       # Stage 1 output
    ├── data_2024.json            # Stage 2 output
    └── power_ranking_2024.csv    # Final export
```

### Data Flow

1. **Stage 1 (data-mining-prep.py)**: Read MusicBee library XML, extract tracks from a specific playlist, build search
   queries, call Songstats `/tracks/search` API, output track list with Songstats IDs.

2. **Stage 2 (data-mining-sstats.py)**: For each track with a valid Songstats ID, fetch comprehensive statistics from
   `/tracks/stats` (10 platforms) and historical peak data from `/tracks/historic_stats`.

3. **Stage 3 (data-mining-completion.py)**: Optional YouTube enhancement using OAuth2 authentication. This script was
   largely incomplete, with the main function only printing "Hello world!".

4. **Stage 4 (power_ranking_2024.ipynb)**: Jupyter notebook for analysis. Load enriched data, normalize metrics using
   MinMaxScaler (0-100 range), compute weighted category scores, apply importance multipliers, generate final power
   rankings with Plotly visualizations.

### Limitations

The legacy pipeline had several significant limitations:

- **No test coverage**: Zero automated tests, making refactoring risky
- **Manual execution**: Each stage required manual invocation in the correct order
- **Hard-coded configuration**: Paths, API keys, and playlist IDs embedded in scripts
- **No error handling infrastructure**: Basic try/except blocks returning empty dictionaries
- **Limited logging**: Print statements only, no structured logging or log files
- **Partial resumability**: Only Stage 1 had resume logic (checking existing output file)
- **No validation**: No input validation or data integrity checks
- **Monolithic analysis**: Scoring logic embedded in a Jupyter notebook

---

## Phase 1: Foundation

**Timeline**: December 5-6, 2025
**Outcome**: Modular architecture with 53% test coverage

Phase 1 established the foundational infrastructure for the new package, focusing on configuration management,
utilities, and coding standards.

### Configuration Module (`msc/config/`)

The configuration system was built on Pydantic Settings, providing type-safe configuration with environment variable
support. All settings use the `MSC_` prefix for namespacing.

Key components:

- **settings.py**: Pydantic Settings class with path configurations, API credentials, and runtime options
- **constants.py**: Enumerations (Platform, StatCategory), weight definitions, and API endpoint mappings

### Utilities Module (`msc/utils/`)

Four utility modules were created to support the pipeline:

- **logging.py**: Structured logging with `PipelineLogger` class, dual-level output (console ERROR, file INFO+), and
  JSONL format for file logs
- **retry.py**: `@retry_with_backoff` decorator for exponential backoff retry logic, plus `RateLimiter` class for API
  call throttling
- **text.py**: Text processing utilities (`format_title`, `format_artist`, `build_query`, `remove_remixer`) adapted
  from legacy scripts
- **path_utils.py**: Path validation and security utilities to prevent path traversal attacks

### Coding Standards

Phase 1 established the coding standards that would govern all subsequent development:

- **PEP 257**: Module docstrings as the first statement in every file
- **PEP 8**: Semantic import grouping (stdlib → third-party → local)
- **Lazy logging**: Placeholder-based logging (`logger.error("Failed %s", value)`) instead of f-strings
- **Security**: Path validation for all file operations using `validate_path_within_base()`

### Test Infrastructure

The test suite was established with pytest, achieving 53% coverage:

- 24 tests for configuration
- 75 tests for utilities
- Shared fixtures in `_tests/conftest.py`

---

## Phase 2: API Clients

**Timeline**: December 16-19, 2025
**Outcome**: Three API clients with 100% test coverage each

Phase 2 focused on creating robust, well-tested API clients for the three external services the pipeline depends on.

### BaseClient (`msc/clients/base.py`)

An abstract base class was created to provide common functionality:

- Session management with connection pooling
- Configurable retry logic and rate limiting
- Consistent error handling patterns
- Base URL and authentication header management

### SongstatsClient (PR #31)

**Delivered**: December 17, 2025

The Songstats client provides full coverage of the Enterprise API:

- Track search (`/tracks/search`)
- Multi-platform statistics (`/tracks/stats`)
- Historical peak data (`/tracks/historic_stats`)
- YouTube video aggregation (`/tracks/info`)
- API quota checking (`/status`)

Features: Rate limiting (configurable requests per second), automatic retry with exponential backoff, comprehensive
error handling with defensive returns.

**Testing**: 74 unit tests + 7 integration tests (100% coverage)

### YouTubeClient (PR #32)

**Delivered**: December 18, 2025

The YouTube client handles OAuth2 authentication and YouTube Data API v3:

- Credential management with automatic refresh
- Video metadata retrieval (duration, views, likes, comments)
- Playlist item enumeration
- Channel information lookup

Features: OAuth2 flow with credential caching, quota-aware design (daily limit tracking), graceful degradation for
quota exhaustion.

**Testing**: 42 unit tests + 7 integration tests (100% coverage)

### MusicBeeClient (PR #34)

**Delivered**: December 19, 2025

The MusicBee client parses iTunes-format library XML files:

- Library file reading with encoding detection
- Playlist extraction by ID or name
- Track metadata extraction (title, artists, album, genre, label, year, ISRC)
- Year-based filtering for playlist tracks

Features: Robust XML parsing with error recovery, configurable library path, playlist search by name pattern.

**Testing**: 40 unit tests + 8 integration tests (100% coverage)

---

## Phase 3: Data Models

**Timeline**: December 19, 2025 (PR #35)
**Outcome**: 17 Pydantic models across 6 modules

Phase 3 replaced raw dictionaries with type-safe Pydantic models, ensuring data integrity throughout the pipeline.

### Model Architecture

All models inherit from `MSCBaseModel`, a frozen Pydantic v2 base class that provides:

- Immutability (frozen=True) for data integrity
- Consistent JSON serialization
- Validation on construction
- Extra field rejection

### Track Models (`msc/models/track.py`)

- **Track**: Core track model with metadata (title, artists, album, genre, label, year, ISRC)
- **SongstatsIdentifiers**: Songstats API identifiers (ID, matched title, ISRC, Spotify ID)

The Track model introduces UUID5-based deterministic identifiers, replacing the legacy string concatenation approach.
Each track gets an 8-character identifier derived from a hash of artist list and title.

### Platform Models (`msc/models/platforms.py`)

Ten platform-specific models capture the unique metrics available from each service:

- SpotifyStats, AppleMusicStats, YouTubeStats, DeezerStats
- TikTokStats, BeatportStats, TidalStats, SoundCloudStats
- AmazonMusicStats, TracklistsStats

Each model defines the specific metrics available for that platform (streams, popularity, charts, playlists, etc.).

### Stats Models (`msc/models/stats.py`)

- **PlatformStats**: Container for all 10 platform models
- **TrackWithStats**: Combines Track with PlatformStats and metadata

### YouTube Models (`msc/models/youtube.py`)

- **YouTubeVideo**: Individual video metadata (ID, title, views, channel)
- **YouTubeVideoData**: Aggregated YouTube presence (most viewed, all sources, total views)

### Ranking Models (`msc/models/ranking.py`)

- **CategoryScore**: Score for a single category with weight and availability
- **PowerRanking**: Complete ranking entry with category breakdown
- **PowerRankingResults**: Full results container with metadata

### Key Features

- **Backward Compatibility**: `from_legacy_json()` methods parse legacy JSON formats
- **Flat/Nested Conversion**: `to_flat_dict()` and `from_flat_dict()` for pandas integration and export
- **Validation**: Pydantic validation on all fields with custom validators where needed

---

## Phase 4: Pipeline & Storage

**Timeline**: December 20, 2025 (PR #37)
**Outcome**: Complete ETL pipeline with 320 tests

Phase 4 implemented the core pipeline architecture using established design patterns.

### Pipeline Architecture

The pipeline follows the ETL (Extract, Transform, Load) pattern with three stages:

1. **ExtractionStage**: Reads MusicBee library, searches Songstats API, outputs Track models
2. **EnrichmentStage**: Fetches platform statistics and YouTube data, outputs TrackWithStats models
3. **RankingStage**: Computes power rankings, outputs PowerRankingResults

Each stage inherits from `PipelineStage` base class with the standard `extract() → transform() → load()` workflow.

### PipelineOrchestrator

The orchestrator coordinates stage execution:

- Manages stage sequencing and dependencies
- Handles observer notification
- Provides run management with timestamped directories
- Supports selective stage execution (run only extract, or only rank, etc.)

### Design Patterns

**Repository Pattern** (`msc/storage/`):

- `JSONTrackRepository`: Persists Track models to JSON
- `JSONStatsRepository`: Persists TrackWithStats models to JSON
- Consistent interface for data access and persistence

**Checkpoint Pattern** (`msc/storage/checkpoint.py`):

- `CheckpointManager`: Tracks processed, failed, and skipped items
- Enables pipeline resumability after interruption
- `ManualReviewQueue`: Stores items that need human review (no Songstats match)

**Observer Pattern** (`msc/pipeline/observer.py`, `observers.py`):

- `PipelineObserver`: Abstract interface for event handling
- `ConsoleObserver`: Prints events to stdout
- `FileObserver`: Writes events to JSONL file
- `ProgressBarObserver`: Rich progress display with ETA
- `MetricsObserver`: Collects timing and count statistics

**Strategy Pattern** (`msc/analysis/`):

- `NormalizationStrategy`: Abstract interface for normalization
- `MinMaxNormalizer`: Scales to 0-100 range (legacy-compatible)
- `ZScoreNormalizer`: Standardizes to mean=0, std=1
- `RobustNormalizer`: Uses median/IQR (outlier-resistant)

### PowerRankingScorer

The scorer implements the legacy algorithm from the Jupyter notebook:

1. **Metric Normalization**: MinMaxScaler with feature_range=(0, 100)
2. **Data Availability Weighting**: Per-metric weight = non_zero_count / total_tracks
3. **Category Score**: Weighted average of normalized metrics
4. **Importance Multipliers**:
    - Negligible (×1): Charts, Engagement, Shorts
    - Low (×2): Reach, Playlists, Professional Support
    - High (×4): Popularity, Streams
5. **Final Score**: Weighted average of category scores (0-100 range)

---

## Phase 5: CLI & Polish

**Timeline**: December 23-27, 2025 (PR #41)
**Outcome**: 7 CLI commands with comprehensive utilities

Phase 5 focused on user experience, creating a professional CLI interface with robust error handling and helpful
output formatting.

### CLI Commands (`msc/cli.py`)

Seven commands were implemented using Typer:

| Command        | Description                                  |
|----------------|----------------------------------------------|
| `msc run`      | Execute pipeline (all stages or subset)      |
| `msc billing`  | Check Songstats API quota and usage          |
| `msc validate` | Validate JSON data files with auto-detection |
| `msc export`   | Export rankings to CSV, ODS, or HTML         |
| `msc clean`    | Manage cache (dry-run mode, age filtering)   |
| `msc stats`    | Display dataset statistics                   |
| `msc init`     | Initialize directory structure               |

### Error Handling (`msc/commands/errors.py`)

A custom exception hierarchy was created:

- `MSCError`: Base exception with suggestion support
- `ConfigurationError`: Missing or invalid configuration
- `APIError`: API communication failures
- `ValidationError`: Data validation failures
- `ExportError`: Export operation failures

The `ErrorHandler` class provides centralized error handling with user-friendly formatting and helpful suggestions.

### Display Formatters (`msc/commands/formatters.py`)

Rich-based formatters for console output:

- `QuotaFormatter`: API usage display with progress bars
- `ValidationFormatter`: Validation results with error details
- `ExportFormatter`: Export summaries with file statistics

### File Validation (`msc/commands/validators.py`)

The `FileValidator` class provides:

- Automatic format detection (Track, TrackWithStats, PowerRankingResults)
- Schema validation against Pydantic models
- Detailed error reporting with location information
- Secure path validation

### Data Export (`msc/commands/exporters.py`)

The `DataExporter` class supports three output formats:

- **CSV**: Standard comma-separated values
- **ODS**: OpenDocument Spreadsheet (LibreOffice/OpenOffice)
- **HTML**: Styled HTML table with embedded CSS

### Cache Management (`msc/commands/cache.py`)

The `CacheManager` class provides:

- Cache statistics (file count, total size, age distribution)
- Dry-run mode for safe preview
- Age-based filtering (delete files older than N days)
- Atomic cleanup operations

---

## The V1 Journey

**Timeline**: December 23-27, 2025 (PR #42)
**Outcome**: Production-ready 1.0.0 release

The final push to V1 involved extensive refinement, bug fixing, and quality improvements.

### Bug Fixes

Several critical issues were identified and resolved:

- **Enrichment Failures**: Fixed stage failures caused by model schema mismatches
- **Billing Display**: Corrected quota formatting in the billing command
- **YouTube Validation**: Fixed video data extraction and validation logic
- **Manual Review Duplicates**: Implemented deduplication in the review queue
- **Frozen Model Mutations**: Fixed attempts to modify immutable Pydantic models

### Feature Additions

New capabilities were added during the V1 push:

- **Query Cleaning**: Comprehensive query normalization for Songstats API searches
- **Keyword Validation**: Rejection of false positive matches (karaoke, instrumental, etc.)
- **ISRC Extraction**: Enhanced metadata extraction from Songstats responses
- **Topic Channel Fallback**: YouTube video extraction from Topic channels
- **Test Mode**: Mock clients and track limiting for development/testing

### Code Quality Improvements

Significant quality improvements were made:

- **Cyclomatic Complexity**: Reduced in transform methods across pipeline stages
- **Lazy Logging**: Migrated all logging to placeholder-based format
- **Observer Helper**: Added helper method for consistent event emission
- **Cache Optimization**: Single-pass statistics collection
- **Path Consolidation**: Unified path validation using path_utils

### Test Suite Reorganization

The test suite was restructured into a modular directory layout:

```
_tests/
├── conftest.py           # Shared fixtures
├── fixtures/             # Test data files
├── unit/                 # Unit tests by module
│   ├── analysis/
│   ├── clients/
│   ├── commands/
│   ├── config/
│   ├── models/
│   ├── pipeline/
│   ├── storage/
│   └── utils/
└── integration/          # Integration tests
```

---

## Release 1.0.0

**Date**: December 27, 2025
**Commit**: e17616a (version bump) → a9b28bd (PR #42 merge)

### Final Metrics

| Metric          | Value                                          |
|-----------------|------------------------------------------------|
| Total Tests     | 1097                                           |
| Test Coverage   | 94%                                            |
| CLI Commands    | 7                                              |
| Package Modules | 12 submodules                                  |
| Pydantic Models | 17                                             |
| Design Patterns | 4 (Repository, Strategy, Observer, Checkpoint) |

### Module Coverage

| Module    | Tests | Coverage |
|-----------|-------|----------|
| config/   | 24    | 100%     |
| utils/    | 75    | 100%     |
| clients/  | 123   | 100%     |
| models/   | 150+  | 97-100%  |
| pipeline/ | 280+  | 91-100%  |
| analysis/ | 140+  | 94-100%  |
| storage/  | 120+  | 91-94%   |
| commands/ | 76    | 91-97%   |
| cli.py    | 22    | 91%      |

### Package Structure

```
msc/
├── __init__.py         # Package version
├── cli.py              # Typer CLI entry point
├── analysis/           # Normalization strategies & scorer
├── clients/            # MusicBee, Songstats, YouTube clients
├── commands/           # CLI utilities
├── config/             # Pydantic settings & constants
├── models/             # Pydantic data models
├── pipeline/           # ETL stages & orchestrator
├── storage/            # Repository pattern & checkpointing
└── utils/              # Logging, retry, text, path security
```

---

## Architectural Highlights

### Design Patterns

The codebase employs four primary design patterns:

1. **Repository Pattern**: Abstracts data persistence, allowing the pipeline to remain agnostic of storage details
2. **Strategy Pattern**: Enables pluggable normalization algorithms without modifying the scorer
3. **Observer Pattern**: Decouples progress tracking from pipeline execution
4. **Checkpoint Pattern**: Provides fault tolerance and resumability

### Security Considerations

- **Path Validation**: All file operations use `validate_path_within_base()` to prevent path traversal attacks
- **Credential Management**: API keys loaded from environment or secure token files
- **Input Sanitization**: Query strings cleaned before API calls

### Quality Assurance

- **PEP 8/257 Compliance**: Consistent code style throughout
- **Lazy Logging**: Placeholder-based logging for performance
- **DeepSource Integration**: Automated code quality analysis
- **Comprehensive Testing**: Unit and integration tests for all modules

### Legacy Preservation

Key elements from the legacy pipeline were preserved:

- **Scoring Algorithm**: The power ranking algorithm matches the original Jupyter notebook
- **Text Utilities**: `format_title`, `remove_remixer` adapted from legacy scripts
- **API Integration**: Same Songstats endpoints with enhanced error handling
- **Platform Coverage**: All 10 original platforms supported

---

## Looking Forward

### Current Status

Version 1.0.0 represents a stable, production-ready release. The codebase is well-tested, documented, and maintainable.
All legacy functionality has been migrated to the new architecture.

### Maintenance

The project is configured for ongoing maintenance:

- **Dependabot**: Monitors dependencies for updates
- **GitHub Actions**: CI/CD for test execution and coverage reporting
- **DeepSource**: Continuous code quality analysis

### Potential Enhancements

Future development could explore:

- **Additional Export Formats**: Excel (XLSX), PDF reports
- **Web Dashboard**: Interactive visualization of rankings
- **Scheduled Execution**: Automated pipeline runs via cron/scheduler
- **Additional Platforms**: Integration with emerging streaming services
- **Historical Analysis**: Trend tracking across multiple pipeline runs
- **API Rate Limit Optimization**: Adaptive rate limiting based on quota availability

---

> *Document created: December 2025*  
*Project: music-charts (msc) v1.0.0*
