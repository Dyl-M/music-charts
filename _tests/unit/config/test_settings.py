"""Unit tests for settings module.

Tests Settings class, get_settings function, and configuration loading.
"""

# Standard library
import json
from pathlib import Path

# Third-party
import pytest

# Local
from msc.config.settings import PROJECT_ROOT, Settings, get_settings


class TestProjectRoot:
    """Tests for PROJECT_ROOT constant."""

    @staticmethod
    def test_project_root_exists() -> None:
        """Should point to existing directory."""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    @staticmethod
    def test_project_root_contains_msc() -> None:
        """Should contain msc package directory."""
        assert (PROJECT_ROOT / "msc").exists()

    @staticmethod
    def test_project_root_contains_pyproject() -> None:
        """Should contain pyproject.toml."""
        assert (PROJECT_ROOT / "pyproject.toml").exists()


class TestSettingsDefaults:
    """Tests for Settings default values."""

    @staticmethod
    def test_default_year() -> None:
        """Should default to 2026."""
        settings = Settings()
        assert settings.year == 2026

    @staticmethod
    def test_default_playlist_id() -> None:
        """Should default to 4361."""
        settings = Settings()
        assert settings.playlist_id == "4361"

    @staticmethod
    def test_default_songstats_rate_limit() -> None:
        """Should default to 10 requests per second."""
        settings = Settings()
        assert settings.songstats_rate_limit == 10

    @staticmethod
    def test_default_youtube_rate_limit() -> None:
        """Should default to 10 requests per second."""
        settings = Settings()
        assert settings.youtube_rate_limit == 10

    @staticmethod
    def test_default_youtube_quota() -> None:
        """Should default to 10000 daily quota."""
        settings = Settings()
        assert settings.youtube_quota_daily == 10000

    @staticmethod
    def test_default_data_dir() -> None:
        """Should default to PROJECT_ROOT/_data."""
        settings = Settings()
        assert settings.data_dir == PROJECT_ROOT / "_data"

    @staticmethod
    def test_default_tokens_dir() -> None:
        """Should default to PROJECT_ROOT/_tokens."""
        settings = Settings()
        assert settings.tokens_dir == PROJECT_ROOT / "_tokens"

    @staticmethod
    def test_default_songstats_api_key_is_none() -> None:
        """Should default to None for API key."""
        settings = Settings()
        assert settings.songstats_api_key is None


class TestSettingsProperties:
    """Tests for Settings computed properties."""

    @staticmethod
    def test_input_dir() -> None:
        """Should return data_dir/input."""
        settings = Settings()
        assert settings.input_dir == settings.data_dir / "input"

    @staticmethod
    def test_output_dir() -> None:
        """Should return data_dir/output."""
        settings = Settings()
        assert settings.output_dir == settings.data_dir / "output"

    @staticmethod
    def test_cache_dir() -> None:
        """Should return data_dir/cache."""
        settings = Settings()
        assert settings.cache_dir == settings.data_dir / "cache"

    @staticmethod
    def test_year_output_dir() -> None:
        """Should return output_dir/year."""
        settings = Settings()
        assert settings.year_output_dir == settings.output_dir / str(settings.year)


class TestSettingsFromEnv:
    """Tests for Settings loading from environment."""

    @staticmethod
    def test_loads_year_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load year from MSC_YEAR environment variable."""
        monkeypatch.setenv("MSC_YEAR", "2024")
        settings = Settings()
        assert settings.year == 2024

    @staticmethod
    def test_loads_playlist_id_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load playlist_id from MSC_PLAYLIST_ID."""
        monkeypatch.setenv("MSC_PLAYLIST_ID", "9999")
        settings = Settings()
        assert settings.playlist_id == "9999"

    @staticmethod
    def test_loads_songstats_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
        """Should load API key from MSC_SONGSTATS_API_KEY."""
        monkeypatch.setenv("MSC_SONGSTATS_API_KEY", "env_key_12345")
        settings = Settings()
        assert settings.songstats_api_key == "env_key_12345"

    @staticmethod
    def test_loads_data_dir_from_env(
            tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Should load data_dir from MSC_DATA_DIR."""
        custom_dir = tmp_path / "custom_data"
        custom_dir.mkdir()
        monkeypatch.setenv("MSC_DATA_DIR", str(custom_dir))
        settings = Settings()
        assert settings.data_dir == custom_dir


class TestGetSongstatsKey:
    """Tests for get_songstats_key method."""

    @staticmethod
    def test_returns_env_key_if_set(monkeypatch: pytest.MonkeyPatch) -> None:
        """Should return API key from environment if set."""
        monkeypatch.setenv("MSC_SONGSTATS_API_KEY", "env_key")
        settings = Settings()
        assert settings.get_songstats_key() == "env_key"

    @staticmethod
    def test_returns_file_key_if_exists(tmp_path: Path) -> None:
        """Should return API key from file if exists."""
        tokens_dir = tmp_path / "_tokens"
        tokens_dir.mkdir()
        key_file = tokens_dir / "songstats_key.txt"
        key_file.write_text("file_key_12345\n", encoding="utf-8")

        settings = Settings(tokens_dir=tokens_dir)
        assert settings.get_songstats_key() == "file_key_12345"

    @staticmethod
    def test_strips_whitespace_from_file_key(tmp_path: Path) -> None:
        """Should strip whitespace from file key."""
        tokens_dir = tmp_path / "_tokens"
        tokens_dir.mkdir()
        key_file = tokens_dir / "songstats_key.txt"
        key_file.write_text("  key_with_whitespace  \n", encoding="utf-8")

        settings = Settings(tokens_dir=tokens_dir)
        assert settings.get_songstats_key() == "key_with_whitespace"

    @staticmethod
    def test_prefers_env_key_over_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Should prefer environment key over file key."""
        tokens_dir = tmp_path / "_tokens"
        tokens_dir.mkdir()
        key_file = tokens_dir / "songstats_key.txt"
        key_file.write_text("file_key", encoding="utf-8")

        monkeypatch.setenv("MSC_SONGSTATS_API_KEY", "env_key")
        settings = Settings(tokens_dir=tokens_dir)
        assert settings.get_songstats_key() == "env_key"

    @staticmethod
    def test_raises_if_no_key_available(tmp_path: Path) -> None:
        """Should raise ValueError if no key found."""
        tokens_dir = tmp_path / "_tokens"
        tokens_dir.mkdir()  # No key file

        settings = Settings(tokens_dir=tokens_dir)
        with pytest.raises(ValueError, match="Songstats API key not found"):
            settings.get_songstats_key()


class TestYouTubeCredentials:
    """Tests for YouTube credential methods."""

    @staticmethod
    def test_get_youtube_oauth_loads_file(tmp_path: Path) -> None:
        """Should load OAuth config from file."""
        oauth_file = tmp_path / "oauth.json"
        oauth_data = {"installed": {"client_id": "test_id"}}
        oauth_file.write_text(json.dumps(oauth_data), encoding="utf-8")

        settings = Settings(youtube_oauth_path=oauth_file)
        result = settings.get_youtube_oauth()
        assert result == oauth_data

    @staticmethod
    def test_get_youtube_oauth_raises_if_missing(tmp_path: Path) -> None:
        """Should raise ValueError if OAuth file missing."""
        missing_file = tmp_path / "missing.json"
        settings = Settings(youtube_oauth_path=missing_file)

        with pytest.raises(ValueError, match="YouTube OAuth file not found"):
            settings.get_youtube_oauth()

    @staticmethod
    def test_get_youtube_credentials_returns_none_if_missing(tmp_path: Path) -> None:
        """Should return None if credentials file missing."""
        missing_file = tmp_path / "missing.json"
        settings = Settings(youtube_credentials_path=missing_file)
        assert settings.get_youtube_credentials() is None

    @staticmethod
    def test_get_youtube_credentials_loads_file(tmp_path: Path) -> None:
        """Should load credentials from file."""
        creds_file = tmp_path / "credentials.json"
        creds_data = {"token": "access_token"}
        creds_file.write_text(json.dumps(creds_data), encoding="utf-8")

        settings = Settings(youtube_credentials_path=creds_file)
        result = settings.get_youtube_credentials()
        assert result == creds_data

    @staticmethod
    def test_save_youtube_credentials(tmp_path: Path) -> None:
        """Should save credentials to file."""
        creds_file = tmp_path / "credentials.json"
        settings = Settings(youtube_credentials_path=creds_file)

        creds_data = {"token": "new_token", "refresh_token": "refresh"}
        settings.save_youtube_credentials(creds_data)

        saved = json.loads(creds_file.read_text(encoding="utf-8"))
        assert saved == creds_data


class TestEnsureDirectories:
    """Tests for ensure_directories method."""

    @staticmethod
    def test_creates_all_directories(tmp_path: Path) -> None:
        """Should create all required directories."""
        data_dir = tmp_path / "_data"
        tokens_dir = tmp_path / "_tokens"
        config_dir = tmp_path / "_config"

        settings = Settings(
            data_dir=data_dir,
            tokens_dir=tokens_dir,
            config_dir=config_dir,
        )
        settings.ensure_directories()

        assert data_dir.exists()
        assert (data_dir / "input").exists()
        assert (data_dir / "output").exists()
        assert (data_dir / "cache").exists()
        assert tokens_dir.exists()
        assert config_dir.exists()

    @staticmethod
    def test_creates_year_output_dir(tmp_path: Path) -> None:
        """Should create year-specific output directory."""
        data_dir = tmp_path / "_data"
        settings = Settings(data_dir=data_dir, year=2024)
        settings.ensure_directories()

        assert (data_dir / "output" / "2024").exists()

    @staticmethod
    def test_is_idempotent(tmp_path: Path) -> None:
        """Should not raise if directories already exist."""
        data_dir = tmp_path / "_data"
        settings = Settings(data_dir=data_dir)

        # Call twice
        settings.ensure_directories()
        settings.ensure_directories()

        assert data_dir.exists()


class TestGetSettings:
    """Tests for get_settings function."""

    @staticmethod
    def test_returns_settings_instance() -> None:
        """Should return a Settings instance."""
        # Clear cache first
        get_settings.cache_clear()
        settings = get_settings()
        assert isinstance(settings, Settings)

    @staticmethod
    def test_returns_cached_instance() -> None:
        """Should return same instance on multiple calls."""
        get_settings.cache_clear()
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2

    @staticmethod
    def test_cache_can_be_cleared() -> None:
        """Should return new instance after cache clear."""
        get_settings.cache_clear()
        settings1 = get_settings()
        get_settings.cache_clear()
        settings2 = get_settings()
        # Different instances (but equal values)
        assert settings1 is not settings2


class TestSettingsValidation:
    """Tests for Settings field validation."""

    @staticmethod
    def test_year_minimum_validation() -> None:
        """Should reject year below 2000."""
        with pytest.raises(ValueError):
            Settings(year=1999)

    @staticmethod
    def test_year_maximum_validation() -> None:
        """Should reject year above 2100."""
        with pytest.raises(ValueError):
            Settings(year=2101)

    @staticmethod
    def test_rate_limit_minimum_validation() -> None:
        """Should reject rate limit below 1."""
        with pytest.raises(ValueError):
            Settings(songstats_rate_limit=0)

    @staticmethod
    def test_rate_limit_maximum_validation() -> None:
        """Should reject rate limit above 100."""
        with pytest.raises(ValueError):
            Settings(songstats_rate_limit=101)
