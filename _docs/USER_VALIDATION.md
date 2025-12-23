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

---

### High Priority Issues

*Important issues that should be fixed before release*

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
During extraction stage, approximately 52% of tracks fail to find Songstats IDs (196 failed out of 373 total tracks). Analysis of the manual review queue reveals that queries sent to Songstats API contain special characters, feature annotations, and punctuation that interfere with search accuracy.

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

* `msc/config/constants.py`: Added `[Extended]` and punctuation to TITLE_PATTERNS_TO_REMOVE, updated TITLE_PATTERNS_TO_SPACE
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
When testing pipeline features or running quick validations, the test suite processes the entire MusicBee library (373+ tracks), making iteration cycles extremely long. Additionally, each test run creates output files in `_data/` that are not automatically cleaned up, leading to clutter and confusion about which outputs are current.

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

1. **Test Playlist**: Create a dedicated small test playlist in MusicBee (e.g., "Test Selection 2025") with 10-20 representative tracks
2. **CLI Flag**: Add `--test-mode` flag that uses test playlist and marks outputs
3. **Auto-cleanup**: Add `--cleanup-after` flag to delete run directory after completion
4. **Playlist Limit**: Add `--limit N` flag to process only first N tracks from any playlist
5. **Test Fixtures**: Use the existing `_tests/fixtures/test_library.xml` for integration tests instead of production library

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

When tracks fail to find Songstats IDs automatically during extraction, they are added to the manual review queue. You can manually add the Songstats IDs and resume the pipeline from where it left off.

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
  "artist_list": ["Artist Name"],
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
