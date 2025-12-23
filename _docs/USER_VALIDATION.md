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
During pipeline execution, the console is flooded with INFO/WARNING log messages while progress bars are attempting to display. This creates visual clutter and makes it impossible to track actual progress.

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
- ISSUE-001: Log overflow during pipeline execution (High Priority)

**Bugs Fixed During Testing**:
1. Fixed extraction stage dictionary access bug (libpybee.Track objects vs dicts)
2. Fixed genre/label list wrapping issue (already lists from MusicBee)

**Notes**:
- Windows users must set `export PYTHONIOENCODING=utf-8` before running to display emojis correctly
- Pipeline successfully extracts and processes tracks, but console output needs UX improvement

---

## Resolution Tracking

| Issue ID | Priority | Status | Assigned | Target Version |
|----------|----------|--------|----------|----------------|
| - | - | - | - | - |

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
