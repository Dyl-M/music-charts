"""Fixtures for models module tests."""

# Third-party
import pytest

# Local
from msc.models.track import SongstatsIdentifiers, Track


@pytest.fixture
def sample_track() -> Track:
    """Create a minimal valid Track instance.

    Returns:
        Track: A track with only required fields.
    """
    return Track(
        title="sample track",
        artist_list=["artist a"],
        year=2024,
    )


@pytest.fixture
def sample_track_with_all_fields() -> Track:
    """Create a Track with all optional fields populated.

    Returns:
        Track: A fully populated track.
    """
    return Track(
        title="complete track extended mix",
        artist_list=["artist a", "artist b", "artist c"],
        year=2024,
        genre=["house", "tech house"],
        grouping=["label a", "label b"],
        search_query="artist a artist b complete track",
        songstats_identifiers=SongstatsIdentifiers(
            songstats_id="abc12345",
            songstats_title="Complete Track",
            isrc="USRC12345678",
            songstats_artists=["Artist A", "Artist B"],
            songstats_labels=["Label A"],
        ),
    )


@pytest.fixture
def sample_songstats_ids() -> SongstatsIdentifiers:
    """Create a SongstatsIdentifiers instance.

    Returns:
        SongstatsIdentifiers: Sample identifiers.
    """
    return SongstatsIdentifiers(
        songstats_id="xyz98765",
        songstats_title="Sample Title",
        isrc="GBRC54321098",
        songstats_artists=["Sample Artist"],
        songstats_labels=["Sample Label"],
    )
