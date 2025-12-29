# Utility Scripts

Standalone utility scripts for manual operations outside the main CLI pipeline.

## Scripts

### `manual_spotify_track_submission.py`

Submit manual track additions to Songstats API for tracks that couldn't be matched automatically.

**Usage:**

```bash
# Generate template from manual_review.json
python _scripts/manual_spotify_track_submission.py --generate

# Submit tracks (auto-detects input file)
python _scripts/manual_spotify_track_submission.py

# Submit with explicit input file
python _scripts/manual_spotify_track_submission.py _data/input/submissions.csv

# Enable debug logging
python _scripts/manual_spotify_track_submission.py --debug
```

**Workflow:**

1. Run pipeline to generate `manual_review.json` with unmatched tracks
2. Run `--generate` to create template at `_data/input/spotify_submission.json`
3. Fill in `songstats_artist_id` and `spotify_track_id` for each track
4. Run script without flags to submit

**Input format (JSON):**

```json
[
  {
    "track": "Artist - Title",
    "songstats_artist_id": "abc123",
    "spotify_track_id": "4uLU6hMCjMI75M1A2tKUQC"
  }
]
```

**Input format (CSV):**

```csv
songstats_artist_id,spotify_track_id
abc123,4uLU6hMCjMI75M1A2tKUQC
```

**Output:**

- Console: Real-time progress with success/pending/failure counts
- Log file: `_data/logs/manual_submissions.log`

**Options:**

| Flag          | Description                                 |
|---------------|---------------------------------------------|
| `--generate`  | Generate template from `manual_review.json` |
| `--debug`     | Enable debug logging (shows API responses)  |
| `--input-dir` | Override default input directory            |

---

### `manual_platform_coverage.py`

Manage platform coverage for enriched tracks. Identify which tracks are missing from which
platforms and maintain a whitelist for tracks confirmed as genuinely unavailable.

**Usage:**

```bash
# Show coverage summary (default)
python _scripts/manual_platform_coverage.py

# Generate/update coverage report from enriched tracks
python _scripts/manual_platform_coverage.py --generate

# Interactively add tracks to platform whitelist
python _scripts/manual_platform_coverage.py --add-to-whitelist

# Enable debug logging
python _scripts/manual_platform_coverage.py --generate --debug
```

**Workflow:**

1. Run pipeline to generate `enriched_tracks.json`
2. Run `--generate` to create coverage report at `_data/input/platform_coverage.json`
3. Review missing tracks per platform
4. Fill in `link` field for tracks you find on each platform
5. Run `--add-to-whitelist` to mark tracks as "confirmed not on platform"
6. Re-run `--generate` to update report with whitelist exclusions

**Output files:**

| File                                  | Description                                       |
|---------------------------------------|---------------------------------------------------|
| `_data/input/platform_coverage.json`  | Tracks missing from each platform with link field |
| `_data/input/platform_whitelist.json` | Per-platform skip lists for confirmed unavailable |
| `_data/logs/platform_coverage.log`    | Execution log                                     |

**Coverage JSON format:**

```json
{
  "spotify": [
    {
      "track_id": "f68b210b",
      "artist": "Disclosure",
      "title": "When A Fire Starts To Burn [Chime Flip]",
      "songstats_id": "em0th986",
      "link": []
    }
  ],
  "apple_music": [
    ...
  ]
}
```

> **Note:** All platforms use a list for the `link` field to support multiple sources per track.

**Whitelist JSON format:**

```json
{
  "spotify": [],
  "apple_music": [
    "track_id_1",
    "track_id_2"
  ],
  "deezer": []
}
```

**Options:**

| Flag                 | Description                                          |
|----------------------|------------------------------------------------------|
| `--generate`         | Generate/update coverage report from enriched tracks |
| `--add-to-whitelist` | Interactively add tracks to platform whitelist       |
| `--debug`            | Enable debug logging                                 |
| `--input`            | Custom path to enriched_tracks.json                  |

---

### `manual_link_submission.py`

Submit filled platform links from `platform_coverage.json` to Songstats API.

**Usage:**

```bash
# Show pending submissions (default)
python _scripts/manual_link_submission.py

# Submit all pending links
python _scripts/manual_link_submission.py --submit

# Submit links for specific platform only
python _scripts/manual_link_submission.py --submit --platform soundcloud

# Enable debug logging
python _scripts/manual_link_submission.py --submit --debug
```

**Workflow:**

1. Fill in `link` field(s) in `platform_coverage.json`
2. Run without flags to preview pending submissions
3. Run with `--submit` to send links to Songstats API

**Output:**

- Console: Real-time progress with success/pending/failure counts
- Log file: `_data/logs/link_submissions.log`

**Options:**

| Flag         | Description                                       |
|--------------|---------------------------------------------------|
| `--submit`   | Submit pending links to Songstats API             |
| `--platform` | Filter by specific platform (e.g., `soundcloud`)  |
| `--debug`    | Enable debug logging (shows API responses)        |
| `--input`    | Custom path to platform_coverage.json             |