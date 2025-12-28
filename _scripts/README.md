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