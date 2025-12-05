# music-charts

[![DeepSource](https://app.deepsource.com/gh/Dyl-M/music-charts.svg/?label=code+coverage&show_trend=true&token=w0Cma8yAE6F5DyZ3EUjnGCfH)](https://app.deepsource.com/gh/Dyl-M/music-charts/)
[![DeepSource](https://app.deepsource.com/gh/Dyl-M/music-charts.svg/?label=active+issues&show_trend=true&token=w0Cma8yAE6F5DyZ3EUjnGCfH)](https://app.deepsource.com/gh/Dyl-M/music-charts/)
[![GitHub last commit](https://img.shields.io/github/last-commit/Dyl-M/music-charts?label=Last%20Commit&style=flat-square&logo=git&logoColor=white)](https://github.com/Dyl-M/music-charts/branches)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/w/Dyl-M/music-charts?label=Commit%20Activity&style=flat-square&logo=git&logoColor=white)](https://github.com/Dyl-M/music-charts/branches)

Data pipeline for analyzing track performance across streaming platforms and generating power rankings.

## Overview

Music-charts processes electronic music tracks from a MusicBee library, enriches them with data from the [Songstats API](https://songstats.com/), and generates power rankings based on weighted metrics across 10 platforms: Spotify, Apple Music, YouTube, Deezer, TikTok, Beatport, Tidal, SoundCloud, Amazon Music, and 1001Tracklists.

## Status

**Current:** Legacy ETL pipeline (4-stage process with standalone scripts)

**In Progress:** Modular architecture revamp for EOY 2025 Recap - see [`_docs/IMPROVEMENTS.md`](_docs/IMPROVEMENTS.md)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run pipeline stages sequentially
cd src && python data-mining-prep.py      # Stage 1: Extract & search
cd src && python data-mining-sstats.py    # Stage 2: Fetch platform stats
cd src && python data-mining-completion.py # Stage 3: YouTube enrichment
jupyter notebook notebooks/power_ranking_2024.ipynb  # Stage 4: Analysis
```

## Documentation

- [`CLAUDE.md`](CLAUDE.md) - Technical architecture and conventions
- [`_docs/IMPROVEMENTS.md`](_docs/IMPROVEMENTS.md) - Modular revamp roadmap

## License

This project is licensed under the [MIT License](LICENSE) - Copyright (c) 2024-2025 Dylan "Dyl-M" Monfret.
