"""Fixtures for integration tests."""

# Standard library
import os
from pathlib import Path

# Third-party
import pytest


@pytest.fixture
def test_library_path() -> Path:
    """Get path to test MusicBee library fixture."""
    return Path(__file__).parent.parent / "fixtures" / "test_library.xml"


@pytest.fixture
def songstats_api_key() -> str | None:
    """Get Songstats API key from environment or token file."""
    # Check environment
    key = os.environ.get("MSC_SONGSTATS_API_KEY")
    if key:
        return key

    # Check token file
    token_file = Path("_tokens/songstats_key.txt")
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()

    return None


@pytest.fixture
def youtube_credentials_path() -> Path | None:
    """Get path to YouTube OAuth credentials if available."""
    creds_path = Path("_tokens/credentials.json")
    if creds_path.exists():
        return creds_path
    return None


@pytest.fixture
def skip_without_api_key(songstats_api_key: str | None):
    """Skip test if no API key available."""
    if songstats_api_key is None:
        pytest.skip("Songstats API key not available")
    return songstats_api_key


@pytest.fixture
def skip_without_youtube_creds(youtube_credentials_path: Path | None):
    """Skip test if no YouTube credentials available."""
    if youtube_credentials_path is None:
        pytest.skip("YouTube credentials not available")
    return youtube_credentials_path
