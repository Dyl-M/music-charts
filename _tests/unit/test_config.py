"""Unit tests for configuration module."""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.config.constants import (
    CATEGORY_WEIGHTS,
    Platform,
    StatCategory,
    WeightLevel,
)

from msc.config.settings import Settings, get_settings


class TestPlatform:
    """Tests for the Platform enum."""

    @staticmethod
    def test_all_platforms_defined() -> None:
        """Should have all expected platforms."""
        expected = {
            "SPOTIFY", "APPLE_MUSIC", "YOUTUBE", "DEEZER",
            "TIKTOK", "BEATPORT", "TIDAL", "SOUNDCLOUD",
            "AMAZON", "TRACKLISTS"
        }
        actual = {p.name for p in Platform}
        assert actual == expected

    @staticmethod
    def test_songstats_sources_returns_tuple() -> None:
        """Should return tuple of source strings."""
        sources = Platform.songstats_sources()
        assert isinstance(sources, tuple)
        assert len(sources) == 10

    @staticmethod
    def test_songstats_sources_lowercase() -> None:
        """All sources should be lowercase."""
        for source in Platform.songstats_sources():
            assert source == source.lower()


class TestStatCategory:
    """Tests for the StatCategory enum."""

    @staticmethod
    def test_all_categories_defined() -> None:
        """Should have all expected categories."""
        expected = {
            "CHARTS", "ENGAGEMENT", "PLAYLISTS", "POPULARITY",
            "PROFESSIONAL", "REACH", "SHORTS", "STREAMS"
        }
        actual = {c.name for c in StatCategory}
        assert actual == expected


class TestWeightLevel:
    """Tests for the WeightLevel enum."""

    @staticmethod
    def test_weight_values() -> None:
        """Weight levels should have correct values."""
        assert WeightLevel.NEGLIGIBLE == 1
        assert WeightLevel.LOW == 2
        assert WeightLevel.HIGH == 4


class TestCategoryWeights:
    """Tests for category weight assignments."""

    @staticmethod
    def test_all_categories_have_weights() -> None:
        """Every category should have a weight assigned."""
        for category in StatCategory:
            assert category in CATEGORY_WEIGHTS

    @staticmethod
    def test_negligible_weights() -> None:
        """Charts, Engagement, and Shorts should be negligible."""
        assert CATEGORY_WEIGHTS[StatCategory.CHARTS] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.ENGAGEMENT] == WeightLevel.NEGLIGIBLE
        assert CATEGORY_WEIGHTS[StatCategory.SHORTS] == WeightLevel.NEGLIGIBLE

    @staticmethod
    def test_low_weights() -> None:
        """Reach, Playlists, and Professional should be low."""
        assert CATEGORY_WEIGHTS[StatCategory.REACH] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PLAYLISTS] == WeightLevel.LOW
        assert CATEGORY_WEIGHTS[StatCategory.PROFESSIONAL] == WeightLevel.LOW

    @staticmethod
    def test_high_weights() -> None:
        """Popularity and Streams should be high."""
        assert CATEGORY_WEIGHTS[StatCategory.POPULARITY] == WeightLevel.HIGH
        assert CATEGORY_WEIGHTS[StatCategory.STREAMS] == WeightLevel.HIGH


class TestSettings:
    """Tests for the Settings class."""

    @staticmethod
    def test_input_dir_property() -> None:
        """Should construct input directory path."""
        settings = Settings()
        assert settings.input_dir == settings.data_dir / "input"

    @staticmethod
    def test_output_dir_property() -> None:
        """Should construct output directory path."""
        settings = Settings()
        assert settings.output_dir == settings.data_dir / "output"

    @staticmethod
    def test_cache_dir_property() -> None:
        """Should construct cache directory path."""
        settings = Settings()
        assert settings.cache_dir == settings.data_dir / "cache"

    @staticmethod
    def test_year_output_dir_property() -> None:
        """Should construct year-specific output directory."""
        settings = Settings(year=2024)
        assert settings.year_output_dir == settings.output_dir / "2024"

    @staticmethod
    def test_get_songstats_key_from_env() -> None:
        """Should return API key from environment variable."""
        settings = Settings(songstats_api_key="test_key_from_env")
        assert settings.get_songstats_key() == "test_key_from_env"

    @staticmethod
    def test_get_songstats_key_from_file(tmp_path: Path) -> None:
        """Should load API key from file."""
        tokens_dir = tmp_path / "tokens"
        tokens_dir.mkdir()
        key_file = tokens_dir / "songstats_key.txt"
        key_file.write_text("test_key_from_file\n", encoding="utf-8")

        settings = Settings(tokens_dir=tokens_dir)
        assert settings.get_songstats_key() == "test_key_from_file"

    @staticmethod
    def test_get_songstats_key_missing_raises_error() -> None:
        """Should raise ValueError when API key not found."""
        settings = Settings(tokens_dir=Path("/nonexistent"))
        with pytest.raises(ValueError, match="Songstats API key not found"):
            settings.get_songstats_key()

    @staticmethod
    def test_ensure_directories_creates_all(tmp_path: Path) -> None:
        """Should create all required directories."""
        base = tmp_path / "test_dirs"
        settings = Settings(
            data_dir=base / "data",
            tokens_dir=base / "tokens",
            config_dir=base / "config",
            year=2024,
        )

        settings.ensure_directories()

        assert settings.data_dir.exists()
        assert settings.input_dir.exists()
        assert settings.output_dir.exists()
        assert settings.cache_dir.exists()
        assert settings.year_output_dir.exists()
        assert settings.tokens_dir.exists()
        assert settings.config_dir.exists()

    @staticmethod
    def test_get_youtube_oauth_success(tmp_path: Path) -> None:
        """Should load YouTube OAuth configuration from file."""
        tokens_dir = tmp_path / "tokens"
        tokens_dir.mkdir()
        oauth_file = tokens_dir / "oauth.json"

        oauth_data = {
            "installed": {
                "client_id": "test_client_id",
                "client_secret": "test_secret",
                "redirect_uris": ["http://localhost:8080/"]
            }
        }
        
        oauth_file.write_text(
            '{"installed": {"client_id": "test_client_id", "client_secret": "test_secret", "redirect_uris": '
            '["http://localhost:8080/"]}}',
            encoding="utf-8"
        )

        settings = Settings(youtube_oauth_path=oauth_file)
        result = settings.get_youtube_oauth()

        assert result == oauth_data
        assert result["installed"]["client_id"] == "test_client_id"

    @staticmethod
    def test_get_youtube_oauth_file_not_found() -> None:
        """Should raise ValueError when OAuth file not found."""
        settings = Settings(youtube_oauth_path=Path("/nonexistent/oauth.json"))

        with pytest.raises(ValueError, match="YouTube OAuth file not found"):
            settings.get_youtube_oauth()

    @staticmethod
    def test_get_youtube_credentials_success(tmp_path: Path) -> None:
        """Should load cached YouTube credentials from file."""
        tokens_dir = tmp_path / "tokens"
        tokens_dir.mkdir()
        creds_file = tokens_dir / "credentials.json"

        creds_data = {
            "token": "test_token",
            "refresh_token": "test_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_secret"
        }

        creds_file.write_text(
            '{"token": "test_token", "refresh_token": "test_refresh", "token_uri": '
            '"https://oauth2.googleapis.com/token", "client_id": "test_client_id", "client_secret": "test_secret"}',
            encoding="utf-8"
        )

        settings = Settings(youtube_credentials_path=creds_file)
        result = settings.get_youtube_credentials()

        assert result == creds_data
        assert result["token"] == "test_token"

    @staticmethod
    def test_get_youtube_credentials_file_not_found() -> None:
        """Should return None when credentials file not found."""
        settings = Settings(youtube_credentials_path=Path("/nonexistent/credentials.json"))

        result = settings.get_youtube_credentials()
        assert result is None

    @staticmethod
    def test_save_youtube_credentials(tmp_path: Path) -> None:
        """Should save YouTube credentials to file with correct formatting."""
        tokens_dir = tmp_path / "tokens"
        tokens_dir.mkdir()
        creds_file = tokens_dir / "credentials.json"

        settings = Settings(youtube_credentials_path=creds_file)

        creds_data = {
            "token": "test_token",
            "refresh_token": "test_refresh",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "test_client_id",
            "client_secret": "test_secret"
        }

        settings.save_youtube_credentials(creds_data)

        # Verify file was created
        assert creds_file.exists()

        # Verify content is correct
        saved_content = creds_file.read_text(encoding="utf-8")
        import json
        saved_data = json.loads(saved_content)
        assert saved_data == creds_data

        # Verify formatting (indent=4)
        assert "    " in saved_content  # Check for 4-space indentation


class TestGetSettings:
    """Tests for the get_settings function."""

    @staticmethod
    def test_get_settings_returns_settings_instance() -> None:
        """Should return a Settings instance."""
        # Clear the lru_cache
        get_settings.cache_clear()

        settings = get_settings()
        assert isinstance(settings, Settings)

    @staticmethod
    def test_get_settings_returns_same_instance() -> None:
        """Should return the same instance on multiple calls."""
        # Clear the lru_cache
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
