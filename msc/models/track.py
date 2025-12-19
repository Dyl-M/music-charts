"""Track metadata models."""

# Standard library
from typing import Annotated

# Third-party
from pydantic import Field, ConfigDict

# Local
from msc.models.base import MSCBaseModel


class Track(MSCBaseModel):
    """Track metadata from MusicBee library.

    Represents a single track with artist, title, and classification info.
    Immutable after creation (frozen=True) since track metadata shouldn't
    change during processing.

    Attributes:
        title: Track title (cleaned, lowercase).
        artist_list: List of artist names (min 1 required).
        year: Release year (1900-2100).
        genre: Genre tags (default: empty list).
        label: Record labels (default: empty list).
        grouping: MusicBee grouping field (optional).
        search_query: Original search query for Songstats (optional,
            alias="request" for backward compatibility).

    Examples:
        >>> track = Track(
        ...     title="16",
        ...     artist_list=["blasterjaxx", "hardwell", "maddix"],
        ...     year=2024,
        ...     genre=["hard techno"],
        ...     label=["revealed"]
        ... )
        >>> track.primary_artist
        'blasterjaxx'
        >>> track.all_artists_string
        'blasterjaxx, hardwell, maddix'
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    # Core fields
    title: Annotated[
        str,
        Field(description="Track title")
    ]
    artist_list: Annotated[
        list[str],
        Field(min_length=1, description="List of artist names")
    ]
    year: Annotated[
        int,
        Field(ge=1900, le=2100, description="Release year")
    ]

    # Classification
    genre: Annotated[
        list[str],
        Field(default_factory=list, description="Genre tags")
    ]
    label: Annotated[
        list[str],
        Field(default_factory=list, description="Record labels")
    ]
    grouping: Annotated[
        str | None,
        Field(default=None, description="MusicBee grouping field")
    ]

    # Search metadata
    search_query: Annotated[
        str | None,
        Field(
            default=None,
            alias="request",  # Legacy compatibility
            description="Original search query used for Songstats"
        )
    ]

    @property
    def primary_artist(self) -> str:
        """First artist in artist_list.

        Returns:
            Primary artist name.

        Examples:
            >>> track.primary_artist
            'blasterjaxx'
        """
        return self.artist_list[0]

    @property
    def all_artists_string(self) -> str:
        """Comma-separated artist names.

        Returns:
            Artists joined by ", ".

        Examples:
            >>> track.all_artists_string
            'blasterjaxx, hardwell, maddix'
        """
        return ", ".join(self.artist_list)

    def has_genre(self, genre: str) -> bool:
        """Check if track belongs to a genre (case-insensitive).

        Args:
            genre: Genre name to check.

        Returns:
            True if genre is in track's genre list.

        Examples:
            >>> track.has_genre("hard techno")
            True
            >>> track.has_genre("HARD TECHNO")
            True
        """
        return genre.lower() in [g.lower() for g in self.genre]


class SongstatsIdentifiers(MSCBaseModel):
    """Songstats track identifiers.

    Used to link tracks to their Songstats data. Immutable after creation
    since identifiers don't change.

    Attributes:
        songstats_id: Songstats track ID (8-char alphanumeric,
            alias="s_id" for backward compatibility).
        songstats_title: Track title in Songstats database
            (alias="s_title" for backward compatibility).
        isrc: International Standard Recording Code (optional).

    Examples:
        >>> ids = SongstatsIdentifiers(
        ...     songstats_id="qmr6e0bx",
        ...     songstats_title="16"
        ... )
        >>> # Or using legacy aliases:
        >>> ids2 = SongstatsIdentifiers(
        ...     s_id="qmr6e0bx",
        ...     s_title="16"
        ... )
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    songstats_id: Annotated[
        str,
        Field(alias="s_id", description="Songstats track ID")
    ]
    songstats_title: Annotated[
        str,
        Field(alias="s_title", description="Track title in Songstats")
    ]
    isrc: Annotated[
        str | None,
        Field(default=None, description="International Standard Recording Code")
    ]
