"""Runtime configuration management using Pydantic settings."""

# Standard library
from pathlib import Path
from typing import Annotated

# Third-party
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    ] = Path("_data")

    tokens_dir: Annotated[
        Path,
        Field(description="Directory for credential files"),
    ] = Path("_tokens")

    config_dir: Annotated[
        Path,
        Field(description="Directory for configuration files"),
    ] = Path("_config")

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

    youtube_quota_daily: Annotated[
        int,
        Field(description="Daily YouTube API quota limit", ge=0),
    ] = 10000

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


def get_settings() -> Settings:
    """Get or create the global settings instance (singleton pattern)."""
    if not hasattr(get_settings, "_instance"):
        get_settings._instance = Settings()  # type: ignore[attr-defined]
    return get_settings._instance  # type: ignore[attr-defined, return-value] # TODO: check this?
