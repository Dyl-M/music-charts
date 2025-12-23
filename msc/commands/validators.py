"""Data validation utilities for CLI commands.

Provides file validation against Pydantic models with auto-detection
of file types and structured error reporting.
"""

# Standard library
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

# Third-party
from pydantic import ValidationError

# Local
from msc.config.settings import get_settings
from msc.models.ranking import PowerRankingResults
from msc.models.stats import TrackWithStats
from msc.models.track import Track
from msc.utils.path_utils import validate_path_within_base


@dataclass(frozen=True)
class ValidationResult:
    """Immutable validation result.

    Attributes:
        is_valid: Whether validation passed
        model_name: Name of model that validated successfully
        error_count: Number of validation errors found
        errors: List of structured error details
        file_path: Path to validated file
    """

    is_valid: bool
    model_name: str
    error_count: int
    errors: list[dict[str, Any]]
    file_path: Path


class FileValidator:
    """Validator for JSON data files against Pydantic models.

    Automatically detects file type from structure and validates
    against the appropriate model (Track, TrackWithStats, PowerRankingResults).
    """

    # Model registry: type name -> (model class, expects list)
    SUPPORTED_MODELS: dict[str, tuple[type, bool]] = {
        "Track": (Track, True),  # List of tracks
        "TrackWithStats": (TrackWithStats, True),  # List of enriched tracks
        "PowerRankingResults": (PowerRankingResults, False),  # Single object
    }

    # Detection rules: (model_name, detection_function)
    # Rules are checked in order, first match wins
    _DETECTION_RULES: list[tuple[str, Callable[[dict | list], bool]]] = []

    @classmethod
    def _register_detection_rules(cls) -> None:
        """Register detection rules for all model types."""
        if cls._DETECTION_RULES:
            return  # Already registered

        # Rule: PowerRankingResults (single dict with 'rankings' and 'year')
        cls._DETECTION_RULES.append(
            ("PowerRankingResults", lambda d: isinstance(d, dict) and "rankings" in d and "year" in d)
        )

        # Rule: TrackWithStats (dict or list with 'platform_stats')
        cls._DETECTION_RULES.append(
            ("TrackWithStats", lambda d: isinstance(d, dict) and "platform_stats" in d)
        )
        cls._DETECTION_RULES.append(
            ("TrackWithStats",
             lambda d: isinstance(d, list) and d and isinstance(d[0], dict) and "platform_stats" in d[0])
        )

        # Rule: Track (dict or list with 'title' and 'artist_list')
        cls._DETECTION_RULES.append(
            ("Track", lambda d: isinstance(d, dict) and "title" in d and "artist_list" in d)
        )
        cls._DETECTION_RULES.append(
            ("Track", lambda d: isinstance(d, list) and d and isinstance(d[0], dict) and "title" in d[0])
        )

    @classmethod
    def detect_file_type(cls, data: dict | list) -> str:
        """Auto-detect data type from JSON structure.

        Args:
            data: Loaded JSON data (dict or list)

        Returns:
            Detected model name ('Track', 'TrackWithStats', 'PowerRankingResults')
            or 'Unknown' if detection fails

        Detection Logic:
            - PowerRankingResults: Has 'rankings' key and 'year' key
            - TrackWithStats: List/dict with 'platform_stats' key
            - Track: List/dict with 'title' and 'artist_list' keys
        """
        # Ensure rules are registered
        cls._register_detection_rules()

        # Check each rule in order
        for model_name, detection_func in cls._DETECTION_RULES:
            try:
                if detection_func(data):
                    return model_name

            except (KeyError, IndexError, TypeError):
                # Rule check failed, continue to next rule
                continue

        return "Unknown"

    def validate_file(
            self,
            file_path: Path,
            base_dir: Path | None = None,
    ) -> ValidationResult:
        """Validate JSON file against appropriate model.

        Args:
            file_path: Path to JSON file
            base_dir: Optional base directory for path validation.
                     If None, uses project root for security.

        Returns:
            ValidationResult with validation status and errors

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
            ValueError: If file path is outside allowed directory
        """
        # Validate file path is within allowed directory for security
        if base_dir is None:
            # Use project root as default for CLI usage
            settings = get_settings()
            base_dir = settings.data_dir.parent

        validated_path = validate_path_within_base(
            Path(file_path),
            base_dir,
            "validation"
        )

        # Load JSON
        with open(validated_path, encoding="utf-8") as f:
            data = json.load(f)

        # Auto-detect file type
        model_name = self.detect_file_type(data)

        if model_name == "Unknown":
            return ValidationResult(
                is_valid=False,
                model_name="Unknown",
                error_count=1,
                errors=[
                    {
                        "loc": ["root"],
                        "msg": "Unable to detect file type from structure",
                        "type": "detection_error",
                    }
                ],
                file_path=file_path,
            )

        # Validate against detected model
        return self.validate_data(data, model_name, file_path)

    def validate_data(
            self,
            data: dict | list,
            model_type: str,
            file_path: Path | None = None,
    ) -> ValidationResult:
        """Validate raw data against specific model type.

        Args:
            data: Data to validate (dict or list)
            model_type: Model name ('Track', 'TrackWithStats', 'PowerRankingResults')
            file_path: Optional path for error reporting

        Returns:
            ValidationResult with validation status and errors
        """
        if model_type not in self.SUPPORTED_MODELS:
            return ValidationResult(
                is_valid=False,
                model_name=model_type,
                error_count=1,
                errors=[
                    {
                        "loc": ["model_type"],
                        "msg": f"Unsupported model type: {model_type}",
                        "type": "unsupported_model",
                    }
                ],
                file_path=file_path or Path(""),
            )

        model_class, expects_list = self.SUPPORTED_MODELS[model_type]
        errors = []

        try:
            if expects_list:
                # Validate list of objects
                if not isinstance(data, list):
                    errors.append(
                        {
                            "loc": ["root"],
                            "msg": f"Expected list of {model_type} objects, got {type(data).__name__}",
                            "type": "type_error",
                        }
                    )

                else:
                    # Validate each item
                    for i, item in enumerate(data):
                        try:
                            model_class.model_validate(item)

                        except ValidationError as e:
                            # Add validation errors for this item
                            for error in e.errors():
                                error_dict = {
                                    "loc": [f"item_{i}", *error["loc"]],
                                    "msg": error["msg"],
                                    "type": error["type"],
                                }
                                errors.append(error_dict)

            else:
                # Validate single object
                model_class.model_validate(data)

        except ValidationError as e:
            # Add validation errors
            errors.extend(e.errors())

        # Build result
        return ValidationResult(
            is_valid=len(errors) == 0,
            model_name=model_type,
            error_count=len(errors),
            errors=errors,
            file_path=file_path or Path(""),
        )
