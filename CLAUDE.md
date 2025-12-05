# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Music-charts is a data pipeline for analyzing track performance across streaming platforms (Spotify, Apple Music, YouTube, Deezer, TikTok, Beatport, Tidal, SoundCloud, Amazon Music, 1001Tracklists). It processes electronic music tracks from a MusicBee library, enriches them with Songstats API data, and generates power rankings based on weighted metrics.

**Status:** Active refactoring toward modular architecture (see `_docs/IMPROVEMENTS.md`)

## Commands (Legacy Pipeline)

```bash
# Install dependencies
pip install -r requirements.txt

# Check Songstats API billing/quota
cd src && python billing.py

# Stage 1: Extract tracks from MusicBee, search via Songstats API
cd src && python data-mining-prep.py

# Stage 2: Fetch comprehensive stats from Songstats API
cd src && python data-mining-sstats.py

# Stage 3: Enrich with YouTube data (requires browser OAuth on first run)
cd src && python data-mining-completion.py

# Stage 4: Run analysis notebook
jupyter notebook notebooks/power_ranking_2024.ipynb
```

No test suite exists yet.

## Architecture

### Current Structure

```
music-charts/
├── src/                    # Legacy pipeline scripts
│   ├── billing.py          # API quota check
│   ├── data-mining-prep.py # Stage 1: Track extraction
│   ├── data-mining-sstats.py # Stage 2: Stats fetching
│   └── data-mining-completion.py # Stage 3: YouTube enrichment
├── data/                   # JSON artifacts & outputs
├── notebooks/              # Jupyter analysis (Stage 4)
├── tokens/                 # Credentials (gitignored)
├── notes/                  # Draft notes
└── _docs/                  # Project documentation
    └── IMPROVEMENTS.md     # Modular architecture roadmap
```

### Target Structure (In Progress)

See `_docs/IMPROVEMENTS.md` for the planned `msc/` package structure with:
- `_config/`, `_data/`, `_legacy/`, `_notebooks/`, `_tests/`, `_tokens/` (support folders)
- `msc/` main package with `clients/`, `models/`, `pipeline/`, `analysis/`, `storage/`, `utils/`

### Multi-Stage ETL Pipeline

Each stage produces JSON artifacts and can run independently:

1. **data-mining-prep.py** → `selection_2024.json` (track metadata with Songstats IDs)
2. **data-mining-sstats.py** → `data_2024.json` (platform stats for all tracks)
3. **data-mining-completion.py** → `ytb_2024.json` (YouTube-specific data)
4. **power_ranking_2024.ipynb** → `power_ranking_2024.csv` (final rankings)

### Data Flow

- MusicBee library XML (hardcoded: `E:/Musique/MusicBee/iTunes Music Library.xml`) filtered by DJ playlist ID '4361'
- Songstats API provides track search and multi-platform statistics
- YouTube Data API validates video sources and fetches view counts
- Jupyter notebook applies MinMaxScaler normalization and weighted scoring across categories

### Weighted Scoring System

- **Negligible (×1):** Charts, Engagement, Shorts
- **Low (×2):** Reach, Playlists, Professional Support
- **High (×4):** Popularity, Streams

## Required Credentials

All stored in `tokens/` (gitignored):
- `songstats_key.txt` - Songstats Enterprise API key
- `oauth.json` - Google OAuth 2.0 client secrets
- `credentials.json` - Cached Google API tokens (auto-generated)

## Key Conventions

- API failures return empty dicts/lists (defensive coding)
- UTF-8 encoding explicit on all file operations
- `data-mining-prep.py` checks for duplicates before re-querying API
- Pandas display options set for full DataFrame visibility in notebooks
- Environment prefix for future config: `MSC_`

## Refactoring Notes

When implementing the new modular architecture:
- Use underscore prefix for support folders (`_config/`, `_data/`, etc.)
- Main package name: `msc`
- Preserve backward compatibility with existing JSON output formats
- Legacy scripts will be archived in `_legacy/`
