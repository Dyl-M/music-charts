# User Validation - Issues Found

This document contains all open and pending issues discovered during user validation testing for version 1.0.0.

## High Priority Issues

#### [ISSUE-015] `msc export` Command Failing

**Command**: `msc export`

**Description**:
The `msc export` command is not working properly during user validation testing. The exact error and failure mode need
to be investigated.

**Steps to Reproduce**:

1. Run `msc export --year 2025`
2. Observe the error/failure

**Expected Behavior**:

- Command should export enriched track data to CSV format (default)
- Should handle ODS and HTML formats with appropriate flags
- Should display export summary with row count, file size, and duration

**Actual Behavior**:

The `msc export` command has multiple critical issues:

1. **Wrong file path** (`msc/cli.py:408`):
    - Tries to load from: `settings.year_output_dir / "stats.json"` (e.g., `_data/output/2025/stats.json`)
    - Should load from: `settings.output_dir / "enriched_tracks.json"` (e.g., `_data/output/enriched_tracks.json`)
    - Results in file not found or loading wrong data

2. **Missing data flattening method**:
    - `TrackWithStats` model lacks `to_flat_dict()` method for proper CSV export
    - When exporting to CSV, nested Pydantic models are converted to string representations
    - Results in CSV cells containing Python dict strings like: `{'songstats_id': 'xxx', 'api_track_id': 'xxx'}`
    - Instead of proper flat columns: `songstats_id, api_track_id`

3. **Nested structures not properly flattened**:
    - `TrackWithStats` has nested structure: `track`, `songstats_identifiers`, `platform_stats`, `youtube_data`
    - Each platform in `platform_stats` has nested objects (e.g., `spotify.streams_total`, `youtube.video_views_total`)
    - Export shows nested dicts as strings instead of creating flat column structure
    - Makes exported data unreadable and unusable for analysis

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (blocks data export functionality for 1.0.0)

**Location in Code**:

- `msc/cli.py:366-467` - Export command implementation
- `msc/commands/exporters.py` - DataExporter class

**Notes**:

- Requires investigation to determine root cause
- May be related to missing data files or incorrect path resolution
- May be related to pandas/odfpy dependency issues

---

#### [ISSUE-016] `msc stats` Command Failing

**Command**: `msc stats`

**Description**:
The `msc stats` command has multiple critical issues that prevent it from working correctly:

1. **Incorrect file path**: Tries to load `_data/output/2025/stats.json` instead of `_data/output/enriched_tracks.json`
2. **Incorrect attribute names**: Uses wrong attribute names when checking platform data (e.g., `streams` instead of
   `streams_total`)
3. **Incorrect platform coverage logic**: Shows 100% coverage for all platforms due to checking `is not None` on fields
   that default to `0`
4. **Missing proper platform presence check**: Needs to verify actual data availability, not just non-None values

**Steps to Reproduce**:

1. Run `msc stats --year 2025`
2. Observe the error/failure

**Expected Behavior**:

- Command should display dataset statistics for the specified year
- Should show total track count
- Should show platform coverage with track counts and percentages
- Should handle missing data gracefully

**Actual Behavior**:

The `msc stats` command has multiple critical issues:

1. **Wrong file path** (`msc/cli.py:598-599`):
    - Tries to load from: `settings.year_output_dir / "stats.json"` (e.g., `_data/output/2025/stats.json`)
    - Should load from: `settings.output_dir / "enriched_tracks.json"` (e.g., `_data/output/enriched_tracks.json`)
    - Results in file not found (0 tracks loaded)

2. **Wrong platform attribute names** (`msc/cli.py:559-565`):
    - Uses `"streams"` instead of `"streams_total"` for Spotify
    - Uses `"views"` instead of `"video_views_total"` for YouTube
    - Uses `"fans"` instead of `"playlist_reach_total"` for Deezer
    - Results in platform objects not being found (always None)

3. **Flawed platform presence detection** (`msc/cli.py:545-546`):
   ```python
   platform = getattr(track.platform_stats, platform_attr, None)
   return platform is not None and getattr(platform, stat_attr, None) is not None
   ```
    - Logic checks `is not None` which returns `True` for `0` values
    - Platform stats default to `0`, not `None`, for missing data
    - Results in false 100% coverage for all platforms (counts tracks with 0 streams as "has data")

4. **Missing proper data availability check**:
    - Current logic only checks if a single field is not None
    - Should check if ANY field in the platform object has meaningful non-zero data
    - Example: A track with 0 Spotify streams, 0 followers should count as "no Spotify data"

5. **Missing popularity_peak data**:
    - Investigation shows 0 tracks have popularity_peak fields populated
    - Despite enrichment code that calls `get_historical_peaks()` and merges peaks
    - All popularity_peak fields show None or 0 across entire dataset
    - Indicates API call may be failing silently or merge logic not working

**User-reported symptoms**:

- "stats kinda returns nothing (0 track retrieved, while it's false)"
- "Stats shows 100% coverage for all platforms"

**Data verification** (from enriched_tracks.json):

- Total tracks in file: 329
- Tracks with Spotify streams > 0: 319 (97.0%)
- Tracks with YouTube views > 0: 312 (94.8%)
- But stats command shows: 0 tracks loaded, 0% coverage (wrong file path)

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (blocks analytics functionality for 1.0.0)

**Location in Code**:

- `msc/cli.py:573-630` - Stats command implementation
- Helper functions: `_has_platform_data()`, `_count_platform_tracks()`

**Notes**:

- Requires investigation to determine root cause
- May be related to missing data files or incorrect path resolution
- May be related to TrackWithStats model structure

---

#### [ISSUE-017] Power Ranking Scores Not in 0-100 Range (Design Issue)

**Command**: `msc run --stage rank`

**Description**:
The power ranking scores by category are not in the expected 0-100 range as they were in the legacy implementation. The
current normalization strategy may be producing scores in a different range (e.g., 0-1), which affects readability and
comparison with historical rankings.

**Expected Behavior**:

- Category scores (Popularity, Streams, Charts, etc.) should be normalized to 0-100 range
- Total score should be weighted sum of category scores
- Scores should match legacy implementation behavior for consistency
- Normalization should use same algorithm as legacy (MinMaxScaler or equivalent)

**Actual Behavior**:

*To be documented after investigation of current scoring output*

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (affects data quality and comparison with legacy rankings)

**Location in Code**:

- `msc/analysis/scorer.py` - PowerRankingScorer implementation
- `msc/analysis/normalizers.py` - MinMaxNormalizer, ZScoreNormalizer, RobustNormalizer
- `msc/pipeline/rank.py` - RankingStage that uses scorer

**Root Cause**:

Likely a normalization strategy issue:

- MinMaxNormalizer may be producing 0-1 range instead of 0-100
- Scores may need to be multiplied by 100 after normalization
- Or normalizer may need a `feature_range=(0, 100)` parameter

**Impact**:

- Rankings are technically correct but scores are harder to interpret
- Can't compare directly with legacy rankings
- User experience is degraded (scores like 0.85 vs 85.0)

**Files to Modify**:

- `msc/analysis/normalizers.py` - Update MinMaxNormalizer to support 0-100 range
- `msc/analysis/scorer.py` - Ensure scores are in 0-100 range
- `msc/pipeline/rank.py` - Verify normalization configuration

**Testing Requirements**:

- Verify category scores are in 0-100 range
- Verify total scores match legacy implementation
- Update tests to expect 0-100 range instead of 0-1

---

#### [ISSUE-018] Missing YouTube Data Despite Songstats Data Availability

**Command**: `msc run --stage enrich`

**Description**:
Some tracks are not being enriched with YouTube data even though minimal YouTube data appears to exist in the Songstats
API response. The enrichment logic may be too strict in validation or may not be extracting all available YouTube data.

**Expected Behavior**:

- All tracks with any YouTube presence in Songstats should have YouTube data
- YouTube data should be extracted even if minimal/incomplete
- Tracks with no YouTube data should be clearly identified vs validation failures

**Actual Behavior**:

*To be documented after investigation of enrichment logs and Songstats responses*

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (affects data completeness)

**Location in Code**:

- `msc/pipeline/enrich.py:207-228` - YouTube data extraction and validation
- `msc/clients/songstats.py` - YouTube video fetching from Songstats API

**Possible Root Causes**:

1. Validation may be too strict (requires all fields: ytb_id, views, channel_name)
2. Songstats API may return partial YouTube data that's being rejected
3. API response structure may vary and code doesn't handle all cases

**Investigation Needed**:

- Review Songstats API responses for tracks without YouTube data
- Check if partial YouTube data exists but is rejected by validation
- Determine if validation should be more permissive

**Related Issues**:

- See ISSUE-007: Enrichment Stage Failing on Empty YouTube Data (fixed, but related)

---

#### [ISSUE-019] Power Ranking Weights Not Adjusted from Data Availability

**Command**: `msc run --stage rank`

**Description**:
The power ranking weights are static and do not adjust based on actual data availability from each platform. The legacy
implementation adjusted weights based data availability rate on which platforms, ensuring fair comparison between tracks
with different platform coverage.

**Expected Behavior**:

- Weights should be dynamically adjusted per stat based on data availability
- If popularity_peak from Deezer is available for 50% of the database (tracks existing withing Songstats DB), then the
  weight for Deezer's popularity_peak should multiplied by 0.5
- Matches legacy implementation behavior

**Actual Behavior**:

- Weights are static for all tracks regardless of data availability

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (affects ranking fairness and accuracy)

**Location in Code**:

- `msc/analysis/scorer.py` - PowerRankingScorer implementation
- `msc/config/constants.py` - CATEGORY_WEIGHTS definition
- `msc/pipeline/rank.py` - RankingStage scoring logic

**Root Cause**:

The current implementation uses static weights from `CATEGORY_WEIGHTS` without adjusting for missing data:

```python
# Current: Static weights
category_weights = {
    StatCategory.POPULARITY: 4,  # High weight
    StatCategory.STREAMS: 4,  # High weight
    # ... etc
}
```

**Expected Implementation**:

```python
# TODO: to define properly
```

**Impact**:

- Rankings are biased toward tracks with more complete data
- Tracks with niche platform presence are unfairly penalized
- Can't fairly compare mainstream vs independent releases

**Files to Modify**:

```
# TODO: to analyze again
```

**Testing Requirements**:

- Verify tracks with missing data get fair scores

---

## Enhancement Requests

*Feature requests discovered during validation*

#### [ISSUE-005] Test Suite Runs on Full MusicBee Library

**Command**: `msc run` (during testing/development)

**Description**:
When testing pipeline features or running quick validations, the test suite processes the entire MusicBee library (373+
tracks), making iteration cycles extremely long. Additionally, each test run creates output files in `_data/` that are
not automatically cleaned up, leading to clutter and confusion about which outputs are current.

**Steps to Reproduce**:

1. Run `msc run` for testing
2. Wait for full library extraction and processing (several minutes)
3. Check `_data/runs/` - multiple run directories accumulate
4. Check `_data/output/` - outputs from multiple test runs remain

**Expected Behavior**:

* Option to run pipeline on a small subset of tracks for rapid testing
* Test mode that uses a fixture playlist with ~10-20 representative tracks
* Automatic cleanup of test run artifacts
* Clear separation between test runs and production runs

**Actual Behavior**:

* Every test run processes 373+ tracks regardless of purpose
* Test iterations take several minutes each
* `_data/runs/` accumulates multiple directories from testing
* No easy way to distinguish test outputs from production outputs
* Manual cleanup required between test runs

**Status**:

- [ ] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: Enhancement (not blocking, but significantly impacts development workflow)

**Proposed Solutions**:

1. **Test Playlist**: Create a dedicated small test playlist in MusicBee (e.g., "Test Selection 2025") with 10-20
   representative tracks
2. **CLI Flag**: Add `--test-mode` flag that uses test playlist and marks outputs
3. **Auto-cleanup**: Add `--cleanup-after` flag to delete run directory after completion
4. **Playlist Limit**: Add `--limit N` flag to process only first N tracks from any playlist
5. **Test Fixtures**: Use the existing `_tests/fixtures/test_library.xml` for integration tests instead of production
   library

**Expected Benefits**:

* Faster iteration during development (seconds instead of minutes)
* Cleaner `_data/` directory structure
* Easier to test specific features or edge cases
* Reduced API quota usage during testing

**Workaround**:

For now, manually create a small playlist in MusicBee for testing purposes and specify it with:

```bash
msc run --playlist "Test Playlist"
```

**Future Enhancements**:

* Add `msc test` command that automatically uses test fixtures
* Implement `--dry-run` mode that simulates pipeline without API calls
* Add `msc clean --test-runs` to remove all test-related artifacts
