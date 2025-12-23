"""Unit tests for CLI validators module."""

# Standard library
import json
from pathlib import Path

# Third-party
import pytest

# Local
from msc.commands.validators import FileValidator, ValidationResult
from msc.models.track import Track


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    @staticmethod
    def test_create_validation_result() -> None:
        """Should create immutable validation result."""
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
        assert result.errors == []

    @staticmethod
    def test_validation_result_frozen() -> None:
        """Should be immutable (frozen dataclass)."""
        result = ValidationResult(
            is_valid=True,
            model_name="Track",
            error_count=0,
            errors=[],
            file_path=Path("test.json"),
        )

        with pytest.raises(AttributeError):
            setattr(result, "is_valid", False)


class TestFileValidatorDetection:
    """Tests for file type detection."""

    @staticmethod
    def test_detect_power_ranking_results() -> None:
        """Should detect PowerRankingResults from dict structure."""
        data = {
            "year": 2025,
            "rankings": [],
            "total_tracks": 0,
        }

        result = FileValidator.detect_file_type(data)

        assert result == "PowerRankingResults"

    @staticmethod
    def test_detect_track_with_stats_dict() -> None:
        """Should detect TrackWithStats from dict with platform_stats."""
        data = {
            "title": "Test",
            "artist_list": ["Artist"],
            "platform_stats": {"spotify": None},
        }

        result = FileValidator.detect_file_type(data)

        assert result == "TrackWithStats"

    @staticmethod
    def test_detect_track_with_stats_list() -> None:
        """Should detect TrackWithStats from list."""
        data = [
            {
                "title": "Test",
                "artist_list": ["Artist"],
                "platform_stats": {"spotify": None},
            }
        ]

        result = FileValidator.detect_file_type(data)

        assert result == "TrackWithStats"

    @staticmethod
    def test_detect_track_dict() -> None:
        """Should detect Track from dict."""
        data = {
            "title": "Test",
            "artist_list": ["Artist"],
            "year": 2025,
        }

        result = FileValidator.detect_file_type(data)

        assert result == "Track"

    @staticmethod
    def test_detect_track_list() -> None:
        """Should detect Track from list."""
        data = [
            {
                "title": "Test",
                "artist_list": ["Artist"],
                "year": 2025,
            }
        ]

        result = FileValidator.detect_file_type(data)

        assert result == "Track"

    @staticmethod
    def test_detect_unknown_structure() -> None:
        """Should return Unknown for unrecognized structure."""
        data = {"random": "data"}

        result = FileValidator.detect_file_type(data)

        assert result == "Unknown"

    @staticmethod
    def test_detect_empty_list() -> None:
        """Should return Unknown for empty list."""
        result = FileValidator.detect_file_type([])

        assert result == "Unknown"


class TestFileValidatorValidateFile:
    """Tests for file validation."""

    @staticmethod
    def test_validate_valid_track_file(tmp_path: Path) -> None:
        """Should validate valid Track JSON file."""
        test_file = tmp_path / "tracks.json"
        data = [
            Track(
                title="Test Song",
                artist_list=["Artist"],
                year=2025,
            ).model_dump()
        ]
        test_file.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(test_file)

        assert result.is_valid is True
        assert result.model_name == "Track"
        assert result.error_count == 0

    @staticmethod
    def test_validate_invalid_track_file(tmp_path: Path) -> None:
        """Should detect validation errors in Track file."""
        test_file = tmp_path / "tracks.json"
        # Missing required field 'year'
        data = [{"title": "Test Song", "artist_list": ["Artist"]}]
        test_file.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(test_file)

        assert result.is_valid is False
        assert result.model_name == "Track"
        assert result.error_count > 0

    @staticmethod
    def test_validate_unknown_file_type(tmp_path: Path) -> None:
        """Should handle unknown file types."""
        test_file = tmp_path / "unknown.json"
        data = {"random": "data"}
        test_file.write_text(json.dumps(data), encoding="utf-8")

        validator = FileValidator()
        result = validator.validate_file(test_file)

        assert result.is_valid is False
        assert result.model_name == "Unknown"
        assert result.error_count == 1

    @staticmethod
    def test_validate_file_not_found() -> None:
        """Should raise FileNotFoundError for missing file."""
        validator = FileValidator()

        with pytest.raises(FileNotFoundError):
            validator.validate_file(Path("/nonexistent/file.json"))

    @staticmethod
    def test_validate_invalid_json(tmp_path: Path) -> None:
        """Should raise JSONDecodeError for invalid JSON."""
        test_file = tmp_path / "invalid.json"
        test_file.write_text("not valid json", encoding="utf-8")

        validator = FileValidator()

        with pytest.raises(json.JSONDecodeError):
            validator.validate_file(test_file)


class TestFileValidatorValidateData:
    """Tests for data validation."""

    @staticmethod
    def test_validate_track_list() -> None:
        """Should validate list of Track objects."""
        data = [
            Track(title="Test", artist_list=["Artist"], year=2025).model_dump()
        ]

        validator = FileValidator()
        result = validator.validate_data(data, "Track", Path("test.json"))

        assert result.is_valid is True
        assert result.model_name == "Track"

    @staticmethod
    def test_validate_unsupported_model() -> None:
        """Should handle unsupported model type."""
        validator = FileValidator()
        result = validator.validate_data({}, "UnsupportedModel", Path("test.json"))

        assert result.is_valid is False
        assert result.error_count == 1
        assert "Unsupported model type" in result.errors[0]["msg"]

    @staticmethod
    def test_validate_wrong_type_for_list_model() -> None:
        """Should detect type mismatch for list models."""
        # Track expects a list, but we give it a dict
        data = {"title": "Test", "artist_list": ["Artist"]}

        validator = FileValidator()
        result = validator.validate_data(data, "Track", Path("test.json"))

        assert result.is_valid is False
        assert "Expected list" in result.errors[0]["msg"]

    @staticmethod
    def test_validate_multiple_items_with_errors() -> None:
        """Should collect errors from multiple items."""
        data = [
            {"title": "Valid", "artist_list": ["Artist"], "year": 2025},
            {"title": "Missing year", "artist_list": ["Artist"]},  # Missing year
            {"artist_list": ["Artist"], "year": 2025},  # Missing title
        ]

        validator = FileValidator()
        result = validator.validate_data(data, "Track", Path("test.json"))

        assert result.is_valid is False
        assert result.error_count > 0
        # Should have errors for items 1 and 2
        assert any("item_1" in str(err["loc"]) for err in result.errors)
        assert any("item_2" in str(err["loc"]) for err in result.errors)
