"""Power ranking models for track scoring and analysis.

This module provides Pydantic models for track power rankings based on
weighted multi-platform statistics. Rankings are calculated using
MinMaxScaler normalization and weighted category scores.
"""

# Standard library
from typing import Annotated

# Third-party
from pydantic import ConfigDict, Field

# Local
from msc.models.base import MSCBaseModel
from msc.models.track import Track


class CategoryScore(MSCBaseModel):
    """Individual category score contribution.

    Represents the normalized and weighted score for a single stat category
    (e.g., streams, popularity, playlists).

    Attributes:
        category: Category name (streams, popularity, playlists, etc.).
        raw_score: Normalized score 0-100 (power ranking within category).
        weight: Effective weight (data_availability × importance_multiplier).
        weighted_score: raw_score × weight, used for final ranking calculation.

    Examples:
        >>> score = CategoryScore(
        ...     category="streams",
        ...     raw_score=85.0,
        ...     weight=2.4,
        ...     weighted_score=204.0
        ... )
        >>> score.weighted_score
        204.0
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    category: Annotated[
        str,
        Field(description="Category name")
    ]
    raw_score: Annotated[
        float,
        Field(
            ge=0.0,
            le=100.0,
            description="Normalized score (0-100) before weighting"
        )
    ]
    weight: Annotated[
        float,
        Field(
            ge=0.0,
            description="Effective weight (data_availability × importance_multiplier)"
        )
    ]
    weighted_score: Annotated[
        float,
        Field(
            ge=0.0,
            description="raw_score × weight, for final ranking calculation"
        )
    ]


class PowerRanking(MSCBaseModel):
    """Power ranking for a single track.

    Contains the track's total power score, individual category scores,
    and track metadata for ranking analysis.

    Attributes:
        track: Track metadata.
        total_score: Total power score (sum of all weighted category scores).
        rank: Ranking position (1 = highest score).
        category_scores: Breakdown of scores by category.

    Examples:
        >>> ranking = PowerRanking(
        ...     track=Track(
        ...         title="16",
        ...         artist_list=["blasterjaxx", "hardwell", "maddix"],
        ...         year=2024
        ...     ),
        ...     total_score=15.7,
        ...     rank=1,
        ...     category_scores=[
        ...         CategoryScore(
        ...             category="streams",
        ...             raw_score=0.85,
        ...             weight=4,
        ...             weighted_score=3.4
        ...         )
        ...     ]
        ... )
        >>> ranking.total_score
        15.7
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    track: Annotated[
        Track,
        Field(description="Track metadata")
    ]
    total_score: Annotated[
        float,
        Field(
            ge=0.0,
            description="Total power score (sum of weighted category scores)"
        )
    ]
    rank: Annotated[
        int,
        Field(
            ge=1,
            description="Ranking position (1 = highest score)"
        )
    ]
    category_scores: Annotated[
        list[CategoryScore],
        Field(
            min_length=1,
            description="Breakdown of scores by category"
        )
    ]

    @property
    def artist_display(self) -> str:
        """Artist name(s) for display.

        Returns primary artist for single artist, or "Artist1 & Artist2"
        for collaborations.

        Returns:
            Formatted artist string.

        Examples:
            >>> ranking.artist_display
            'blasterjaxx & hardwell & maddix'
        """
        if len(self.track.artist_list) == 1:
            return self.track.primary_artist
        return " & ".join(self.track.artist_list)


class PowerRankingResults(MSCBaseModel):
    """Collection of power rankings for all tracks.

    Contains ranked results for all analyzed tracks, sorted by total_score
    (highest first).

    Attributes:
        rankings: List of power rankings sorted by score (descending).
        year: Year of analysis.

    Examples:
        >>> results = PowerRankingResults(
        ...     rankings=[
        ...         PowerRanking(track=..., total_score=15.7, rank=1, ...),
        ...         PowerRanking(track=..., total_score=12.3, rank=2, ...)
        ...     ],
        ...     year=2024
        ... )
        >>> results.total_tracks
        2
    """

    model_config = ConfigDict(frozen=True)  # Immutable

    rankings: Annotated[
        list[PowerRanking],
        Field(
            description="List of power rankings sorted by score (descending)"
        )
    ]
    year: Annotated[
        int,
        Field(
            ge=1900,
            le=2100,
            description="Year of analysis"
        )
    ]

    @property
    def total_tracks(self) -> int:
        """Total number of ranked tracks.

        Returns:
            Number of tracks in rankings.

        Examples:
            >>> results.total_tracks
            2
        """
        return len(self.rankings)

    def get_by_rank(self, rank: int) -> PowerRanking | None:
        """Get ranking by position.

        Args:
            rank: Ranking position (1-based).

        Returns:
            PowerRanking at given position, or None if not found.

        Examples:
            >>> top_track = results.get_by_rank(1)
            >>> top_track.total_score
            15.7
        """
        for ranking in self.rankings:
            if ranking.rank == rank:
                return ranking
        return None

    def get_by_artist(self, artist: str) -> list[PowerRanking]:
        """Get all rankings for an artist.

        Args:
            artist: Artist name (case-insensitive).

        Returns:
            List of rankings where artist appears in artist_list.

        Examples:
            >>> hardwell_tracks = results.get_by_artist("hardwell")
            >>> len(hardwell_tracks)
            3
        """
        artist_lower = artist.lower()
        return [
            ranking
            for ranking in self.rankings
            if artist_lower in [a.lower() for a in ranking.track.artist_list]
        ]
