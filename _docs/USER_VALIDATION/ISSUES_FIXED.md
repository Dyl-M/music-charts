# User Validation - Issues Fixed

This document contains all resolved issues that were discovered and fixed during user validation testing for version
1.0.0.

## Critical Issues

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

## High Priority Issues

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

#### [ISSUE-015] `msc export` Command Fixed - Clean CSV Output

**Command**: `msc export`

**Description**:
The `msc export` command was producing CSV files with nested Python objects (lists and dicts) instead of clean scalar
values. This made the exported data unusable for analysis in spreadsheet applications.

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (blocks data export functionality for 1.0.0)

**Original Issues**:

1. **Nested dicts in CSV**: Fields like `songstats_identifiers` and `youtube_data_most_viewed` rendered as Python dict
   strings
2. **Lists in CSV**: Fields like `artist_list`, `genre`, `grouping` rendered as Python list strings (
   `['value1', 'value2']`)
3. **Duplicate data**: `songstats_identifiers` appeared both as nested dict AND as individual flattened fields
4. **Unnecessary metadata**: Fields like `title`, `year`, `search_query` duplicated data already in JSON

**Solution Implemented (2025-12-26)**:

✅ **1. Simplified Export to Identifiers + Stats Only**:

- CSV now contains only: `track_id`, `songstats_id`, and platform statistics
- Full track metadata remains in `enriched_tracks.json` (the source of truth)
- Clean separation: JSON for full data, CSV for stats analysis

✅ **2. Removed All Nested Structures**:

- Removed nested dict fields: `songstats_identifiers`, `youtube_data_most_viewed`, `youtube_data_songstats_identifiers`
- Removed list fields: `artist_list`, `genre`, `grouping`, `songstats_artists`, `songstats_labels`,
  `youtube_data_all_sources`
- All exported values are now scalars (strings, numbers, or None)

✅ **3. Updated `TrackWithStats.to_flat_dict()`**:

```python
def to_flat_dict(self) -> dict[str, Any]:
    result: dict[str, Any] = {
        "track_id": self.track.identifier,
        "songstats_id": self.songstats_identifiers.songstats_id
    }
    # Add platform stats (already flat scalars)
    result.update(self.platform_stats.to_flat_dict())
    return result
```

✅ **4. Fixed Legacy Key Mapping**:

- `from_legacy_json()`: Maps legacy `"label"` key to `"grouping"` field
- `from_flat_dict()`: Handles both `"label"` and `"grouping"` keys

**Files Modified**:

- `msc/models/stats.py` - `TrackWithStats.to_flat_dict()`, `from_legacy_json()`, `from_flat_dict()`
- `_tests/unit/test_stats_model.py` - Updated tests for new behavior
- `_tests/unit/test_commands_exporters.py` - Updated HTML export test

**Test Results**:

```
$ uv run pytest _tests/unit/test_stats_model.py _tests/unit/test_commands_exporters.py -v
============================= 32 passed in 0.57s ==============================
```

**CSV Output Sample**:

```csv
track_id,songstats_id,spotify_streams_total,spotify_playlist_reach_total,...
f68b210b,em0th986,10187,11.5,...
```

---

#### [ISSUE-016] `msc stats` Command Fixed - Platform Coverage Now Accurate

**Command**: `msc stats`

**Description**:
The `msc stats` command had multiple critical issues preventing accurate platform coverage statistics. Fixed all file
path issues, attribute name mismatches, and implemented proper platform presence detection using Songstats API data.

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (blocks analytics functionality for 1.0.0)

**Original Issues**:

1. **Wrong file path**: Tried to load from `_data/output/2025/stats.json` instead of `_data/output/enriched_tracks.json`
2. **Wrong platform attribute names**: Used incorrect attributes (e.g., `streams` instead of `streams_total`)
3. **Missing platforms**: Only checked 5 platforms instead of all 10
4. **Flawed platform presence logic**: Checked `is not None` which incorrectly counted tracks with 0 values
5. **Amazon Music 0% coverage**: Platform name normalization issue (`"amazon"` vs `"amazon_music"`)

**Solution Implemented (2025-12-25)**:

✅ **1. Fixed File Path**:

- Changed from `settings.year_output_dir / "stats.json"` → `settings.output_dir / "enriched_tracks.json"`
- Now correctly loads enriched tracks data

✅ **2. Fixed Platform Attribute Names**:

- Spotify: `"streams"` → `"streams_total"`
- YouTube: `"views"` → `"video_views_total"`
- Deezer: `"fans"` → `"playlist_reach_total"`
- All attributes now match model field names

✅ **3. Added All 10 Platforms**:

- Added missing platforms: SoundCloud, Tidal, Amazon Music, Beatport, 1001Tracklists
- Now displays coverage for all supported streaming platforms

✅ **4. Implemented Proper Platform Presence Detection**:

**Architecture Decision**: Two-phase platform availability checking

**Phase 1 - Get Available Platforms** (`SongstatsClient.get_available_platforms()`):

- Calls `/tracks/info` endpoint to determine which platforms track exists on
- Returns `links` array showing actual platform availability
- Normalizes platform names: `"tracklist"` → `"1001tracklists"`, `"amazon"` → `"amazon_music"`

**Phase 2 - Filter Platform Stats** (`PlatformStats.from_flat_dict()`):

- Only creates platform stat instances for available platforms
- Correctly distinguishes "not on platform" (None) from "on platform with 0 stats" (0)
- Uses name mapping dict for consistent normalization

**Key Implementation Details**:

```python
# msc/clients/songstats.py - Platform name normalization
platform_name_map = {
    "tracklist": "1001tracklists",
    "amazon": "amazon_music",
}
normalized = {platform_name_map.get(platform, platform) for platform in platforms}

# msc/models/stats.py - Field name normalization
field_to_source = {
    "tracklists": "1001tracklists",
}
normalized_name = field_to_source.get(field_name, field_name)
if normalized_name in available_platforms:
    platform_kwargs[field_name] = model_class(**platform_data)


# msc/cli.py - Platform presence check
def _has_platform_data(track: TrackWithStats, platform_attr: str) -> bool:
    """Check if track is present on a specific platform.

    A track is considered present if ANY field in the platform stats
    has a non-None value (even if it's 0).
    """
    platform = getattr(track.platform_stats, platform_attr, None)
    if platform is None:
        return False

    platform_dict = platform.model_dump()
    return any(value is not None for value in platform_dict.values())
```

**Why This Architecture?**:

The Songstats `/tracks/stats` endpoint returns ALL requested platforms with 0 values even when a track doesn't exist on
that platform. This makes it impossible to distinguish:

- Track not on platform (shouldn't count)
- Track on platform with 0 activity (should count)

By checking `/tracks/info` first, we get the authoritative list of platforms where the track actually exists, then use
that to filter which platform stats to create.

**Files Modified**:

- `msc/clients/songstats.py:334-370` - Added `get_available_platforms()` method with normalization dict
- `msc/models/stats.py:149-227` - Updated `from_flat_dict()` with `available_platforms` parameter and field name
  normalization
- `msc/pipeline/enrich.py:169-210, 361-383` - Call `get_available_platforms()` before fetching stats, pass to
  `_create_platform_stats()`
- `msc/cli.py:534-585, 598-630` - Fixed file path, attribute names, added all 10 platforms, updated presence detection

**Test Results** (Run 2025_20251225_233149):

```
=== Dataset Statistics - 2025 ===

Total Tracks: 329

Platform Coverage:
  Spotify          320 tracks ( 97.3%)
  Apple Music      315 tracks ( 95.7%)
  YouTube          312 tracks ( 94.8%)
  Amazon Music     303 tracks ( 92.1%)  ✅ Now showing correctly!
  Deezer           306 tracks ( 93.0%)
  SoundCloud       236 tracks ( 71.7%)
  Tidal            301 tracks ( 91.5%)
  TikTok           262 tracks ( 79.6%)
  Beatport         261 tracks ( 79.3%)
  1001Tracklists   253 tracks ( 76.9%)
```

**Platform Name Normalization Map**:

Three different naming conventions exist:

1. **API source names**: `"tracklist"`, `"amazon"` (from `/tracks/info` endpoint)
2. **Normalized comparison names**: `"1001tracklists"`, `"amazon_music"` (in available_platforms set)
3. **Model field names**: `"tracklists"`, `"amazon_music"` (Pydantic model attributes)

The normalization ensures all three conventions map correctly:

- `get_available_platforms()`: API → Comparison names
- `from_flat_dict()`: Field → Comparison names for lookup

**Benefits**:

- ✅ Accurate platform coverage statistics (no more 0% or 100% false readings)
- ✅ Distinguishes "not on platform" from "on platform with no activity"
- ✅ Preserves all platform data in JSON for weight computation (ISSUE-019)
- ✅ Cleaner, more maintainable code with dict-based normalization
- ✅ All 10 platforms properly tracked

**Related Issues**:

- Enables proper weight adjustment for ISSUE-019 (Power Ranking Weights)
- Provides accurate data availability information for analytics

---

#### [ISSUE-017] Power Ranking Scores Not in 0-100 Range (Design Issue)

**Command**: `msc run --stage rank`

**Description**:
The power ranking scores by category were not in the expected 0-100 range as they were in the legacy implementation. The
normalization strategy was producing scores in 0-1 range, which affected readability and comparison with historical
rankings.

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data quality and comparison with legacy rankings)

**Solution Implemented (2025-12-26)**:

✅ **1. Updated MinMaxNormalizer with `feature_range` Parameter**:

Added configurable output range to MinMaxNormalizer (default 0-100):

```python
class MinMaxNormalizer(NormalizationStrategy):
    def __init__(self, feature_range: tuple[float, float] = (0.0, 100.0)) -> None:
        self.feature_range = feature_range
        self._range_min = feature_range[0]
        self._range_max = feature_range[1]
        self._range_span = self._range_max - self._range_min
        self._midpoint = (self._range_min + self._range_max) / 2
```

✅ **2. Updated CategoryScore Model**:

- `raw_score`: Changed constraint from `le=1.0` to `le=100.0`
- `weight`: Changed from `int` to `float` (now represents `availability × importance`)

✅ **3. Refactored PowerRankingScorer with Legacy Algorithm**:

Implemented the legacy algorithm from `power_ranking_2024.ipynb`:

- Per-metric normalization to 0-100 range
- Data availability weighting per metric
- Category weight = `avg_availability × importance_multiplier`
- Final score = **weighted average** (0-100 range) instead of weighted sum

**Files Modified**:

- `msc/analysis/normalizers.py:15-88` - Added `feature_range` parameter to MinMaxNormalizer
- `msc/models/ranking.py:25-65` - Updated CategoryScore constraints
- `msc/analysis/scorer.py:145-280` - Refactored with legacy algorithm

**Test Results**:

✅ All 100 tests passing (normalizers, scorer, ranking model)

---

#### [ISSUE-019] Power Ranking Weights Not Adjusted from Data Availability

**Command**: `msc run --stage rank`

**Description**:
The power ranking weights were static and did not adjust based on actual data availability from each platform. The
legacy
implementation adjusted weights based on data availability rate, ensuring fair comparison between tracks with different
platform coverage.

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects ranking fairness and accuracy)

**Solution Implemented (2025-12-26)**:

✅ **Implemented Legacy Algorithm with Dynamic Weight Adjustment**:

The new `PowerRankingScorer` now computes weights dynamically based on data availability:

**1. Per-Metric Availability Calculation**:

```python
def _compute_availability_weights(metric_values: dict[str, list[float]]) -> dict[str, float]:
    """Availability = proportion of tracks with non-zero value for this metric."""
    availability = {}
    for metric_name, values in metric_values.items():
        non_zero_count = sum(1 for v in values if v > 0)
        availability[metric_name] = non_zero_count / len(values)
    return availability
```

**2. Category Score with Availability Weighting**:

```python
# Category score = weighted average of normalized metrics by availability
# Formula: score = sum(normalized_stat × availability) / sum(availability)
weighted_sum = sum(normalized[metric] * availability[metric] for metric in metrics)
score = weighted_sum / total_availability
```

**3. Effective Category Weight**:

```python
# Category weight = avg_availability × importance_multiplier
avg_availability = sum(availability_weights.values()) / len(metrics)
category_weight = avg_availability * importance_multiplier
```

**4. Final Score as Weighted Average**:

```python
# Final score = weighted average (0-100 range)
total_score = sum(category_score * category_weight) / sum(category_weights)
```

**Key Algorithm Changes**:

| Aspect             | Before                  | After (Legacy Algorithm)     |
|--------------------|-------------------------|------------------------------|
| Normalization      | 0-1 range               | 0-100 range                  |
| Per-stat weighting | None (uniform)          | By data availability         |
| Category weight    | Just importance (1,2,4) | availability × importance    |
| Final score        | Weighted **sum** (0-32) | Weighted **average** (0-100) |

**Files Modified**:

- `msc/analysis/scorer.py:145-280` - Complete refactor with new algorithm

**Benefits**:

- ✅ Tracks with missing data get fair scores (not penalized for missing platforms)
- ✅ Metrics with low availability contribute less to rankings
- ✅ Final scores in readable 0-100 range
- ✅ Matches legacy implementation behavior

**Test Results**:

✅ All scorer tests updated and passing

---

#### [ISSUE-018] Missing YouTube Data Despite Songstats Data Availability

**Command**: `msc run --stage enrich`

**Description**:
Many tracks were not receiving YouTube data during enrichment even though YouTube videos existed in Songstats. The issue
occurred when tracks only had Topic channel videos (auto-generated YouTube channels ending with " - Topic") and no
regular channel videos.

**Status**:

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Deferred

**Priority**: High (affects data completeness)

**Root Cause Analysis**:

The `_extract_youtube_videos()` method in `SongstatsClient` was designed to prefer non-Topic channel videos for
`most_viewed`. When ONLY Topic videos existed:

1. `non_topic_videos` list was empty
2. `most_viewed` was set to empty dict `{}`
3. In `enrich.py`, validation checked `most_viewed.get("ytb_id")` which was falsy for empty dict
4. YouTube data was rejected even though videos existed

**Data from Investigation**:

- **77 out of 329 tracks** (23%) had no YouTube data
- Of those, **~66% (10/15 sampled)** had Topic-only videos being rejected
- Remaining **~33% (5/15 sampled)** genuinely had no YouTube videos in Songstats

**Example Before Fix**:

```python
# Track: "<32n [Extended Mix]" (songstats_id: 4c5038go)
# Songstats API returned:
{
    "most_viewed": {},  # Empty because only Topic video exists
    "most_viewed_is_topic": True,
    "all_sources": [
        {"ytb_id": "-becj_4ipV4", "views": 11177, "channel_name": "Release - Topic"}
    ]
}
# Result: YouTube data REJECTED (validation fails on empty most_viewed)
```

**Solution Implemented (2025-12-26)**:

✅ **Added Topic Video Fallback in `_extract_youtube_videos()`**:

When no non-Topic videos exist, fall back to the most viewed Topic video instead of returning empty dict:

```python
# Find most viewed non-Topic video, fall back to Topic video if none
non_topic_videos = [
    vid for vid in video_list
    if " - Topic" not in vid["channel_name"]
]

if non_topic_videos:
    most_viewed = non_topic_videos[0]

elif video_list:
    # Fallback to most viewed Topic video if no non-Topic videos exist
    most_viewed = video_list[0]

else:
    most_viewed = {}
```

**Example After Fix**:

```python
# Track: "<32n [Extended Mix]" (songstats_id: 4c5038go)
# Now returns:
{
    "most_viewed": {
        "ytb_id": "-becj_4ipV4",
        "views": 11177,
        "channel_name": "Release - Topic"  # Topic video used as fallback
    },
    "most_viewed_is_topic": True,
    "all_sources": [...]
}
# Result: YouTube data CAPTURED
```

**Files Modified**:

- `msc/clients/songstats.py:657-671` - Added Topic video fallback logic
- `msc/clients/songstats.py:257-265` - Updated docstring to reflect new behavior
- `msc/clients/songstats.py:640-642` - Updated internal docstring
- `_tests/unit/test_songstats_client.py:454-482` - Updated test for new fallback behavior

**Test Results**:

✅ All 74 Songstats client tests passing

**Impact**:

- ~50 additional tracks will now receive YouTube data (Topic-only videos)
- `YouTubeVideo.is_topic_channel` property can identify Topic channel videos
- `most_viewed_is_topic` flag indicates if overall most viewed video was from Topic channel
- No changes needed to enrichment stage validation logic

**Related Issues**:

- See ISSUE-007: Enrichment Stage Failing on Empty YouTube Data (fixed earlier, different root cause)

---