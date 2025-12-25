**# User Validation for Version 1.0.0

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
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: Critical (causes track enrichment to fail unnecessarily)

**Location in Code**:

- `msc/pipeline/enrich.py:209-211` - YouTube data validation check
- `msc/pipeline/enrich.py:207-223` - YouTube data processing block

**Root Cause**:

The code checked `if youtube_results:` but an empty dict like `{"most_viewed": {}, "all_sources": []}` is truthy in
Python, so it passed the check and tried to create YouTubeVideo from the empty dict, causing Pydantic validation errors.

Before:

```python
if youtube_results:
    # Convert API response to YouTubeVideoData model
    most_viewed_video = YouTubeVideo(**youtube_results["most_viewed"])  # FAILS if empty!
```

**Impact**:

- Tracks with empty YouTube data fail enrichment entirely
- Loses platform stats data that was successfully fetched
- Increases failed track count unnecessarily
- Reduces overall enrichment success rate

**Solution Implemented**:

1. ✅ Added comprehensive validation to check ALL required YouTubeVideo fields
2. ✅ Check that `ytb_id`, `views`, and `channel_name` all exist and are not None
3. ✅ Special handling for `views` field which can be None (causing int validation error)
4. ✅ Only create YouTubeVideo model if all required fields are valid
5. ✅ Skip YouTube enrichment gracefully if any field is missing/invalid
6. ✅ Continue processing track with platform stats even if YouTube data is incomplete
7. ✅ Log debug message when YouTube data is not found

After:

```python
# Check if YouTube data is valid (all required fields present and not None)
most_viewed = youtube_results.get("most_viewed") if youtube_results else None
if (most_viewed
        and most_viewed.get("ytb_id")
        and most_viewed.get("views") is not None  # Explicit None check for int field!
        and most_viewed.get("channel_name")):
    # Convert API response to YouTubeVideoData model
    most_viewed_video = YouTubeVideo(**youtube_results["most_viewed"])
    # ... rest of processing
else:
    self.logger.debug("No YouTube data found for: %s", track.title)
```

**Files Modified**:

- `msc/pipeline/enrich.py:209-214` - Added comprehensive YouTube data validation

**Two Types of Failures Fixed**:

1. **Empty dict**: `{"most_viewed": {}, "all_sources": []}` - Missing all fields
2. **Partial data with None values**: `{"most_viewed": {"ytb_id": "abc", "views": None, "channel_name": "X"}}` - Field
   exists but value is None

**Testing**:

- ✅ All 22 enrichment stage tests passing
- ✅ Both empty dict and None value cases handled

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
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (significantly impacts manual review workflow usability)

**Location in Code**:

- `msc/storage/checkpoint.py:329-332` - Deduplication check in `ManualReviewQueue.add()`
- `msc/pipeline/extract.py` - Adds failed tracks to queue during search process

**Root Cause**:

The `ManualReviewQueue.add()` method was simply appending items without checking if the track_id already exists.

Before:

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

**Solution Implemented**:

1. ✅ Added deduplication check in `ManualReviewQueue.add()` method
2. ✅ Check if track_id already exists before appending
3. ✅ Log debug message when duplicate is skipped
4. ✅ Return early if duplicate found (no save operation needed)

After:

```python
def add(self, track_id: str, title: str, artist: str, reason: str, ...) -> None:
    """Add an item to the review queue with deduplication."""
    # Check if track_id already exists in queue (deduplication)
    if any(existing.track_id == track_id for existing in self.items):
        self.logger.debug("Track already in review queue, skipping: %s", track_id)
        return

    # Create and append item
    item = ManualReviewItem(...)
    self.items.append(item)
    self._save()
```

**Files Modified**:

- `msc/storage/checkpoint.py:329-332` - Added deduplication check

**Testing**:

- ✅ All 9 existing ManualReviewQueue tests passing
- ✅ Deduplication logic verified in code review

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

#### [ISSUE-010] Empty Fields in Extracted Track Data

**Command**: `msc run`

**Description**:
Multiple fields in the extracted tracks data (`tracks.json`) are consistently empty/null across all tracks, indicating
that data is not being properly extracted from MusicBee or fetched from Songstats API. This affects data completeness
and potential analysis capabilities.

**Affected Fields**:

1. **`label`** (list): Always `[]` - Should contain record label(s) from MusicBee
2. **`grouping`** (string): Always `null` - MusicBee custom grouping field
3. **`search_query`** (string): Always `null` - Should store the query used for Songstats search (debugging/tracking)
4. **`isrc`** (string): Always `null` - Should contain ISRC code from Songstats API response

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Open `_data/runs/2025_YYYYMMDD_HHMMSS/tracks.json`
3. Examine any track entry
4. Observe that `label`, `grouping`, `search_query`, and `isrc` fields are empty/null

**Expected Behavior**:

- **`label`**: Should extract record label information from MusicBee library XML (`<key>Publisher</key>` tag)
- **`grouping`**: Should extract MusicBee grouping field if present (`<key>Grouping</key>` tag)
- **`search_query`**: Should store the actual search query used to find the track in Songstats (for
  debugging/transparency)
- **`isrc`**: Should extract ISRC code from Songstats API search results (available in track metadata)

**Actual Behavior**:

```json
{
  "title": "When A Fire Starts To Burn [Chime Flip]",
  "artist_list": [
    "Disclosure"
  ],
  "year": 2025,
  "genre": [
    "Dubstep / Brostep / Riddim"
  ],
  "label": [],
  // ❌ Always empty
  "grouping": null,
  // ❌ Always null
  "search_query": null,
  // ❌ Always null
  "songstats_identifiers": {
    "songstats_id": "em0th986",
    "songstats_title": "When A Fire Starts To Burn (Chime Flip)",
    "isrc": null
    // ❌ Always null
  }
}
```

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data completeness and analytical capabilities)

**Current Status (2025-12-24)**:

✅ **Completed**:

1. `search_query` field - Now populated with Songstats search query
2. `grouping` field - Now uses native `list` from libpybee (no wrapping bug)
3. `artist_list` field - Now uses native `list` from libpybee (see ISSUE-014)

⚠️ **Partially Complete**:

3. `label` field - Populated but redundant with `grouping` (both use MusicBee data)

❌ **Not Working**:

4. `isrc` field - Still returning `null` despite code to extract from Songstats API

**Sub-Issues Created**:

- See ISSUE-011: Label/Grouping Redundancy and Missing Songstats Metadata
- See ISSUE-012: Track Identifier Should Use UUID Instead of String Concatenation

**Location in Code**:

- `msc/clients/musicbee.py:150-180` - Track extraction from XML (missing label/grouping extraction)
- `msc/pipeline/extract.py:242-260` - Search query construction (not stored in track)
- `msc/pipeline/extract.py:270-290` - Songstats search result processing (ISRC not extracted)

**Root Cause Analysis**:

1. **`label` field**: MusicBeeClient likely not reading the `<key>Publisher</key>` or `<key>Label</key>` tag from
   library XML
2. **`grouping` field**: MusicBeeClient not reading the `<key>Grouping</key>` tag from library XML
3. **`search_query` field**: ExtractionStage builds search query but doesn't store it in the Track model before saving
4. **`isrc` field**: Songstats API returns ISRC in search results, but ExtractionStage doesn't extract and store it in
   SongstatsIdentifiers

**Impact**:

- Missing record label information reduces analytical capabilities (e.g., label-based rankings, independent vs major
  label analysis)
- Missing grouping field loses user-defined categorization from MusicBee
- Missing search_query makes it difficult to debug failed searches or understand matching logic
- Missing ISRC prevents cross-referencing with other music databases and official music identification systems

**Terminology Clarification**:

**Important**: There's a naming confusion between two different concepts:

1. **`label`** (plural in code): Track model field representing **record label(s)** (e.g., "Monstercat", "OWSLA", "
   mau5trap")
    - Source: MusicBee library XML (`<key>Publisher</key>` tag)
    - Purpose: Identifies which record label released the track
    - Example: `["Monstercat", "Universal Music"]`

2. **`grouping`**: MusicBee custom field for user-defined **grouping/categorization**
    - Source: MusicBee library XML (`<key>Grouping</key>` tag)
    - Purpose: User-defined categorization (e.g., "Favorites", "Workout", "Chill")
    - Example: `"Best of 2025"` or `"Festival Anthems"`

Both fields describe different concepts despite confusing naming:

- `label` = Music business entity (record label company)
- `grouping` = User-defined category (personal organization)

**Proposed Solution**:

**✅ LIBPYBEE NATIVE SUPPORT DISCOVERED** (2025-12-24)

Investigation of libpybee documentation (https://dyl-m.github.io/libpybee/references/track/) reveals that the Track
class provides native support for both fields:

- **`artist_list` (list)** - Native artist list ✅ (eliminates need for manual parsing)
- **`grouping` (list)** - Native list support ✅ (not a string!)

**Implementation Update Based on Native Support**:

1. ✅ **artist_list field**:
    - Use `track.artist_list` directly from libpybee (see ISSUE-014 for details)
    - No need for manual splitting on commas/ampersands

2. ✅ **grouping field**:
    - Use `track.grouping` directly from libpybee (already returns list)
    - Current code incorrectly wraps it in another list: `[grouping] if grouping...`
    - **FIX NEEDED**: Remove list wrapping, use native list directly

3. ✅ **label field**:
    - Update `MusicBeeClient._parse_track()` to extract `<key>Publisher</key>` or `<key>Label</key>` tag
    - Store as list in Track.label field
    - Handle multiple labels if separated by semicolons/commas

3. ✅ **search_query field**:
    - Store the built search query in Track.search_query before saving to repository
    - Update in ExtractionStage after successful/failed search

4. ✅ **isrc field**:
    - Extract ISRC from Songstats API search results
    - Check if `result.get("isrc")` exists in search response
    - Store in SongstatsIdentifiers.isrc field

**Files to Modify**:

- `msc/clients/musicbee.py` - Add label/grouping extraction
- `msc/pipeline/extract.py` - Store search_query and extract ISRC from API results

**Testing Requirements**:

- Verify label extraction from MusicBee XML with Publisher tag
- Verify grouping extraction from MusicBee XML with Grouping tag
- Verify search_query is stored for both successful and failed searches
- Verify ISRC extraction from Songstats API response when available
- Update unit tests to verify all fields are populated

**Related Files**:

- Run directory: `_data/runs/2025_20251224_113317/tracks.json`
- MusicBee library: Path from `MSC_MUSICBEE_LIBRARY` env var

---

#### [ISSUE-011] Label/Grouping Redundancy and Missing Songstats Metadata

**Command**: `msc run`

**Description**:
After implementing ISSUE-010 fixes, three new data quality issues were discovered in `tracks.json`:

1. **`label` and `grouping` are redundant** - Both fields contain the same MusicBee grouping data, making one field
   unnecessary
2. **ISRC still not populated** - Despite code to extract ISRC from Songstats API, field remains `null`
3. **Missing Songstats artist metadata** - No field to store the artist list returned by Songstats API for comparison
   with MusicBee data

**Steps to Reproduce**:

1. Run `msc run --year 2025` (after ISSUE-010 fixes)
2. Open `_data/runs/2025_YYYYMMDD_HHMMSS/tracks.json`
3. Examine track entries
4. Observe redundant label/grouping and missing ISRC/songstats_artists

**Expected Behavior**:

**Field Separation**:

- `label`: Should contain record labels from **Songstats API** (authoritative source)
- `grouping`: Should contain user-defined grouping from **MusicBee** only
- `songstats_identifiers.isrc`: Should contain ISRC code from Songstats API
- `songstats_identifiers.songstats_artists`: Should contain artist list from Songstats API

**Purpose**:

- Compare MusicBee artist names vs Songstats canonical artist names
- Compare MusicBee labels (user-entered) vs Songstats labels (authoritative)
- Enable data quality validation and discrepancy detection
- Use ISRC for cross-referencing with external music databases

**Actual Behavior**:

```json
{
  "title": "When A Fire Starts To Burn [Chime Flip]",
  "artist_list": [
    "Disclosure"
  ],
  // From MusicBee
  "year": 2025,
  "genre": [
    "Dubstep / Brostep / Riddim"
  ],
  "label": [
    "[NO LABELS]"
  ],
  // ❌ From MusicBee (redundant with grouping)
  "grouping": [
    "[NO LABELS]"
  ],
  // ✅ From MusicBee (correct)
  "search_query": "disclosure when a fire starts to burn chime flip",
  "songstats_identifiers": {
    "songstats_id": "em0th986",
    "songstats_title": "When A Fire Starts To Burn (Chime Flip)",
    "isrc": null
    // ❌ Should have ISRC from API
    // ❌ Missing: "songstats_artists": ["Disclosure"]
    // ❌ Missing: "songstats_labels": ["..."]
  }
}
```

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data quality and comparison capabilities)

**Solution Implemented (2025-12-24)**:

✅ **1. Added Songstats Metadata Fields**:

- **`SongstatsIdentifiers.songstats_artists`** - Artist list from Songstats API for comparison with MusicBee data
- **`SongstatsIdentifiers.songstats_labels`** - Record labels from Songstats API (authoritative source)

✅ **2. Fixed ISRC Extraction**:

- ISRC is located in `track_info.links[]` array (available from multiple streaming platforms)
- Extract from first platform that provides it (ISRC is universal across platforms)
- Uses `get_track_info()` endpoint instead of search endpoint
- Added debug logging to show which platform provided the ISRC

✅ **3. Removed Redundant Label Field**:

- Removed `Track.label` field (redundant with `songstats_labels`)
- Kept `Track.grouping` field (user's local label organization from MusicBee)
- Authoritative labels now in `songstats_identifiers.songstats_labels`

**Files Modified**:

- `msc/models/track.py:65-67,217-223` - Removed `label` field, added `songstats_artists` and `songstats_labels` to
  SongstatsIdentifiers
- `msc/pipeline/extract.py:131-147,269-315` - Removed label assignment, extract artist/label lists from API, fixed ISRC
  extraction from `track_info.links[]`

**Implementation Notes**:

- Both artist/label fields handle API responses that may return lists of dicts (e.g., `[{"name": "Artist"}]`)
- Extract only the `"name"` field from each dict, or convert to string if not a dict
- Fields default to empty lists for backward compatibility
- ISRC extraction loops through all platform links and takes first available ISRC
- Adds 1 additional API call per track (329 tracks × 2 = 658 API calls vs 329)

**Proposed Solution**:

**1. Restructure `label` field**:

- ✅ Keep `Track.label` as list of record labels
- ✅ Populate from MusicBee grouping field (current behavior)
- ✅ Add `SongstatsIdentifiers.songstats_labels` field for Songstats API labels
- ✅ Enable comparison: MusicBee labels vs Songstats authoritative labels

**2. Fix ISRC extraction**:

- ✅ Investigate why `result.get("isrc")` returns `None`
- ✅ Check Songstats API response structure for ISRC location
- ✅ May need to use different API endpoint or field path
- ✅ Add logging to debug ISRC extraction

**3. Add Songstats artist metadata**:

- ✅ Add `SongstatsIdentifiers.songstats_artists` field (list[str])
- ✅ Extract from Songstats API search results
- ✅ Store artist list returned by Songstats for the track
- ✅ Enable comparison: MusicBee artists vs Songstats canonical artists

**Implementation Details**:

**SongstatsIdentifiers model update** (msc/models/track.py):

```python
class SongstatsIdentifiers(MSCBaseModel):
    songstats_id: str
    songstats_title: str
    isrc: str | None = None
    songstats_artists: list[str] = Field(default_factory=list)  # NEW
    songstats_labels: list[str] = Field(default_factory=list)  # NEW
```

**Extraction stage update** (msc/pipeline/extract.py):

```python
# Extract from Songstats search result
result = search_results[0]
updated_identifiers = track.songstats_identifiers.model_copy(
    update={
        "songstats_id": result.get("songstats_track_id", ""),
        "songstats_title": result.get("title", ""),
        "isrc": result.get("isrc"),  # Investigate correct field path
        "songstats_artists": result.get("artists", []),  # NEW
        "songstats_labels": result.get("labels", []),  # NEW
    }
)
```

**Files to Modify**:

- `msc/models/track.py:178-200` - Add songstats_artists and songstats_labels to SongstatsIdentifiers
- `msc/pipeline/extract.py:265-271` - Extract additional fields from API response

**Testing Requirements**:

- Verify ISRC is populated when available in API response
- Verify songstats_artists list matches API response
- Verify songstats_labels list matches API response
- Test backward compatibility with old JSON files (default to empty lists)

**Related Files**:

- `_data/runs/2025_20251224_113317/tracks.json` - Current data showing redundancy

---

#### [ISSUE-012] Track Identifier Should Use UUID Instead of String Concatenation

**Command**: `msc run`, `msc export`

**Description**:
The current track identifier (`track_id` in exports, `Track.identifier` property) uses string concatenation of artist,
title, and year (e.g., `"disclosure_when_a_fire_starts_to_burn_[chime_flip]_2025"`). This creates long, unwieldy
identifiers that are not ideal for database keys, API endpoints, or URL parameters.

**Current Implementation**:

```python
@property
def identifier(self) -> str:
    """Format: artist_title_year"""
    normalized_artist = self.primary_artist.lower().replace(" ", "_")
    normalized_title = self.title.lower().replace(" ", "_")
    return f"{normalized_artist}_{normalized_title}_{self.year}"
```

**Example Output**:

```
"disclosure_when_a_fire_starts_to_burn_[chime_flip]_2025"  # 52 characters!
```

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Check `_data/output/power_rankings_2025_flat.json`
3. Observe `track_id` field with long concatenated strings

**Expected Behavior**:

- Track identifier should be a compact UUID (e.g., `"a1b2c3d4"` or full UUID)
- Identifier should be stable across runs for the same track
- Identifier should be deterministic (same track → same UUID)
- Identifier should be suitable for use as database key, URL parameter, or API endpoint
- Human-readable track info should be in separate fields (title, artist, year)

**Actual Behavior**:

- Track identifier is a long concatenated string
- Can be 40-60+ characters long
- Contains special characters (`[`, `]`, `_`, etc.)
- Not suitable for URLs or compact identifiers
- Makes JSON files harder to read and debug

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data structure and export formats)

**Solution Implemented (2025-12-25)**:

✅ **Implemented Option 1: UUID5-based Deterministic Identifier**

The `Track.identifier` property now uses UUID5 hashing to generate compact, deterministic 8-character identifiers:

**Key Features**:

- ✅ **Compact**: 8 characters (e.g., `c4e7f8a3`) vs 40-60+ characters
- ✅ **Deterministic**: Same track always produces same ID across runs
- ✅ **Stable**: UUID5 namespace-based hashing ensures reproducibility
- ✅ **URL-safe**: No special characters, suitable for database keys and API endpoints
- ✅ **Backward compatible**: `legacy_identifier` property provides old format for reference

**Implementation Details**:

```python
@property
def identifier(self) -> str:
    """Unique identifier for this track (UUID5-based)."""
    # Create stable content string from core track identifiers
    # Using pipe separator to avoid collisions (e.g., "AB|C" vs "A|BC")
    content = f"{self.primary_artist.lower()}|{self.title.lower()}|{self.year}"

    # Generate UUID5 using DNS namespace (deterministic, reproducible)
    track_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, content)

    # Return first 8 characters for compact identifier
    return str(track_uuid)[:8]
```

**Backward Compatibility**:

Added `legacy_identifier` property that preserves the old string concatenation format for reference:

```python
@property
def legacy_identifier(self) -> str:
    """Legacy identifier format (pre-UUID5 implementation)."""
    normalized_artist = self.primary_artist.lower().replace(" ", "_")
    normalized_title = self.title.lower().replace(" ", "_")
    return f"{normalized_artist}_{normalized_title}_{self.year}"
```

**UX Improvement - Progress Bar Display**:

Updated pipeline progress bars to display track **title** instead of UUID identifier for better user experience:

**Before**:

```
Extraction → c4e7f8a3
Enrichment → c4e7f8a3
```

**After**:

```
Extraction → Scary Monsters and Nice Sprites
Enrichment → Scary Monsters and Nice Sprites
```

Logs still use the UUID identifier for tracking:

```json
{
  "event_type": "item_processing",
  "item_id": "c4e7f8a3",
  "message": "Searching Songstats: Scary Monsters and Nice Sprites - skrillex",
  "metadata": {
    "current_item": "Scary Monsters and Nice Sprites"
  }
}
```

**Files Modified**:

- `msc/models/track.py:119-170` - Updated `identifier` property to UUID5, added `legacy_identifier` property
- `msc/pipeline/extract.py:251` - Added `current_item` metadata for progress bar
- `msc/pipeline/enrich.py:161` - Added `current_item` metadata for progress bar
- `_tests/unit/test_track_model.py` - Added 9 comprehensive tests for UUID identifier

**Testing Results**:

✅ **All 53 track model tests passing**

New tests added:

- `test_identifier_is_uuid_based` - Validates 8-char hexadecimal format
- `test_identifier_is_deterministic` - Same track = same ID
- `test_identifier_is_stable_across_runs` - Stability across instantiations
- `test_identifier_differs_for_different_tracks` - Different tracks = different IDs
- `test_identifier_case_insensitive` - Case-insensitive hashing
- `test_legacy_identifier_format` - Old format validation
- `test_legacy_identifier_vs_new_identifier` - Format comparison
- `test_identifier_with_special_characters` - Special character handling

**Migration Notes**:

No migration script needed since:

- Repository and checkpoint usage is not affected (uses same `identifier` property)
- Export formats automatically use new UUID format
- `legacy_identifier` available for any backward compatibility needs
- Old data files can coexist with new format

**Proposed Solutions**:

**Option 1: Deterministic UUID from Content Hash** ✅ Recommended

Use a hash of artist+title+year to generate a stable, deterministic UUID:

```python
import uuid
import hashlib


@property
def identifier(self) -> str:
    """Generate deterministic UUID from track content."""
    # Create stable hash from core track identifiers
    content = f"{self.primary_artist.lower()}|{self.title.lower()}|{self.year}"
    content_hash = hashlib.sha256(content.encode()).digest()

    # Generate UUID5 (namespace-based, deterministic)
    track_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, content)
    return str(track_uuid)[:8]  # Short form: "a1b2c3d4"
```

**Benefits**:

- ✅ Stable: Same track always gets same UUID
- ✅ Compact: 8-character identifier (vs 40-60 chars)
- ✅ Deterministic: Reproducible across runs
- ✅ Suitable for URLs, database keys, APIs

**Option 2: Songstats ID as Primary Identifier**

Use the Songstats ID directly (already available after extraction):

```python
@property
def identifier(self) -> str:
    """Use Songstats ID if available, fallback to UUID."""
    if self.songstats_identifiers.songstats_id:
        return self.songstats_identifiers.songstats_id  # e.g., "em0th986"
    # Fallback for tracks without Songstats ID
    return self._generate_uuid()
```

**Benefits**:

- ✅ Uses authoritative external ID
- ✅ Already 8 characters (compact)
- ✅ Enables direct Songstats API lookups
- ❌ Not available before extraction stage
- ❌ Tracks without Songstats ID need fallback

**Impact**:

**Breaking Changes**:

- All exports will have different track_id format
- Checkpoints use identifier as key - will need migration
- Manual review queue uses identifier - will need update

**Migration Path**:

1. Add new UUID field alongside existing identifier initially
2. Update export formats to use UUID as primary key
3. Keep old identifier as `track_identifier_legacy` for reference
4. Provide migration script for old checkpoints

**Files to Modify**:

- `msc/models/track.py:120-142` - Update `identifier` property
- `msc/storage/json_repository.py` - Update repository key usage
- `msc/storage/checkpoint.py` - Update checkpoint tracking
- `_tests/unit/test_track_model.py` - Update identifier tests

**Testing Requirements**:

- Verify UUID generation is deterministic (same track → same UUID)
- Verify UUID is stable across pipeline runs
- Verify backward compatibility with old data files
- Test export formats with new identifier format
- Verify checkpoint resumability with new identifiers

**Related Files**:

- `_data/output/power_rankings_2025_flat.json` - Shows current long identifiers

---

#### [ISSUE-013] False Positive Songstats Matches Need Similarity Validation

**Command**: `msc run`

**Description**:
The Songstats API search is returning false positive matches where the track returned does not actually match the track
being searched for. These false positives occur when Songstats finds a track with similar keywords but different
content (e.g., karaoke versions, different remixes, cover versions).

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Open `_data/runs/2025_YYYYMMDD_HHMMSS/tracks.json`
3. Search for tracks where `songstats_title` differs significantly from `title`
4. Verify by checking the Songstats page for the track

**Expected Behavior**:

- Songstats search should only match tracks that are the same or very similar versions
- A similarity validation should reject matches that are:
    - Different versions (Karaoke, Instrumental, etc.)
    - Different remixes when searching for a specific remix
    - Completely different tracks with similar keywords
    - Cover versions when searching for originals
- Similarity threshold should be configurable
- Failed similarity checks should log warnings and add tracks to manual review

**Actual Behavior**:

**Example 1: Karaoke Version Mismatch**

```json
{
  "title": "Our Time [Extended Mix]",
  "artist_list": [
    "Afrojack",
    "Martin Garrix",
    "David Guetta & Amél"
  ],
  "songstats_identifiers": {
    "songstats_id": "...",
    "songstats_title": "Our Time - Karaoke Version Originally Performed by Afrojack, Martin Garrix, David Guetta & Amél"
    // ❌ This is a KARAOKE VERSION, not the Extended Mix EDM track!
  }
}
```

- Songstats returns karaoke versions, instrumental versions, or other variants
- No validation that the returned track matches the requested version
- Users get incorrect data for tracks without noticing
- Power rankings include wrong tracks with wrong statistics

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed ✅
- [ ] Deferred

**Priority**: High (affects data accuracy and rankings validity)

**Solution Implemented (2025-12-25)**:

✅ **Keyword-only validation provides optimal balance between accuracy and success rate**:

After testing multiple validation approaches, settled on simple keyword rejection:

- Added `_validate_track_match()` method in ExtractionStage
- Checks Songstats result titles for reject keywords only (no similarity validation)
- Rejects matches containing: karaoke, instrumental, acapella, backing track, cover version, tribute, etc.
- Failed matches are added to manual review queue with rejection reason
- Achieved **89.5% success rate** (334/373 tracks) - matching baseline without over-filtering

**Evolution of Approaches**:

1. **Initial approach**: Dual-threshold validation (title 75% + artist 50% overlap) → 64.1% success (too strict)
2. **Query comparison**: Single query similarity with normalization → 86.7% success (better but complex)
3. **Pattern fixes**: Case-insensitive regex, featuring pattern removal → 88.3% success (still below baseline)
4. **Final approach**: Keyword-only rejection → **89.5% success** ✅ (optimal)

**Why Keyword-Only Won**:

- Similarity validation created false negatives (rejected legitimate matches)
- For curated electronic music library, false positives are rare
- Keyword rejection catches obvious mismatches without over-filtering
- Simpler implementation with clearer logic
- Success rate matches baseline (89.4%) while still providing protection

**Files Modified**:

- `msc/config/constants.py:118-136` - Added REJECT_KEYWORDS tuple (12 keywords), removed individual bracket patterns
  from TITLE_PATTERNS_TO_REMOVE
- `msc/pipeline/extract.py:272-315,486-532` - Added validation method with keyword-only check, stores rejection reason
  in manual review
- `msc/utils/text.py:28-39` - Fixed format_title() to use case-insensitive regex pattern removal

**Implementation Details**:

1. **Keyword Rejection Only** (lines 510-520): Scans Songstats title for reject keywords, returns (False, reason) if
   found
2. **Accept All Others** (line 523): No similarity validation - all non-keyword matches accepted
3. **Pattern Removal Fix**: Uses `re.sub(re.escape(pattern), "", result, flags=re.IGNORECASE)` for case-insensitive
   matching
4. **Clean Logging**: Only logs warnings for keyword rejections (minimal noise)

**Example Rejections**:

- "Our Time [Extended Mix]" → "Our Time - Karaoke Version..." ❌ (keyword: "karaoke")
- "Track Name" → "Track Name (Instrumental)" ❌ (keyword: "instrumental")
- "Song" → "Song - Originally Performed By..." ❌ (keyword: "originally performed")

**Test Results** (Run 2025_20251225_010833):

- Processed: 334 tracks
- Failed: 39 tracks (no Songstats IDs found in database)
- Success rate: **89.5%** (334/373)
- Zero keyword rejections (all 39 failures are legitimate "not found" cases)
- Matches baseline performance without creating false rejections

**Proposed Solution (Original Documentation)**:

**1. Implement Similarity Validation After Search**:

Add validation logic in `ExtractionStage.transform()` after receiving Songstats search results:

```python
# After getting search result
result = search_results[0]

# Validate similarity between search and result
if not self._validate_track_match(track, result):
    self.logger.warning(
        "Similarity check failed for %s - %s (Songstats: '%s')",
        track.primary_artist,
        track.title,
        result.get("title", ""),
    )
    # Add to manual review instead of accepting match
    self.review_queue.add(
        track_id=track_id,
        title=track.title,
        artist=track.primary_artist,
        reason="Failed similarity check - potential false positive",
        metadata={"songstats_title": result.get("title", ""), "query": query},
    )
    continue  # Skip this track, don't store bad match
```

**2. Similarity Validation Algorithm**:

```python
def _validate_track_match(self, track: Track, result: dict) -> bool:
    """Validate that Songstats result matches the searched track.
 
    Args:
        track: Original track from MusicBee
        result: Search result from Songstats API
 
    Returns:
        True if match is valid, False if likely false positive
    """
    songstats_title = result.get("title", "").lower()
    search_title = track.title.lower()

    # Reject obvious mismatches (karaoke, instrumental, cover versions)
    reject_keywords = ["karaoke", "instrumental", "acapella", "backing track", "originally performed"]
    if any(keyword in songstats_title for keyword in reject_keywords):
        return False

    # Calculate title similarity (Levenshtein or fuzzy matching)
    title_similarity = self._calculate_similarity(search_title, songstats_title)

    # Calculate artist similarity
    search_artists = set(a.lower() for a in track.artist_list)
    result_artists = set(a.lower() for a in result.get("artists", []))
    artist_overlap = len(search_artists & result_artists) / max(len(search_artists), 1)

    # Require both title and artist similarity above threshold
    TITLE_THRESHOLD = 0.75  # 75% similarity required
    ARTIST_THRESHOLD = 0.5  # At least 50% artist overlap

    return title_similarity >= TITLE_THRESHOLD and artist_overlap >= ARTIST_THRESHOLD
```

**3. Add Configuration for Thresholds**:

Add to `msc/config/constants.py`:

```python
# Songstats match validation
SIMILARITY_TITLE_THRESHOLD = 0.75
SIMILARITY_ARTIST_THRESHOLD = 0.5
REJECT_KEYWORDS = ["karaoke", "instrumental", "acapella", "backing track", "originally performed", "cover version"]
```

**Libraries to Use**:

- `rapidfuzz` or `python-Levenshtein` for string similarity
- Or built-in `difflib.SequenceMatcher` (no external dependency)

**Files to Modify**:

- `msc/pipeline/extract.py:260-290` - Add similarity validation after search
- `msc/config/constants.py` - Add thresholds and reject keywords
- `msc/utils/text.py` - Add similarity calculation functions

**Testing Requirements**:

- Test with known false positive cases (karaoke versions, etc.)
- Verify threshold tuning doesn't reject valid matches
- Test edge cases (remixes with different names, featuring artists)
- Verify manual review queue receives rejected matches

**Related Files**:

- `_data/runs/2025_20251224_113317/tracks.json` - Contains false positive example

---

#### [ISSUE-014] Artist List Not Splitting on Ampersand (`&`) Separator

**Command**: `msc run`

**Description**:
The artist list extraction is only splitting on commas (`,`) but not on ampersands (`&`), resulting in multiple artists
being grouped together as a single artist entry. This affects data quality and makes artist-based analysis inaccurate.

**Steps to Reproduce**:

1. Run `msc run --year 2025`
2. Open `_data/runs/2025_YYYYMMDD_HHMMSS/tracks.json`
3. Search for tracks with multiple artists
4. Observe that artists separated by `&` are not split

**Expected Behavior**:

- Artist strings should be split on both `,` and ` & ` (with spaces)
- Each artist should be a separate element in `artist_list`
- Featured artists in `(feat. Artist)` should be handled appropriately
- Libpybee may provide native support for artist lists (needs investigation)

**Actual Behavior**:

**Example 1: Multiple Artists Not Split**

```json
{
  "title": "Our Time [Extended Mix]",
  "artist_list": [
    "Afrojack",
    // ✅ Correct
    "Martin Garrix",
    // ✅ Correct
    "David Guetta & Amél"
    // ❌ Should be ["David Guetta", "Amél"]
  ]
}
```

**Example 2: Featured Artist Not Split**

```json
{
  "title": "Inside Our Hearts [Extended Mix]",
  "artist_list": [
    "Martin Garrix & Alesso (feat. Shaun Farrugia)"
    // ❌ Should be ["Martin Garrix", "Alesso", "Shaun Farrugia"]
  ]
}
```

- Artists separated by ` & ` remain as one string
- Featured artists `(feat. ...)` are not extracted
- Inconsistent artist counts affect analysis
- Artist-based rankings are inaccurate

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data accuracy and artist-based analysis)

**Solution Implemented (2025-12-24)**:

✅ Used libpybee's native `artist_list` attribute directly - no more manual string parsing needed!

**Files Modified**:

- `msc/pipeline/extract.py:108,114,125-128` - Now uses `track.artist_list` from libpybee natively
- Removed manual parsing with `split(",")`
- All artist separators (`,`, `&`, `×`, etc.) now handled by libpybee automatically

**Root Cause**:

The current code in `msc/pipeline/extract.py:126-127` only splits on commas:

```python
# Convert artist string to list (MusicBee returns comma-separated string)
artist_list = [a.strip() for a in artist_str.split(",")]
if isinstance(artist_str, str) else[artist_str]
```

This doesn't handle:

- ` & ` separator (with spaces)
- `×` separator
- Featured artists `(feat. ...)`, `(ft. ...)`, `(with ...)`

**Proposed Solution**:

**✅ CONFIRMED: Libpybee Has Native `artist_list` Support**

Investigation of libpybee documentation (https://dyl-m.github.io/libpybee/references/track/) confirms that the Track
class provides:

- `artist` (str) - Single artist string (legacy/display format)
- **`artist_list` (list)** - Native list of artists ✅
- `grouping` (list) - Already returns a list (not a string!) ✅

**Recommended Implementation**:
Use `track.artist_list` instead of manually parsing `track.artist` string.

**Option 2: Enhanced Splitting Logic**

If libpybee doesn't provide native list, enhance the splitting logic:

```python
def split_artists(artist_str: str) -> list[str]:
    """Split artist string on multiple separators.
 
    Handles:
    - Comma separator: "Artist A, Artist B"
    - Ampersand separator: "Artist A & Artist B"
    - Multiplication sign: "Artist A × Artist B"
    - Featured artists: "Artist A (feat. Artist B)"
 
    Args:
        artist_str: Artist string from MusicBee
 
    Returns:
        List of individual artist names
    """
    import re

    # First split on commas
    artists = artist_str.split(",")

    # Then split each part on & and ×
    result = []
    for artist in artists:
        # Remove featured artist annotations (already handled in format_artist)
        # Split on & or ×
        parts = re.split(r'\s+&\s+|\s+×\s+', artist)
        result.extend([p.strip() for p in parts if p.strip()])

    return result
```

**Implementation Location**:

```python
# In msc/pipeline/extract.py around line 125-127
try:
    # Convert artist string to list
    artist_list = split_artists(artist_str) if isinstance(artist_str, str) else [artist_str]

    # Clean each artist name
    artist_list = [format_artist(a) for a in artist_list]
```

**Files to Modify**:

- `msc/pipeline/extract.py:125-127` - Replace simple split with enhanced logic
- `msc/utils/text.py` - Add `split_artists()` function
- `_tests/unit/test_text.py` - Add tests for artist splitting

**Testing Requirements**:

- Test splitting on `,` separator: "A, B" → ["A", "B"]
- Test splitting on ` & ` separator: "A & B" → ["A", "B"]
- Test splitting on ` × ` separator: "A × B" → ["A", "B"]
- Test combined: "A, B & C" → ["A", "B", "C"]
- Test featured artists: "A (feat. B)" → ["A", "B"] or ["A"] (depending on requirements)
- Test edge cases: "A & B, C & D" → ["A", "B", "C", "D"]

**Investigation Needed**:

- Check if libpybee provides native `track.artists` (plural) attribute
- If yes, use native support
- If no, implement enhanced splitting logic

**Related Files**:

- `_data/runs/2025_20251224_113317/tracks.json` - Contains examples of unsplit artists

---

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

*To be documented after investigation*

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
The `msc stats` command is not working properly during user validation testing. The exact error and failure mode need to
be investigated.

**Steps to Reproduce**:

1. Run `msc stats --year 2025`
2. Observe the error/failure

**Expected Behavior**:

- Command should display dataset statistics for the specified year
- Should show total track count
- Should show platform coverage with track counts and percentages
- Should handle missing data gracefully

**Actual Behavior**:

*To be documented after investigation*

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

# TODO: to analyze again

**Testing Requirements**:

- Verify tracks with missing data get fair scores

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
- [x] `msc run`

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

| Issue ID  | Priority       | Status       | Target Version |
|-----------|----------------|--------------|----------------|
| ISSUE-001 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-002 | 🟠 Medium      | ✅ Fixed      | 1.0.0          |
| ISSUE-003 | 🟠 Medium      | ✅ Fixed      | 1.0.0          |
| ISSUE-004 | 🔵 Low         | ✅ Fixed      | 1.0.0          |
| ISSUE-005 | 📈 Enhancement | ⏳ Deferred   | Future         |
| ISSUE-006 | ☢️ Critical    | ✅ Fixed      | 1.0.0          |
| ISSUE-007 | ☢️ Critical    | ✅ Fixed      | 1.0.0          |
| ISSUE-008 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-009 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-010 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-011 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-012 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-013 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-014 | 🔴 High        | ✅ Fixed      | 1.0.0          |
| ISSUE-015 | 🔴 High        | 📋 Planned   | 1.0.0          |
| ISSUE-016 | 🔴 High        | 📋 Planned   | 1.0.0          |
| ISSUE-017 | 🔴 High        | 📋 Planned   | 1.0.0          |
| ISSUE-018 | 🔴 High        | 📋 Planned   | 1.0.0          |
| ISSUE-019 | 🔴 High        | 📋 Planned   | 1.0.0          |

---

## Sign-off Criteria

For 1.0.0 release approval:

- [ ] All Critical issues resolved
- [ ] All High Priority issues resolved or documented as known limitations
- [ ] Documentation updated with any breaking changes
- [ ] README reflects accurate usage for 1.0.0
- [ ] All CLI commands tested end-to-end
- [ ] Error messages are clear and actionable
- [ ] Help text is accurate and comprehensive**
