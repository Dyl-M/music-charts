"""Shared fixtures for unit tests.

This file contains fixtures used across multiple test modules.
Module-specific fixtures should be defined in their respective conftest.py files.
"""

# Standard library
import json
from pathlib import Path

# Third-party
import pytest


@pytest.fixture
def sample_track_data() -> dict:
    """Sample track data for testing.

    Returns:
        dict: A minimal track data dictionary with all required fields.
    """
    return {
        "title": "sample track extended mix",
        "artist_list": ["artist a", "artist b"],
        "label": ["sample records"],
        "genre": ["house"],
        "request": "artist a, artist b sample track",
        "data": {
            "s_id": "abc123",
            "s_title": "Sample Track",
        },
    }


@pytest.fixture
def sample_stats_data() -> dict:
    """Sample statistics data for testing.

    Returns:
        dict: A dictionary with sample platform statistics.
    """
    return {
        "spotify_streams": 1000000,
        "spotify_playlist_reach": 500000,
        "spotify_playlist_count": 150,
        "spotify_popularity_peak": 75,
        "apple_music_playlist_reach": 200000,
        "deezer_popularity_peak": 60,
        "youtube_views": 2000000,
    }


@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory structure.

    Creates the standard _data directory layout used by the application.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the created _data directory.
    """
    data_dir = tmp_path / "_data"
    (data_dir / "input").mkdir(parents=True)
    (data_dir / "output").mkdir(parents=True)
    (data_dir / "cache").mkdir(parents=True)
    (data_dir / "logs").mkdir(parents=True)
    (data_dir / "runs").mkdir(parents=True)
    return data_dir


@pytest.fixture
def temp_tokens_dir(tmp_path: Path) -> Path:
    """Create a temporary tokens directory with mock credentials.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the created _tokens directory.
    """
    tokens_dir = tmp_path / "_tokens"
    tokens_dir.mkdir(parents=True)

    # Create mock API key file
    (tokens_dir / "songstats_key.txt").write_text(
        "mock_api_key_for_testing", encoding="utf-8"
    )

    return tokens_dir


@pytest.fixture
def temp_youtube_oauth(tmp_path: Path) -> Path:
    """Create temporary YouTube OAuth file for testing.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the created OAuth JSON file.
    """
    oauth_file = tmp_path / "_tokens" / "oauth.json"
    oauth_file.parent.mkdir(parents=True, exist_ok=True)

    oauth_data = {
        "installed": {
            "client_id": "test_client_id.apps.googleusercontent.com",
            "client_secret": "test_client_secret",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }

    oauth_file.write_text(
        json.dumps(oauth_data, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    return oauth_file


@pytest.fixture
def temp_youtube_credentials(tmp_path: Path) -> Path:
    """Create temporary YouTube credentials file for testing.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the created credentials JSON file.
    """
    creds_file = tmp_path / "_tokens" / "credentials.json"
    creds_file.parent.mkdir(parents=True, exist_ok=True)

    creds_data = {
        "token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "test_client_id.apps.googleusercontent.com",
        "client_secret": "test_client_secret",
        "scopes": [
            "https://www.googleapis.com/auth/youtube.readonly",
            "https://www.googleapis.com/auth/youtube.force-ssl",
        ],
    }

    creds_file.write_text(
        json.dumps(creds_data, ensure_ascii=False, indent=4), encoding="utf-8"
    )
    return creds_file
