# Music-Charts Revamp: Modular Architecture Plan

> **Goal:** Transform the current monolithic ETL pipeline into a modular, extensible system ready for EOY 2025 Recap and
> future web app integration.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Target Architecture](#target-architecture)
3. [Module Breakdown](#module-breakdown)
4. [Implementation Phases](#implementation-phases)
5. [Web App Considerations](#web-app-considerations)
6. [Migration Strategy](#migration-strategy)

---

## Current State Analysis

### Existing Pipeline

```
data-mining-prep.py → data-mining-sstats.py → data-mining-completion.py → notebook
```

### Pain Points

| Issue                    | Impact                                          | Priority |
|--------------------------|-------------------------------------------------|----------|
| Hardcoded paths & IDs    | Cannot run on different machines/years          | Critical |
| Duplicate API logic      | Maintenance burden, inconsistent error handling | High     |
| No logging/retry         | Silent failures, debugging difficulty           | High     |
| Scattered credentials    | Security risk, repetitive code                  | Medium   |
| Notebook-based analysis  | Not programmatically accessible                 | Medium   |
| No data validation       | Runtime errors from malformed data              | Medium   |
| Year-specific file names | Manual updates each year                        | Low      |

---

## Target Architecture

### Directory Structure

```
music-charts/
├── _config/
│   ├── config.yaml                # Runtime configuration
│   ├── weights.yaml               # Scoring weights (editable)
│   └── platforms.yaml             # Platform definitions
│
├── _data/
│   ├── input/                     # Source data
│   ├── output/                    # Generated artifacts
│   │   └── {year}/                # Year-specific outputs
│   └── cache/                     # API response cache
│
├── _legacy/                       # Archived original scripts
│   ├── src/                       # Original source files
│   │   ├── billing.py
│   │   ├── data-mining-prep.py
│   │   ├── data-mining-sstats.py
│   │   └── data-mining-completion.py
│   └── notebooks/                 # Original notebooks
│       └── power_ranking_2024.ipynb
│
├── _notebooks/                    # Exploratory analysis only
│
├── _tests/                        # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
│
├── _tokens/                       # Credentials (gitignored)
│
├── msc/                           # Main package
│   ├── __init__.py
│   ├── config/                    # Configuration management
│   │   ├── __init__.py
│   │   ├── settings.py            # Environment & runtime config
│   │   └── constants.py           # Static values (platforms, weights)
│   │
│   ├── clients/                   # External API clients
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base client
│   │   ├── songstats.py           # Songstats API wrapper
│   │   ├── youtube.py             # YouTube Data API wrapper
│   │   └── musicbee.py            # MusicBee library reader
│   │
│   ├── models/                    # Data models & schemas
│   │   ├── __init__.py
│   │   ├── track.py               # Track dataclass
│   │   ├── stats.py               # Platform statistics models
│   │   └── ranking.py             # Power ranking model
│   │
│   ├── pipeline/                  # ETL pipeline stages
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract pipeline stage
│   │   ├── extract.py             # Stage 1: Track extraction
│   │   ├── enrich.py              # Stage 2: Stats enrichment
│   │   ├── youtube.py             # Stage 3: YouTube data
│   │   └── rank.py                # Stage 4: Power ranking
│   │
│   ├── analysis/                  # Analytics & scoring
│   │   ├── __init__.py
│   │   ├── normalizer.py          # MinMaxScaler wrapper
│   │   ├── scorer.py              # Weighted scoring logic
│   │   └── visualizer.py          # Plotly chart generation
│   │
│   ├── storage/                   # Data persistence
│   │   ├── __init__.py
│   │   ├── json_store.py          # JSON file operations
│   │   ├── csv_store.py           # CSV export
│   │   └── cache.py               # API response caching
│   │
│   ├── utils/                     # Shared utilities
│   │   ├── __init__.py
│   │   ├── text.py                # Title formatting, cleaning
│   │   ├── retry.py               # Retry decorator with backoff
│   │   └── logging.py             # Structured logging setup
│   │
│   ├── cli.py                     # CLI entry point
│   └── api.py                     # Future: FastAPI web server
│
├── pyproject.toml                 # Modern Python packaging
└── README.md
```

---

## Module Breakdown

### 1. Configuration (`msc/config/`)

**settings.py**

```python
from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Paths
    musicbee_library: Path
    data_dir: Path = Path("_data")
    tokens_dir: Path = Path("_tokens")

    # Filters
    year: int = 2025
    playlist_id: str = "4361"

    # API
    songstats_rate_limit: int = 10  # requests/second
    youtube_quota_daily: int = 10000

    class Config:
        env_file = ".env"
        env_prefix = "MSC_"
```

**constants.py**

```python
from enum import Enum


class Platform(str, Enum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "appleMusic"
    YOUTUBE = "youtube"
    DEEZER = "deezer"
    TIKTOK = "tiktok"
    BEATPORT = "beatport"
    TIDAL = "tidal"
    SOUNDCLOUD = "soundcloud"
    AMAZON = "amazonMusic"
    TRACKLISTS = "1001tracklists"


class StatCategory(str, Enum):
    CHARTS = "charts"
    ENGAGEMENT = "engagement"
    PLAYLISTS = "playlists"
    POPULARITY = "popularity"
    PROFESSIONAL = "professional_support"
    REACH = "reach"
    SHORTS = "shorts"
    STREAMS = "streams"


# Weight multipliers
CATEGORY_WEIGHTS = {
    StatCategory.CHARTS: 1,  # Negligible
    StatCategory.ENGAGEMENT: 1,  # Negligible
    StatCategory.SHORTS: 1,  # Negligible
    StatCategory.REACH: 2,  # Low
    StatCategory.PLAYLISTS: 2,  # Low
    StatCategory.PROFESSIONAL: 2,  # Low
    StatCategory.POPULARITY: 4,  # High
    StatCategory.STREAMS: 4,  # High
}
```

### 2. API Clients (`msc/clients/`)

**base.py**

```python
from abc import ABC, abstractmethod
from typing import Any
import logging


class BaseClient(ABC):
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity."""
        pass

    @abstractmethod
    def get_quota(self) -> dict[str, Any]:
        """Return current quota/billing status."""
        pass
```

**songstats.py**

```python
from msc.clients.base import BaseClient
from msc.utils.retry import retry_with_backoff
from msc.models.track import Track
from msc.models.stats import PlatformStats


class SongstatsClient(BaseClient):
    BASE_URL = "https://api.songstats.com/enterprise/v1"

    @retry_with_backoff(max_retries=3)
    def search(self, title: str, artist: str) -> list[dict]:
        """Search for track by title and artist."""
        ...

    @retry_with_backoff(max_retries=3)
    def get_stats(self, songstats_id: str, platforms: list[str]) -> PlatformStats:
        """Fetch statistics for a track across platforms."""
        ...

    @retry_with_backoff(max_retries=3)
    def get_peaks(self, songstats_id: str, platform: str) -> dict:
        """Get historical peak metrics."""
        ...

    def get_billing(self) -> dict:
        """Check API billing/quota status."""
        ...
```

### 3. Data Models (`msc/models/`)

**track.py**

```python
from dataclasses import dataclass, field
from datetime import date


@dataclass
class Track:
    title: str
    artists: list[str]
    label: str | None = None
    genre: str | None = None
    release_date: date | None = None
    songstats_id: str | None = None
    isrc: str | None = None

    @property
    def search_query(self) -> str:
        return f"{self.artists[0]} - {self.title}"

    def to_dict(self) -> dict:
        ...

    @classmethod
    def from_musicbee(cls, entry: dict) -> "Track":
        ...
```

**stats.py**

```python
from dataclasses import dataclass
from typing import Optional


@dataclass
class PlatformStats:
    platform: str
    streams: int = 0
    playlist_reach: int = 0
    playlist_count: int = 0
    chart_peak: Optional[int] = None
    popularity_peak: Optional[int] = None
    shazams: int = 0

    def to_flat_dict(self) -> dict[str, int]:
        """Flatten for DataFrame compatibility."""
        ...
```

### 4. Pipeline Stages (`msc/pipeline/`)

**base.py**

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar, Generic
import logging

T = TypeVar("T")
U = TypeVar("U")


class PipelineStage(ABC, Generic[T, U]):
    """Base class for all pipeline stages."""

    def __init__(self, input_path: Path | None = None, output_path: Path | None = None):
        self.input_path = input_path
        self.output_path = output_path
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def extract(self) -> T:
        """Load input data."""
        pass

    @abstractmethod
    def transform(self, data: T) -> U:
        """Process data."""
        pass

    @abstractmethod
    def load(self, data: U) -> None:
        """Save output data."""
        pass

    def run(self) -> U:
        """Execute the full ETL cycle."""
        self.logger.info(f"Starting {self.__class__.__name__}")
        raw = self.extract()
        transformed = self.transform(raw)
        self.load(transformed)
        self.logger.info(f"Completed {self.__class__.__name__}")
        return transformed
```

**extract.py**

```python
from msc.pipeline.base import PipelineStage
from msc.clients.musicbee import MusicBeeClient
from msc.clients.songstats import SongstatsClient
from msc.models.track import Track


class ExtractionStage(PipelineStage[list[dict], list[Track]]):
    """Stage 1: Extract tracks from MusicBee and search Songstats."""

    def __init__(self, musicbee: MusicBeeClient, songstats: SongstatsClient, **kwargs):
        super().__init__(**kwargs)
        self.musicbee = musicbee
        self.songstats = songstats

    def extract(self) -> list[dict]:
        return self.musicbee.get_playlist_tracks(self.config.playlist_id)

    def transform(self, data: list[dict]) -> list[Track]:
        tracks = []
        for entry in data:
            track = Track.from_musicbee(entry)
            # Search for Songstats ID
            results = self.songstats.search(track.title, track.artists[0])
            if results:
                track.songstats_id = results[0]["songstats_id"]
            tracks.append(track)
        return tracks

    def load(self, data: list[Track]) -> None:
        # Save to JSON via storage module
        ...
```

### 5. Analysis (`msc/analysis/`)

**scorer.py**

```python
from msc.config.constants import StatCategory, CATEGORY_WEIGHTS
from msc.models.stats import PlatformStats
import pandas as pd
from sklearn.preprocessing import MinMaxScaler


class PowerRankingScorer:
    def __init__(self, weights: dict[StatCategory, int] | None = None):
        self.weights = weights or CATEGORY_WEIGHTS
        self.scaler = MinMaxScaler(feature_range=(0, 100))

    def compute_category_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize and weight each category."""
        ...

    def compute_power_ranking(self, df: pd.DataFrame) -> pd.Series:
        """Calculate final weighted power ranking."""
        ...

    def rank_tracks(self, tracks: list[dict]) -> pd.DataFrame:
        """Full ranking pipeline: normalize → weight → rank."""
        ...
```

### 6. CLI Entry Point (`msc/cli.py`)

```python
import typer
from pathlib import Path
from msc.config.settings import Settings
from msc.pipeline import ExtractionStage, EnrichmentStage, YouTubeStage, RankingStage

app = typer.Typer(name="msc")


@app.command()
def run(
        year: int = typer.Option(2025, help="Target year for analysis"),
        stages: list[str] = typer.Option(["all"], help="Stages to run"),
        config: Path = typer.Option("_config/config.yaml", help="Config file path"),
):
    """Run the music charts pipeline."""
    settings = Settings(year=year)

    if "all" in stages or "extract" in stages:
        ExtractionStage(settings).run()

    if "all" in stages or "enrich" in stages:
        EnrichmentStage(settings).run()

    if "all" in stages or "youtube" in stages:
        YouTubeStage(settings).run()

    if "all" in stages or "rank" in stages:
        RankingStage(settings).run()


@app.command()
def billing():
    """Check Songstats API billing status."""
    ...


@app.command()
def validate(input_file: Path):
    """Validate a data file against schema."""
    ...


if __name__ == "__main__":
    app()
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)

- [ ] Set up `pyproject.toml` with modern packaging
- [ ] Create `config/` module with Settings and Constants
- [ ] Implement `utils/` (logging, retry, text helpers)
- [ ] Create base classes for clients and pipeline stages
- [ ] Set up basic test structure

### Phase 2: API Clients (Week 2-3)

- [ ] Implement `SongstatsClient` with all current API calls
- [ ] Implement `YouTubeClient` with OAuth flow
- [ ] Implement `MusicBeeClient` for library parsing
- [ ] Add response caching layer
- [ ] Write integration tests for each client

### Phase 3: Data Models (Week 3)

- [ ] Define `Track`, `PlatformStats`, `Ranking` dataclasses
- [ ] Add JSON serialization/deserialization
- [ ] Implement schema validation (Pydantic or dataclass-json)
- [ ] Ensure backward compatibility with existing JSON files

### Phase 4: Pipeline Migration (Week 4-5)

- [ ] Migrate `data-mining-prep.py` → `ExtractionStage`
- [ ] Migrate `data-mining-sstats.py` → `EnrichmentStage`
- [ ] Migrate `data-mining-completion.py` → `YouTubeStage`
- [ ] Extract notebook logic → `RankingStage` + `PowerRankingScorer`
- [ ] Verify outputs match original pipeline

### Phase 5: CLI & Polish (Week 5-6)

- [ ] Implement Typer CLI with all commands
- [ ] Add progress bars (rich/tqdm integration)
- [ ] Comprehensive error handling and logging
- [ ] Documentation and usage examples
- [ ] Performance optimization (async where beneficial)

---

## Web App Considerations

### API Design (Future `api.py`)

```python
from fastapi import FastAPI, BackgroundTasks
from msc.pipeline import Pipeline
from msc.models import Track, Ranking

app = FastAPI(title="Music Charts API")


@app.get("/tracks/{year}")
async def get_tracks(year: int) -> list[Track]:
    """List all tracks for a given year."""
    ...


@app.get("/rankings/{year}")
async def get_rankings(year: int) -> list[Ranking]:
    """Get power rankings for a given year."""
    ...


@app.post("/pipeline/run")
async def run_pipeline(year: int, stages: list[str], background_tasks: BackgroundTasks):
    """Trigger pipeline execution (async)."""
    background_tasks.add_task(Pipeline(year).run, stages)
    return {"status": "started"}


@app.get("/stats/{songstats_id}")
async def get_track_stats(songstats_id: str) -> dict:
    """Fetch real-time stats for a specific track."""
    ...
```

### Database Consideration

For web app scalability, consider migrating from JSON files to:

| Option         | Pros                                     | Cons                               |
|----------------|------------------------------------------|------------------------------------|
| **SQLite**     | Zero config, portable, good for reads    | Single writer, limited concurrency |
| **PostgreSQL** | Full-featured, JSONB support             | Requires server                    |
| **DuckDB**     | Excellent for analytics, Pandas-friendly | Newer, less tooling                |

**Recommendation:** Start with SQLite + SQLAlchemy ORM for easy migration path.

### Caching Strategy

```python
# Redis or file-based cache for API responses
@cache(ttl=3600)  # 1 hour
def get_track_stats(songstats_id: str) -> dict:
    return client.get_stats(songstats_id)
```

---

## Migration Strategy

### Backward Compatibility

1. **Keep existing scripts** in `_legacy/` during transition
2. **Output format unchanged** - new modules produce identical JSON structure
3. **Gradual migration** - replace one stage at a time, verify outputs match

### Testing Approach

```python
# Compare new vs old outputs
def test_extraction_matches_legacy():
    legacy_output = json.load(open("_data/selection_2024.json"))
    new_output = ExtractionStage().run()

    assert len(new_output) == len(legacy_output)
    for old, new in zip(legacy_output, new_output):
        assert old["title"] == new.title
        assert old["songstats_identifiers"]["songstats"] == new.songstats_id
```

### Rollback Plan

If issues arise:

1. Legacy scripts remain functional
2. Config toggle: `USE_LEGACY_PIPELINE=true`
3. Data format unchanged, so outputs are interchangeable

---

## Quick Start (Post-Migration)

```bash
# Install
pip install -e .

# Configure
cp _config/config.example.yaml _config/config.yaml
# Edit config.yaml with your paths

# Run full pipeline
msc run --year 2025

# Run specific stages
msc run --year 2025 --stages extract enrich

# Check API quota
msc billing

# Export rankings
msc export --year 2025 --format csv
```

---

## Open Questions

1. **Async vs Sync:** Should API clients be async for better performance?
2. **Database:** Is SQLite sufficient, or plan for PostgreSQL from the start?
3. **Authentication:** How will the web app handle user auth (if needed)?
4. **Hosting:** Target deployment platform (Vercel, Railway, self-hosted)?
5. **Historical Data:** Should we re-process 2024 data with the new pipeline?

---

## Progress Tracker

### Completed

- [x] Initial architecture design and documentation
- [x] Directory structure defined with underscore-prefixed support folders
- [x] Module breakdown with code examples
- [x] Implementation phases outlined
- [x] Web app considerations documented
- [x] Migration strategy defined

### Next Steps

1. Create `pyproject.toml` with package configuration
2. Set up `msc/` package skeleton
3. Move legacy scripts to `_legacy/`
4. Implement `msc/config/` module

---

*Last updated: December 2024*
