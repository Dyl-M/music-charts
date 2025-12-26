"""Unit tests for data validation utilities.

Tests file validation and auto-detection functionality.
"""

# Standard library
import json
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Local
from msc.commands.validators import ValidationResult, FileValidator


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    @staticmethod
    def test_creates_valid_result() -> None:
        """Should create valid result."""
        result = ValidationResult(
            is_valid=True,
            model_name="Track",
            error_count=0,
            errors=[],
            file_path=Path("test.json"),
        )
        assert result.is_valid is True
        assert result.model_name == "Track"
        assert result.error_count == 0

    @staticmethod
    def test_creates_invalid_result() -> None:
        """Should create invalid result."""
        errors = [{"loc": ["title"], "msg": "required", "type": "missing"}]
        result = ValidationResult(
            is_valid=False,
            model_name="Track",
            error_count=1,
            errors=errors,
            file_path=Path("test.json"),
        )
        assert result.is_valid is False
        assert result.error_count == 1
        assert len(result.errors) == 1

    @staticmethod
    def test_is_frozen() -> None:
        """Should be immutable."""
        result = ValidationResult(
            is_valid=True,
            model_name="Track",
            error_count=0,
            errors=[],
            file_path=Path("test.json"),
        )
        with pytest.raises(AttributeError):
            # noinspection PyDataclass
            result.is_valid = False


class TestFileValidatorSupportedModels:
    """Tests for FileValidator.SUPPORTED_MODELS registry."""

    @staticmethod
    def test_includes_track() -> None:
        """Should include Track model."""
        assert "Track" in FileValidator.SUPPORTED_MODELS

    @staticmethod
    def test_includes_track_with_stats() -> None:
        """Should include TrackWithStats model."""
        assert "TrackWithStats" in FileValidator.SUPPORTED_MODELS

    @staticmethod
    def test_includes_power_ranking_results() -> None:
        """Should include PowerRankingResults model."""
        assert "PowerRankingResults" in FileValidator.SUPPORTED_MODELS

    @staticmethod
    def test_track_expects_list() -> None:
        """Track should expect list format."""
        _, expects_list = FileValidator.SUPPORTED_MODELS["Track"]
        assert expects_list is True

    @staticmethod
    def test_power_ranking_expects_single() -> None:
        """PowerRankingResults should expect single object."""
        _, expects_list = FileValidator.SUPPORTED_MODELS["PowerRankingResults"]
        assert expects_list is False


class TestFileValidatorDetectFileType:
    """Tests for FileValidator.detect_file_type method."""

    @staticmethod
    def test_detects_power_ranking_results() -> None:
        """Should detect PowerRankingResults from structure."""
        data = {"rankings": [], "year": 2024}
        result = FileValidator.detect_file_type(data)
        assert result == "PowerRankingResults"

    @staticmethod
    def test_detects_track_with_stats_dict() -> None:
        """Should detect TrackWithStats from dict with platform_stats."""
        data = {"title": "Test", "platform_stats": {}}
        result = FileValidator.detect_file_type(data)
        assert result == "TrackWithStats"

    @staticmethod
    def test_detects_track_with_stats_list() -> None:
        """Should detect TrackWithStats from list with platform_stats."""
        data = [{"title": "Test", "platform_stats": {}}]
        result = FileValidator.detect_file_type(data)
        assert result == "TrackWithStats"

    @staticmethod
    def test_detects_track_dict() -> None:
        """Should detect Track from dict with title and artist_list."""
        data = {"title": "Test", "artist_list": ["Artist"]}
        result = FileValidator.detect_file_type(data)
        assert result == "Track"

    @staticmethod
    def test_detects_track_list() -> None:
        """Should detect Track from list with title."""
        data = [{"title": "Test", "artist_list": ["Artist"]}]
        result = FileValidator.detect_file_type(data)
        assert result == "Track"

    @staticmethod
    def test_returns_unknown_for_unrecognized() -> None:
        """Should return Unknown for unrecognized structure."""
        data = {"random": "data", "without": "markers"}
        result = FileValidator.detect_file_type(data)
        assert result == "Unknown"

    @staticmethod
    def test_returns_unknown_for_empty_dict() -> None:
        """Should return Unknown for empty dict."""
        data = {}
        result = FileValidator.detect_file_type(data)
        assert result == "Unknown"

    @staticmethod
    def test_returns_unknown_for_empty_list() -> None:
        """Should return Unknown for empty list."""
        data = []
        result = FileValidator.detect_file_type(data)
        assert result == "Unknown"

    @staticmethod
    def test_prioritizes_power_ranking_over_track() -> None:
        """Should detect PowerRankingResults even with title field."""
        data = {"rankings": [], "year": 2024, "title": "Test"}
        result = FileValidator.detect_file_type(data)
        assert result == "PowerRankingResults"

    @staticmethod
    def test_prioritizes_track_with_stats_over_track() -> None:
        """Should detect TrackWithStats when platform_stats present."""
        data = {"title": "Test", "artist_list": ["A"], "platform_stats": {}}
        result = FileValidator.detect_file_type(data)
        assert result == "TrackWithStats"


class TestFileValidatorValidateFile:
    """Tests for FileValidator.validate_file method."""

    @staticmethod
    def test_validates_valid_track_file(tmp_path: Path) -> None:
        """Should validate valid Track JSON file."""
        file_path = tmp_path / "tracks.json"
        data = [{"title": "Test Track", "artist_list": ["Artist"], "year": 2024}]
        file_path.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(file_path, base_dir=tmp_path)

        assert result.is_valid is True
        assert result.model_name == "Track"

    @staticmethod
    def test_validates_invalid_track_file(tmp_path: Path) -> None:
        """Should detect invalid Track file."""
        file_path = tmp_path / "tracks.json"
        data = [{"title": "Test", "year": "not an int"}]  # Missing artist_list
        file_path.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(file_path, base_dir=tmp_path)

        assert result.is_valid is False
        assert result.error_count > 0

    @staticmethod
    def test_raises_for_nonexistent_file(tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing file."""
        validator = FileValidator()
        with pytest.raises(FileNotFoundError):
            validator.validate_file(tmp_path / "missing.json", base_dir=tmp_path)

    @staticmethod
    def test_raises_for_invalid_json(tmp_path: Path) -> None:
        """Should raise JSONDecodeError for invalid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not json", encoding="utf-8")

        validator = FileValidator()
        with pytest.raises(json.JSONDecodeError):
            validator.validate_file(file_path, base_dir=tmp_path)

    @staticmethod
    def test_returns_unknown_for_undetectable(tmp_path: Path) -> None:
        """Should return Unknown model for undetectable structure."""
        file_path = tmp_path / "random.json"
        data = {"random": "data"}
        file_path.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(file_path, base_dir=tmp_path)

        assert result.is_valid is False
        assert result.model_name == "Unknown"
        assert "detection_error" in result.errors[0]["type"]

    @staticmethod
    def test_uses_default_base_dir(tmp_path: Path) -> None:
        """Should use settings base dir when not provided."""
        file_path = tmp_path / "tracks.json"
        data = [{"title": "Test", "artist_list": ["A"], "year": 2024}]
        file_path.write_text(json.dumps(data), encoding="utf-8")

        with patch("msc.commands.validators.get_settings") as mock_settings:
            mock_settings.return_value.data_dir = tmp_path

            validator = FileValidator()
            result = validator.validate_file(file_path)

            # Should work without explicit base_dir
            assert result.model_name in ["Track", "Unknown"]


class TestFileValidatorValidateData:
    """Tests for FileValidator.validate_data method."""

    @staticmethod
    def test_validates_track_list() -> None:
        """Should validate list of Track data."""
        data = [{"title": "Test", "artist_list": ["Artist"], "year": 2024}]

        validator = FileValidator()
        result = validator.validate_data(data, "Track")

        assert result.is_valid is True
        assert result.model_name == "Track"

    @staticmethod
    def test_rejects_non_list_for_track() -> None:
        """Should reject non-list for Track model."""
        data = {"title": "Test", "artist_list": ["Artist"], "year": 2024}

        validator = FileValidator()
        result = validator.validate_data(data, "Track")

        assert result.is_valid is False
        assert "Expected list" in result.errors[0]["msg"]

    @staticmethod
    def test_validates_power_ranking_single() -> None:
        """Should validate single PowerRankingResults object."""
        data = {"rankings": [], "year": 2024}

        validator = FileValidator()
        result = validator.validate_data(data, "PowerRankingResults")

        assert result.is_valid is True
        assert result.model_name == "PowerRankingResults"

    @staticmethod
    def test_rejects_unsupported_model() -> None:
        """Should reject unsupported model type."""
        validator = FileValidator()
        result = validator.validate_data({}, "UnsupportedModel")

        assert result.is_valid is False
        assert "Unsupported model type" in result.errors[0]["msg"]

    @staticmethod
    def test_collects_validation_errors_per_item() -> None:
        """Should collect errors for each invalid item in list."""
        data = [
            {"title": "Valid", "artist_list": ["A"], "year": 2024},
            {"title": "Invalid"},  # Missing artist_list
        ]

        validator = FileValidator()
        result = validator.validate_data(data, "Track")

        assert result.is_valid is False
        # Should have errors for item_1
        error_locs = [str(e["loc"]) for e in result.errors]
        assert any("item_1" in loc for loc in error_locs)

    @staticmethod
    def test_returns_empty_file_path_when_not_provided() -> None:
        """Should use empty path when file_path not provided."""
        validator = FileValidator()
        result = validator.validate_data([], "Track")

        assert result.file_path == Path("")


class TestFileValidatorPathSecurity:
    """Tests for path security in file validation."""

    @staticmethod
    def test_rejects_path_traversal(tmp_path: Path) -> None:
        """Should reject path traversal attempts."""
        # Create file outside base dir
        outside_dir = tmp_path.parent / "outside"
        outside_dir.mkdir(exist_ok=True)
        outside_file = outside_dir / "secret.json"
        outside_file.write_text("[]", encoding="utf-8")

        validator = FileValidator()

        # Try to access file outside base_dir via traversal
        traversal_path = tmp_path / ".." / "outside" / "secret.json"
        with pytest.raises(ValueError, match="outside"):
            validator.validate_file(traversal_path, base_dir=tmp_path)
