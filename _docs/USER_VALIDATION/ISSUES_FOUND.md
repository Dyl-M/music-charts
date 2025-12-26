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
