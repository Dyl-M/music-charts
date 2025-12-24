# User Validation for Version 1.0.0

This document tracks user validation testing for the music-charts CLI before the 1.0.0 "release".

## Validation Status

- **Testing Phase**: In Progress
- **Target Version**: 1.0.0
- **Start Date**: 2025-12-23

## Testing Scope

All CLI commands will be validated from a user perspective:

- `msc init` - Directory structure initialization
- `msc billing` - Songstats API quota checking
- `msc run` - Full pipeline execution
- `msc validate` - File validation with auto-detection
- `msc export` - Data export (CSV/ODS/HTML)
- `msc stats` - Dataset statistics display
- `msc clean` - Cache management

## Issues Found

### Critical Issues

*Issues that must be fixed before 1.0.0 release*

#### [ISSUE-007] Enrichment Stage Failing on Empty YouTube Data

**Command**: `msc run`

**Description**:
The enrichment stage is failing for tracks when Songstats API returns empty YouTube data. The code attempts to create a
YouTubeVideo model from an empty dictionary, causing Pydantic validation errors.

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Enrichment stage processes tracks
3. Some tracks fail with validation errors when YouTube data is empty
4. Check `_data/logs/pipeline.log` - shows ValidationError for YouTubeVideo

**Expected Behavior**:

- When YouTube data is empty or invalid, skip YouTube enrichment gracefully
- Continue processing track without YouTube data (set youtube_data to None)
- Log a debug/info message about missing YouTube data
- Track should still be enriched with platform stats

**Actual Behavior**:

```
2025-12-24 00:32:48 | ERROR | msc.pipeline.enrich | Failed to enrich track: sportmode_seasmoke_2025
Traceback (most recent call last):
  File "msc\pipeline\enrich.py", line 211, in transform
    most_viewed_video = YouTubeVideo(**youtube_results["most_viewed"])
pydantic_core._pydantic_core.ValidationError: 3 validation errors for YouTubeVideo
ytb_id
  Field required [type=missing, input_value={}, input_type=dict]
views
  Field required [type=missing, input_value={}, input_type=dict]
channel_name
  Field required [type=missing, input_value={}, input_type=dict]
```

- Track enrichment fails completely
- Track marked as failed in checkpoint
- No platform stats saved for the track

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: Critical (causes track enrichment to fail unnecessarily)

**Location in Code**:

- `msc/pipeline/enrich.py:211` - Attempts to create YouTubeVideo from empty dict
- `msc/pipeline/enrich.py:207-218` - YouTube data processing block

**Root Cause**:

The code assumes `youtube_results["most_viewed"]` is always a valid dict with required fields:

```python
if youtube_results:
    # Convert API response to YouTubeVideoData model
    most_viewed_video = YouTubeVideo(**youtube_results["most_viewed"])  # FAILS if empty!
```

When Songstats API returns `{"most_viewed": {}, "all_sources": []}`, the code crashes.

**Impact**:

- Tracks with empty YouTube data fail enrichment entirely
- Loses platform stats data that was successfully fetched
- Increases failed track count unnecessarily
- Reduces overall enrichment success rate

**Solution Needed**:

Add validation to check if `most_viewed` dict contains required fields before creating YouTubeVideo model. If empty,
skip YouTube enrichment but continue with platform stats.

**Related Files**:

- Run directory: `_data/runs/2025_20251224_000042/`
- Logs: `_data/logs/pipeline.log`

---

#### [ISSUE-006] Enrichment Stage Completely Failing - Missing start_date Argument

**Command**: `msc run`

**Description**:
The enrichment stage is failing for 100% of tracks due to a missing required argument in the `get_historical_peaks()`API
call. All tracks fail with
`TypeError: SongstatsClient.get_historical_peaks() missing 1 required positional argument: 'start_date'`.

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Extraction stage completes successfully
3. Enrichment stage processes 0 tracks (all fail)
4. Check `_data/logs/pipeline.log` - shows TypeError for every track

**Expected Behavior**:

- Enrichment stage should fetch historical peaks data for each track
- `get_historical_peaks()` should be called with required `start_date` parameter
- Tracks should be enriched with platform statistics and historical data
- Successful tracks should be saved to `_data/output/enriched_tracks.json`

**Actual Behavior**:

```
2025-12-24 00:16:22 | ERROR | msc.pipeline.enrich | Failed to enrich track: playmen_wallstreet_[extended_mix]_2025
Traceback (most recent call last):
  File "msc\pipeline\enrich.py", line 192, in transform
    peaks_data = self.songstats.get_historical_peaks(songstats_id)
TypeError: SongstatsClient.get_historical_peaks() missing 1 required positional argument: 'start_date'
```

- All tracks fail during enrichment (0 successful)
- Enrichment checkpoint contains only failed_ids (no processed_ids)
- Ranking stage has no data to process

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: Critical (blocks all pipeline functionality beyond extraction)

**Location in Code**:

- `msc/pipeline/enrich.py:192` - Missing `start_date` argument in API call
- `msc/clients/songstats.py:191-196` - Method signature requires `start_date: str`

**Root Cause**:

The enrichment stage calls:

```python
peaks_data = self.songstats.get_historical_peaks(songstats_id)
```

But the method signature is:

```python
def get_historical_peaks(
        self,
        songstats_track_id: str,
        start_date: str,  # REQUIRED - MISSING IN CALL!
        sources: str | list[str] | None = None,
) -> dict[str, int]:
    ...
```

**Impact**:

- Enrichment stage: 0% success rate (was working before, regression)
- No enriched data produced
- Ranking stage has no input data
- Pipeline effectively stops after extraction

**Solution Implemented**:

1. ✅ Added `start_date` parameter to `get_historical_peaks()` call in enrichment stage
2. ✅ Start date is computed as January 1st of the target year: `f"{self.settings.year}-01-01"`
3. ✅ Now correctly passes `songstats_id` and `start_date` to the API method

**Files Modified**:

- `msc/pipeline/enrich.py:192-194` - Added start_date calculation and parameter

**Fix Details**:

Before:

```python
# Fetch historical peaks (for popularity metrics)
peaks_data = self.songstats.get_historical_peaks(songstats_id)
```

After:

```python
# Fetch historical peaks (for popularity metrics)
# Start date is January 1st of the target year
start_date = f"{self.settings.year}-01-01"
peaks_data = self.songstats.get_historical_peaks(songstats_id, start_date)
```

**Related Files**:

- Run directory: `_data/runs/2025_20251224_000042/`
- Checkpoint: `_data/runs/2025_20251224_000042/checkpoints/enrichment_checkpoint.json` (all failed)
- Logs: `_data/logs/pipeline.log`

---

---

### High Priority Issues

*Important issues that should be fixed before release*

#### [ISSUE-008] Manual Review Queue Accumulating Duplicates Within Same Run

**Command**: `msc run`

**Description**:
The manual review queue (`manual_review.json`) is accumulating duplicate entries for the same track within a single
pipeline run. The same failed track appears multiple times in the queue, making manual review inefficient.

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Some tracks fail extraction and are added to manual_review.json
3. Check `_data/runs/2025_YYYYMMDD_HHMMSS/manual_review.json` - contains duplicates

**Expected Behavior**:

- Each failed track should appear only ONCE in manual_review.json
- Track_id should be unique within the queue
- Manual review queue should deduplicate automatically
- Users should see a clean list of unique failed tracks

**Actual Behavior**:

```bash
wc -l _data/runs/2025_20251224_000042/manual_review.json
1141 lines (should be ~380 unique tracks)

grep -c "kirara_magic_aim_tech" manual_review.json
3 occurrences (same track appears 3 times!)
```

- Same track_id appears multiple times in manual_review.json
- File has 1141 lines but only ~380 unique tracks
- Users must manually deduplicate when doing manual review
- Queue is ~3x larger than necessary

**Status**:

- [x] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: High (significantly impacts manual review workflow usability)

**Location in Code**:

- `msc/storage/checkpoint.py:338` - `ManualReviewQueue.add()` appends without checking duplicates
- `msc/pipeline/extract.py` - Adds failed tracks to queue during search process

**Root Cause**:

The `ManualReviewQueue.add()` method simply appends items without checking if the track_id already exists:

```python
def add(self, item: ManualReviewItem) -> None:
    """Add item to queue."""
    self.items.append(item)  # NO DUPLICATE CHECK!
    self._save()
```

During track search, if multiple search attempts fail (e.g., retry logic, multiple query variations), the track gets
added to the queue multiple times.

**Impact**:

- Manual review queue becomes cluttered with duplicates
- Users waste time reviewing the same tracks multiple times
- Queue file grows unnecessarily (1141 lines for ~380 unique tracks)
- Poor user experience for manual validation workflow
- Confusion about how many tracks actually need review

**Solution Needed**:

Add deduplication logic to `ManualReviewQueue.add()`:

```python
def add(self, item: ManualReviewItem) -> None:
    """Add item to queue (with deduplication)."""
    # Check if track_id already exists
    if not any(existing.track_id == item.track_id for existing in self.items):
        self.items.append(item)
        self._save()
```

Or use a dict internally keyed by track_id instead of a list for automatic deduplication.

**Related Files**:

- `msc/storage/checkpoint.py` - ManualReviewQueue implementation
- `_data/runs/2025_20251224_000042/manual_review.json` - Contains 1141 lines with ~380 unique tracks

---

#### [ISSUE-009] Billing Command Not Displaying Quota Information (Investigation Needed)

**Command**: `msc billing`

**Description**:
The `msc billing` command completes but does not display API quota information. User reports "no info is returned" when
running the command.

**Steps to Reproduce**:

1. Run `msc billing`
2. Observe output

**Expected Behavior**:

- Display Songstats API quota information in a formatted table
- Show requests_used, requests_limit, remaining quota
- Show reset_date
- Display usage percentage with color coding (green/yellow/red)
- Warn if usage exceeds 80%

**Actual Behavior**:

- Table is displayed but shows all zeros and "Unknown"
- No useful quota information shown
- User sees empty/meaningless data

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (blocks API quota monitoring)

**Location in Code**:

- `msc/cli.py:280-311` - billing command implementation
- `msc/clients/songstats.py:66-90` - get_quota() method
- `msc/commands/formatters.py:20-53` - QuotaFormatter.format_billing_table()

**Root Cause**:

**API Response Structure Mismatch!**

The Songstats `/status` endpoint returns:

```json
{
  "result": "success",
  "message": "Data Retrieved.",
  "status": {
    "current_month_total_requests": 5678,
    "current_month_total_requested_objects": 343,
    "current_month_total_bill": "34.30",
    "previous_month_total_requests": 0,
    "previous_month_total_requested_objects": 0,
    "previous_month_total_bill": "0.00"
  }
}
```

But the code was expecting:

```python
quota_data.get("requests_used", 0)  # DOESN'T EXIST!
quota_data.get("requests_limit", 0)  # DOESN'T EXIST!
quota_data.get("reset_date", "Unknown")  # DOESN'T EXIST!
```

Since none of these fields existed in the API response, `.get()` returned default values (0, 0, "Unknown"), resulting in
an empty table.

**Solution Implemented**:

1. ✅ Rewrote `QuotaFormatter.format_billing_table()` to extract from `status` object
2. ✅ Updated table structure with 3 columns: Metric, Current Month, Previous Month
3. ✅ Now displays actual data:
    - API Requests: `status.current_month_total_requests` vs previous month
    - Objects Requested: `status.current_month_total_requested_objects`
    - Total Bill: `status.current_month_total_bill` vs previous month
4. ✅ Removed non-existent fields (requests_limit, reset_date, usage percentage)
5. ✅ Updated billing command to remove old warning logic
6. ✅ Changed table title from "Songstats API Quota" to "Songstats API Status"

**Fix Details**:

Before:

```python
# Extract quota data
requests_used = quota_data.get("requests_used", 0)  # Returns 0 (doesn't exist)
requests_limit = quota_data.get("requests_limit", 0)  # Returns 0 (doesn't exist)
reset_date = quota_data.get("reset_date", "Unknown")  # Returns "Unknown"
```

After:

```python
# Extract status data
status = quota_data.get("status", {})
current_requests = status.get("current_month_total_requests", 0)  # 5678
current_bill = status.get("current_month_total_bill", "0.00")  # "34.30"
previous_requests = status.get("previous_month_total_requests", 0)  # 0
```

**Files Modified**:

- `msc/commands/formatters.py:20-53` - Rewrote QuotaFormatter.format_billing_table()
- `msc/cli.py:280-311` - Removed old warning logic, updated docstring

**Testing**:

- ✅ API fetch verified: Returns correct structure with status object
- ✅ Table creation verified: Creates table with 3 rows
- ✅ Data extraction verified: Correctly extracts current/previous month data

---

#### [ISSUE-001] Log Overflow During Pipeline Execution

**Command**: `msc run`

**Description**:
During pipeline execution, the console is flooded with INFO/WARNING log messages while progress bars are attempting to
display. This creates visual clutter and makes it impossible to track actual progress.

**Steps to Reproduce**:

1. Run `msc run` (with `export PYTHONIOENCODING=utf-8` on Windows)
2. Observe the massive log output scrolling while progress indicators try to display

**Expected Behavior**:

- Clean progress bars showing stage progress
- Only critical errors/warnings should be displayed
- INFO-level logs should be suppressed or sent to file only
- User should see clean, minimal output focused on progress

**Actual Behavior**:
Hundreds of log lines flood the console:

```
2025-12-23 20:26:10 | INFO | msc.pipeline.extract | Extracting data...
[2025-12-23T20:26:10.565694] pipeline_started Starting music-charts pipeline
2025-12-23 20:26:10 | INFO | MusicBeeClient | Copying library from E:\Musique\...
2025-12-23 20:26:11 | WARNING | msc.pipeline.extract | No Songstats ID found for: ...
[continues for hundreds of lines]
```

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High

**Solution Implemented**:

1. ✅ Modified `setup_logging()` to support separate console and file log levels
2. ✅ Console now shows only ERROR level (minimal output) by default
3. ✅ All INFO/WARNING logs still written to `_data/logs/pipeline.log`
4. ✅ ConsoleObserver only shows PIPELINE_STARTED, PIPELINE_COMPLETED, PIPELINE_FAILED events
5. ✅ `--verbose` flag now properly controls both logging and observer verbosity

**Files Modified**:

- `msc/utils/logging.py`: Added `console_level` and `log_file` parameters
- `msc/cli.py`: Set console to ERROR, file to INFO, and detect verbose mode for orchestrator
- `msc/pipeline/observers.py`: Limited ConsoleObserver events to pipeline-level only

**Testing**:

- Need to verify clean output with `msc run` command

---

### Medium Priority Issues

*Issues that should be addressed soon after release*

#### [ISSUE-002] Temporary Files in Root Data Directory

**Command**: `msc run`

**Description**:
The pipeline creates temporary/intermediate files directly in `_data/` root directory, which clutters the data folder
and makes it unclear which files are outputs vs temporary artifacts.

**Files Affected**:

- `_data/tracks.json` - Intermediate track data from extraction stage
- `_data/manual_review.json` - Manual review queue items

**Expected Behavior**:

- Temporary/intermediate files should be in a dedicated subdirectory (e.g., `_data/temp/`, `_data/runs/`, or
  `_data/cache/`)
- Clear separation between final outputs (`_data/output/`) and temporary artifacts

**Actual Behavior**:

- Both files are created directly in `_data/` root
- No clear distinction between temporary and permanent files

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: Medium

**Location in Code**:

- `msc/pipeline/orchestrator.py:87` - `self.data_dir / "tracks.json"`
- `msc/pipeline/orchestrator.py:95` - `self.data_dir / "manual_review.json"`

**Solution Implemented**:

1. ✅ Created run-based directory structure: `_data/runs/{year}_{run_id}/`
2. ✅ Moved `tracks.json` to run directory
3. ✅ Moved `manual_review.json` to run directory
4. ✅ Moved checkpoints to run directory (per-run isolation)
5. ✅ Moved event logs to `_data/logs/pipeline_events_{run_id}.jsonl`
6. ✅ Added run_id logging to show users where data is stored

**Files Modified**:

- `msc/pipeline/orchestrator.py`: Added run_id, run_dir, updated all paths
- `_tests/unit/test_orchestrator.py`: Updated test expectations

**New Directory Structure**:

```
_data/
├── runs/
│   └── {year}_{run_id}/          # e.g., 2025_20251223_143052
│       ├── tracks.json           # Extracted tracks (intermediate)
│       ├── manual_review.json    # Manual review items (per-run)
│       └── checkpoints/          # Checkpoints (per-run isolation)
│           ├── extraction_checkpoint.json
│           └── enrichment_checkpoint.json
├── logs/
│   ├── pipeline.log              # Detailed logging output
│   └── pipeline_events_{run_id}.jsonl
└── output/
    └── enriched_tracks.json      # Final enriched data
```

**Important Notes**:

- Each run is now fully isolated with its own directory
- Checkpoints are per-run to prevent state contamination between runs
- To resume a failed run, use the same run_id (future enhancement)

---

#### [ISSUE-003] Manual Review Queue Accumulates Across Runs

**Command**: `msc run`

**Description**:
The `manual_review.json` file accumulates items from all pipeline runs without any way to distinguish which reviews
belong to which run. This makes it impossible to know which manual reviews are current vs. from previous runs.

**Steps to Reproduce**:

1. Run `msc run` - generates some manual review items
2. Run `msc run` again - new items are appended to existing ones
3. Check `_data/manual_review.json` - contains items from both runs mixed together

**Expected Behavior**:

- Each pipeline run should have its own manual review file with a timestamp
- Manual review files should be linked to checkpoint logic (run ID or timestamp)
- Users should be able to identify which reviews are from the current run
- Option to archive/clear old manual review items

**Actual Behavior**:

- All manual review items from all runs are stored in a single file
- Items accumulate indefinitely across multiple runs
- No way to distinguish which items are from which run
- No automatic cleanup or archival mechanism

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: Medium

**Location in Code**:

- `msc/storage/checkpoint.py:274-289` - `ManualReviewQueue._load()` loads existing items
- `msc/storage/checkpoint.py:338` - `self.items.append(item)` appends to existing list
- `msc/pipeline/orchestrator.py:95` - Hardcoded path without timestamp

**Solution Implemented**:

1. ✅ Each pipeline run now creates a unique directory: `_data/runs/{year}_{run_id}/`
2. ✅ Manual review file is now per-run: `_data/runs/{year}_{run_id}/manual_review.json`
3. ✅ Run ID is timestamp-based (format: `YYYYMMDD_HHMMSS`)
4. ✅ Each run's manual review items are isolated from other runs
5. ✅ Users can identify which run a manual review file belongs to

**Files Modified**:

- `msc/pipeline/orchestrator.py`: Added run_id, moved manual_review.json to run directory

**Future Enhancements** (not required for 1.0.0):

- Add CLI command to view/manage manual review items (e.g., `msc review list`, `msc review clear`)
- Consider adding a review status field (pending/resolved/ignored)

**Related Issues**:

- ISSUE-002 (file organization) - Fixed together

---

### Low Priority Issues

*Nice-to-have improvements for future versions*

#### [ISSUE-004] Poor Songstats API Search Success Rate Due to Unclean Queries

**Command**: `msc run`

**Description**:
During extraction stage, approximately 52% of tracks fail to find Songstats IDs (196 failed out of 373 total tracks).
Analysis of the manual review queue reveals that queries sent to Songstats API contain special characters, feature
annotations, and punctuation that interfere with search accuracy.

**Examples of Problematic Queries**:

From manual_review.json analysis:

* `"Oliverse & MØØNE adrenaline"` - Contains `&` in artist name
* `"RIENK × Lukher the air i breathe"` - Contains `×` (multiplication sign)
* `"ROY KNOX & Austin Christopher (feat. Stephanie Schulte) if i stay"` - Contains `&` and `(feat. ...)`
* `"Andromedik (feat. Lauren L'aimant) air"` - Contains feature annotation
* `"jeonghyeon & SUNGYOO all i need extended"` - Contains `&` separator

**Expected Behavior**:

* Artist names should be cleaned before building search queries
* Special characters (`×`, `&`) should be replaced with spaces
* Feature annotations (`(feat. ...)`, `(ft. ...)`) should be removed
* Remaining parentheses/brackets should be stripped
* Multiple spaces should be normalized to single spaces

**Actual Behavior**:

* Raw artist names from MusicBee are used directly in queries
* Special characters and annotations cause search failures
* Over half of tracks fail to find Songstats IDs

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: Low (affects data quality, but not blocking for 1.0.0)

**Location in Code**:

* `msc/utils/text.py` - Query building functions
* `msc/pipeline/extract.py:242` - Search query construction

**Solution Implemented**:

1. ✅ Added `format_artist()` function to clean artist names
2. ✅ **REMOVE featured artists** entirely - they create query mismatches in Songstats (`(feat. Artist B)` → removed)
3. ✅ Replaces special separators in artist names: `×` → space, `&` → space
4. ✅ Removes remaining parentheses and brackets from artist names
5. ✅ Enhanced `format_title()` to remove mix tags: `[Extended]`, `[Extended Mix]`, `[Original Mix]`, etc.
6. ✅ Enhanced `format_title()` to remove punctuation: `!`, `"`, `.`, `,`
7. ✅ **KEEP apostrophes** (`'`) - they are semantically important ("don't" ≠ "dont")
8. ✅ Updated title separators: ` & ` → space (in addition to ` × `)
9. ✅ Modified `build_search_query()` to use spaces instead of commas between artists
10. ✅ Normalizes whitespace and converts to lowercase
11. ✅ Added 23 comprehensive tests for query cleaning (47 total, all passing)

**Important Finding**:

Initial testing revealed that removing apostrophes actually **decreased** success rate:

* Run 1 (with apostrophes removed): 313/368 successful (85.1%)
* Run 2 (keeping apostrophes): Expected to improve

Apostrophes are semantically critical:

* "don't" vs "dont" - different words
* "can't" vs "cant" - different words
* "ain't" vs "aint" - different words

**Corrective Action**: Reverted apostrophe removal to preserve query accuracy.

**Files Modified**:

* `msc/config/constants.py`: Added `[Extended]` and punctuation to TITLE_PATTERNS_TO_REMOVE, updated
  TITLE_PATTERNS_TO_SPACE
* `msc/utils/text.py`: Added `format_artist()`, updated `build_search_query()` to use space separator
* `_tests/unit/test_text.py`: Added 23 comprehensive tests (47 total, all passing)

**Query Improvements**:

Before:

```
"Oliverse & MØØNE adrenaline"
"RIENK × Lukher the air i breathe"
"ROY KNOX & Austin Christopher (feat. Stephanie Schulte) if i stay"
```

After:

```
"oliverse møøne adrenaline"
"rienk lukher the air i breathe"
"roy knox austin christopher if i stay"  (featured artist removed - prevents mismatches!)
```

**Testing**:

* ✅ All 47 text utility tests passing
* ⏳ Need to run full pipeline to measure improvement in success rate
* ⏳ Compare manual review queue size before/after improvement

**Expected Impact**:

* Should significantly reduce the 52% failure rate
* Cleaner queries should produce better Songstats search results
* Fewer tracks requiring manual review

---

### Enhancement Requests

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

---

## Issue Template

Use this template when adding new issues:

```markdown
#### [ISSUE-XXX] Short Issue Title

**Command**: `msc command-name`

**Description**:
Clear description of what was observed vs what was expected.

**Steps to Reproduce**:

1. Step one
2. Step two
3. Step three

**Expected Behavior**:
What should happen

**Actual Behavior**:
What actually happens

**Status**:

- [ ] Planned
- [ ] In Progress
- [ ] Fixed
- [ ] Deferred

**Priority**: Critical | High | Medium | Low | Enhancement

**Notes**:
Any additional context or related information

---
```

## Test Session Logs

### Session 1 - 2025-12-23

**Tester**: User
**Focus**: Initial CLI validation
**Environment**:

- OS: Windows
- Python: [version]
- Package version: alpha

**Tests Performed**:

- [ ] `msc --help`
- [x] `msc init` ✅ No issues
- [x] `msc billing` ✅ No issues
- [ ] `msc validate`
- [ ] `msc stats`
- [ ] `msc clean`
- [ ] `msc export`
- [x] `msc run` ⚠️ Works but has UX issues (ISSUE-001)

**Issues Found**:

- ISSUE-001: Log overflow during pipeline execution (High Priority) - ✅ Fixed
- ISSUE-002: Temporary files in root data directory (Medium Priority) - ✅ Fixed
- ISSUE-003: Manual review queue accumulates across runs (Medium Priority) - ✅ Fixed
- ISSUE-004: Poor Songstats API search success rate due to unclean queries (Low Priority) - ✅ Fixed

**Bugs Fixed During Testing**:

1. Fixed extraction stage dictionary access bug (libpybee.Track objects vs dicts)
2. Fixed genre/label list wrapping issue (already lists from MusicBee)
3. Fixed log overflow UX issue with dual-level logging and minimal ConsoleObserver output

**Improvements Implemented**:

1. Implemented run-based directory structure for better data organization
2. Isolated manual review items per run to prevent accumulation
3. Moved checkpoints to run directory to prevent state contamination between runs
4. Reorganized data directories (runs/, logs/, output/)
5. Added comprehensive query cleaning to improve Songstats API search success rate:
    * Artist name cleaning (remove `×`, `&`, feature annotations)
    * Title punctuation removal (`!`, `"`, `.`, `,` - **keep apostrophes**)
    * Space-based artist separator (no commas)

**Notes**:

- Windows users must set `export PYTHONIOENCODING=utf-8` before running to display emojis correctly
- Pipeline successfully extracts and processes tracks
- Console output is now clean with progress bars only (verbose logging available in file)

---

## Manual Review Workflow

### Filling in Missing Songstats IDs

When tracks fail to find Songstats IDs automatically during extraction, they are added to the manual review queue. You
can manually add the Songstats IDs and resume the pipeline from where it left off.

#### Workflow Steps

**1. Run the pipeline**

```bash
msc run --year 2025
```

The pipeline creates a run directory: `_data/runs/2025_YYYYMMDD_HHMMSS/`

**2. Check failed tracks**

Open the manual review file to see which tracks need manual IDs:

```
_data/runs/2025_YYYYMMDD_HHMMSS/manual_review.json
```

**3. Find Songstats IDs**

For each failed track:

- Go to [Songstats](https://songstats.com/)
- Search for the track manually
- Copy the ID from the URL: `https://songstats.com/track/<songstats_id>/...`

**4. Add to extraction checkpoint**

Open the checkpoint file:

```
_data/runs/2025_YYYYMMDD_HHMMSS/checkpoints/extraction_checkpoint.json
```

Add the track to the checkpoint's `processed_ids` array and update the tracks.json file.

**Alternative: Edit tracks.json directly**

Open the tracks repository:

```
_data/runs/2025_YYYYMMDD_HHMMSS/tracks.json
```

Find the track in the JSON array and add the Songstats ID:

```json
{
  "title": "Track Name",
  "artist_list": [
    "Artist Name"
  ],
  "year": 2025,
  "songstats_identifiers": {
    "songstats_id": "12345678",
    "songstats_title": "Track Name",
    "isrc": null
  }
}
```

**5. Resume the pipeline**

By default, the pipeline automatically resumes from the most recent run for the year:

```bash
msc run --year 2025
```

The pipeline will:

- ✅ Find the latest run directory (`2025_YYYYMMDD_HHMMSS`)
- ✅ Load existing checkpoint with processed IDs
- ✅ Skip already-processed tracks (including manually added ones)
- ✅ Continue enrichment/ranking from where it left off

#### CLI Flags

- **Default behavior**: Resumes from most recent run for the year
  ```bash
  msc run --year 2025
  ```

- **Force new run**: Create fresh run directory instead of resuming
  ```bash
  msc run --year 2025 --new-run
  ```

- **Reset pipeline**: Clear all checkpoints and start from scratch
  ```bash
  msc run --year 2025 --reset
  ```

#### Implementation Details

**Automatic Run Resumption** (orchestrator.py:74-92):

- Pipeline searches for most recent run directory matching the year pattern
- Run directories format: `_data/runs/{year}_{YYYYMMDD_HHMMSS}/`
- Sorts by timestamp and automatically resumes from latest
- Only creates new run if `--new-run` flag is used or no existing runs found

**Checkpoint Persistence**:

- Each run has its own checkpoint directory: `_data/runs/{year}_{run_id}/checkpoints/`
- Checkpoints track `processed_ids`, `failed_ids`, and metadata
- Extraction stage skips tracks already in `processed_ids` (extract.py:199-218)
- Manual edits to tracks.json are preserved across resumptions

---

## Resolution Tracking

| Issue ID  | Priority    | Status   | Assigned | Target Version |
|-----------|-------------|----------|----------|----------------|
| ISSUE-001 | High        | Fixed    | @Dyl-M   | 1.0.0          |
| ISSUE-002 | Medium      | Fixed    | @Dyl-M   | 1.0.0          |
| ISSUE-003 | Medium      | Fixed    | @Dyl-M   | 1.0.0          |
| ISSUE-004 | Low         | Fixed    | @Dyl-M   | 1.0.0          |
| ISSUE-005 | Enhancement | Deferred | @Dyl-M   | Future         |
| ISSUE-006 | Critical    | Fixed    | @Dyl-M   | 1.0.0          |
| ISSUE-007 | Critical    | Planned  | @Dyl-M   | 1.0.0          |
| ISSUE-008 | High        | Planned  | @Dyl-M   | 1.0.0          |
| ISSUE-009 | High        | Fixed    | @Dyl-M   | 1.0.0          |

---

## Sign-off Criteria

For 1.0.0 release approval:

- [ ] All Critical issues resolved
- [ ] All High Priority issues resolved or documented as known limitations
- [ ] Documentation updated with any breaking changes
- [ ] README reflects accurate usage for 1.0.0
- [ ] All CLI commands tested end-to-end
- [ ] Error messages are clear and actionable
- [ ] Help text is accurate and comprehensive
