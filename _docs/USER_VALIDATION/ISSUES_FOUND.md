# User Validation - Issues Found

This document contains all open and pending issues discovered during user validation testing for version 1.0.0.

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

- [x] Planned
- [x] In Progress
- [x] Fixed
- [ ] Won't Fix

**Priority**: Enhancement (not blocking, but significantly impacts development workflow)

**Resolution (2025-12-26)**:

Implemented CLI test mode with full feature set.

**New CLI Flags Added to `msc run`**:

- `--test-mode` / `-t`: Run with test library fixture (mocked APIs, no quota usage)
- `--limit N` / `-l N`: Limit number of tracks to process
- `--cleanup`: Delete run directory after completion (for test iterations)

**Implementation Details**:

- Test mode uses `_tests/fixtures/test_library.xml` (5 tracks, 4 playlists)
- Mock Songstats client auto-injected with predefined responses
- No real API calls = no quota usage, fast execution
- Works with existing `--stage` and `--new-run` flags

**Coverage Improvements**:

- CLI: 91% (up from 56%)
- Orchestrator: 91% (up from 79%)
- Songstats Client: 92% (up from 80%)
- Track Model: 100% (up from 77%)
- Overall: **94%** (1096 tests passing)

**Test Quality Improvements (2025-12-26)**:

- Fixed duplicate class definitions in `test_songstats.py`
- Fixed unused variable warnings across test files
- Added proper `# noinspection` comments for intentional code patterns
- All IDE/linter warnings in test files resolved

**Usage Examples**:

```bash
msc run --test-mode                    # Run with test fixtures
msc run --test-mode --limit 2          # Test with only 2 tracks
msc run --test-mode --cleanup          # Auto-cleanup after test
msc run --test-mode --stage extract    # Test extraction only
```
