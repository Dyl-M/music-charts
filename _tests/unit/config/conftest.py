"""Fixtures for config module tests."""

# Standard library
from pathlib import Path

# Third-party
import pytest


@pytest.fixture
def mock_settings_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up environment for Settings tests.

    Creates temporary directories and sets environment variables.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.
        monkeypatch: Pytest's monkeypatch fixture.

    Returns:
        Path: The temporary directory root.
    """
    # Create directory structure
    data_dir = tmp_path / "_data"
    tokens_dir = tmp_path / "_tokens"
    config_dir = tmp_path / "_config"

    data_dir.mkdir()
    tokens_dir.mkdir()
    config_dir.mkdir()

    # Set environment variables
    monkeypatch.setenv("MSC_DATA_DIR", str(data_dir))
    monkeypatch.setenv("MSC_TOKENS_DIR", str(tokens_dir))
    monkeypatch.setenv("MSC_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("MSC_YEAR", "2026")

    return tmp_path


@pytest.fixture
def temp_songstats_key(tmp_path: Path) -> Path:
    """Create a temporary Songstats API key file.

    Args:
        tmp_path: Pytest's built-in temporary path fixture.

    Returns:
        Path: Path to the created key file.
    """
    tokens_dir = tmp_path / "_tokens"
    tokens_dir.mkdir(exist_ok=True)
    key_file = tokens_dir / "songstats_key.txt"
    key_file.write_text("test_api_key_12345", encoding="utf-8")
    return key_file
