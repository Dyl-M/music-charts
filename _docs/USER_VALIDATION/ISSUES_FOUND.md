# User Validation - Issues Found

This document contains all open and pending issues discovered during user validation testing for version 1.0.0.

## High Priority Issues

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
