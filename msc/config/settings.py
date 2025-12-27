"""Runtime configuration management using Pydantic settings."""

# Standard library
import json
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any

# Third-party
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# Project root directory (msc/config/settings.py -> msc/config/ -> msc/ -> project_root/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_prefix="MSC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Paths
    musicbee_library: Annotated[
        Path,
        Field(description="Path to MusicBee iTunes Music Library.xml"),
    ] = Path("E:/Musique/MusicBee/iTunes Music Library.xml")

    data_dir: Annotated[
        Path,
        Field(description="Directory for data artifacts"),
    ] = PROJECT_ROOT / "_data"

    tokens_dir: Annotated[
        Path,
        Field(description="Directory for credential files"),
    ] = PROJECT_ROOT / "_tokens"

    config_dir: Annotated[
        Path,
        Field(description="Directory for configuration files"),
    ] = PROJECT_ROOT / "_config"

    # Filters
    year: Annotated[
        int,
        Field(description="Target year for analysis", ge=2000, le=2100),
    ] = 2025

    playlist_id: Annotated[
        str,
        Field(description="MusicBee playlist ID for DJ tracks"),
    ] = "4361"

    # API Configuration
    songstats_rate_limit: Annotated[
        int,
        Field(description="Maximum Songstats API requests per second", ge=1, le=100),
    ] = 10

    youtube_rate_limit: Annotated[
        int,
        Field(description="Maximum YouTube API requests per second", ge=1, le=100),
    ] = 10

    youtube_quota_daily: Annotated[
        int,
        Field(description="Daily YouTube API quota limit", ge=0),
    ] = 10000

    youtube_oauth_path: Annotated[
        Path,
        Field(description="Path to YouTube OAuth 2.0 client secrets"),
    ] = PROJECT_ROOT / "_tokens" / "oauth.json"

    youtube_credentials_path: Annotated[
        Path,
        Field(description="Path to cached YouTube credentials"),
    ] = PROJECT_ROOT / "_tokens" / "credentials.json"

    # API Keys (loaded from files or environment)
    songstats_api_key: Annotated[
        str | None,
        Field(description="Songstats API key (or set MSC_SONGSTATS_API_KEY)"),
    ] = None

    @property
    def input_dir(self) -> Path:
        """Directory for input data files."""
        return self.data_dir / "input"

    @property
    def output_dir(self) -> Path:
        """Directory for output data files."""
        return self.data_dir / "output"

    @property
    def cache_dir(self) -> Path:
        """Directory for cached API responses."""
        return self.data_dir / "cache"

    @property
    def year_output_dir(self) -> Path:
        """Year-specific output directory."""
        return self.output_dir / str(self.year)

    @property
    def test_library_path(self) -> Path:
        """Path to test library fixture for test mode."""
        return PROJECT_ROOT / "_tests" / "fixtures" / "test_library.xml"

    def get_songstats_key(self) -> str:
        """Load Songstats API key from file or environment."""
        if self.songstats_api_key:
            return self.songstats_api_key

        key_file = self.tokens_dir / "songstats_key.txt"
        if key_file.exists():
            return key_file.read_text(encoding="utf-8").strip()

        raise ValueError(
            "Songstats API key not found. Set MSC_SONGSTATS_API_KEY or create tokens/songstats_key.txt"
        )

    def get_youtube_oauth(self) -> dict[str, Any]:
        """Load YouTube OAuth 2.0 client secrets from file.

        Returns:
            dict[str, Any]: OAuth client configuration.

        Raises:
            ValueError: If OAuth file not found.
        """
        if not self.youtube_oauth_path.exists():
            raise ValueError(f"YouTube OAuth file not found: {self.youtube_oauth_path}")

        with open(self.youtube_oauth_path, encoding="utf-8") as f:
            return json.load(f)

    def get_youtube_credentials(self) -> dict[str, Any] | None:
        """Load cached YouTube credentials if available.

        Returns:
            dict[str, Any] | None: Cached credentials or None if not found.
        """
        if not self.youtube_credentials_path.exists():
            return None

        with open(self.youtube_credentials_path, encoding="utf-8") as f:
            return json.load(f)

    def save_youtube_credentials(self, credentials: dict[str, Any]) -> None:
        """Save YouTube credentials to cache file.

        Args:
            credentials: Credentials dictionary to save.
        """
        with open(self.youtube_credentials_path, "w", encoding="utf-8") as f:
            json.dump(credentials, f, ensure_ascii=False, indent=4)

    def ensure_directories(self) -> None:
        """Create all required directories if they don't exist."""
        for directory in [
            self.data_dir,
            self.input_dir,
            self.output_dir,
            self.cache_dir,
            self.year_output_dir,
            self.tokens_dir,
            self.config_dir,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get or create the global settings instance (singleton pattern)."""
    return Settings()
