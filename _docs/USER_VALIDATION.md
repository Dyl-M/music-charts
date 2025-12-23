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

---

### Enhancement Requests

*Feature requests discovered during validation*

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

**Bugs Fixed During Testing**:

1. Fixed extraction stage dictionary access bug (libpybee.Track objects vs dicts)
2. Fixed genre/label list wrapping issue (already lists from MusicBee)
3. Fixed log overflow UX issue with dual-level logging and minimal ConsoleObserver output

**Improvements Implemented**:

1. Implemented run-based directory structure for better data organization
2. Isolated manual review items per run to prevent accumulation
3. Moved checkpoints to run directory to prevent state contamination between runs
4. Reorganized data directories (runs/, logs/, output/)

**Notes**:

- Windows users must set `export PYTHONIOENCODING=utf-8` before running to display emojis correctly
- Pipeline successfully extracts and processes tracks
- Console output is now clean with progress bars only (verbose logging available in file)

---

## Resolution Tracking

| Issue ID  | Priority | Status | Assigned | Target Version |
|-----------|----------|--------|----------|----------------|
| ISSUE-001 | High     | Fixed  | @Dyl-M   | 1.0.0          |
| ISSUE-002 | Medium   | Fixed  | @Dyl-M   | 1.0.0          |
| ISSUE-003 | Medium   | Fixed  | @Dyl-M   | 1.0.0          |

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
