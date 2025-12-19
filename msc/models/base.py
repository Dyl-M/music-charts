"""Base model class with shared configuration and utilities."""

# Standard library
import json
from pathlib import Path
from typing import Any, Self

# Third-party
from pydantic import BaseModel, ConfigDict


class MSCBaseModel(BaseModel):
    """Base model for all music-charts data models.

    Provides shared configuration and utility methods for:
    - JSON serialization with None exclusion
    - Alias population for backward compatibility
    - String whitespace stripping
    - Validation on assignment

    All models in the msc.models package inherit from this base class
    to ensure consistent behavior and serialization patterns.

    Examples:
        >>> class MyModel(MSCBaseModel):
        ...     name: str
        ...     count: int | None = None
        >>>
        >>> model = MyModel(name="test", count=5)
        >>> model.model_dump()
        {'name': 'test', 'count': 5}
    """

    model_config = ConfigDict(
        populate_by_name=True,  # Allow both field name and alias
        validate_assignment=True,  # Validate on attribute assignment
        arbitrary_types_allowed=False,  # Strict type checking
        str_strip_whitespace=True,  # Auto-strip strings
    )

    def to_flat_dict(self) -> dict[str, Any]:
        """Convert nested model to flat dict with aliased keys.

        Uses model_dump with by_alias=True to export fields using their
        alias names. Useful for backward compatibility with legacy pandas
        code that expects flat dictionaries.

        Returns:
            Flat dictionary with alias keys where defined.

        Examples:
            >>> model.to_flat_dict()
            {'spotify_streams_total': 1000000, ...}
        """
        return self.model_dump(by_alias=True, exclude_none=True)

    def to_json_file(self, path: Path, indent: int = 2) -> None:
        """Save model to JSON file with UTF-8 encoding.

        Args:
            path: Output file path.
            indent: JSON indentation level (default: 2).

        Examples:
            >>> track.to_json_file(Path("_data/track.json"))
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(
                self.model_dump(exclude_none=True),
                f,
                ensure_ascii=False,
                indent=indent,
            )

    @classmethod
    def from_json_file(cls, path: Path) -> Self:
        """Load model from JSON file with UTF-8 encoding.

        Args:
            path: Input file path.

        Returns:
            Model instance loaded from JSON.

        Examples:
            >>> track = Track.from_json_file(Path("_data/track.json"))
        """
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        return cls(**data)
