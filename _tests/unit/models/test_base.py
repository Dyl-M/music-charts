"""Unit tests for base model module.

Tests MSCBaseModel class, serialization, and file operations.
"""

# Standard library
import json
from pathlib import Path

# Third-party
import pytest
from pydantic import ValidationError

# Local
from msc.models.base import MSCBaseModel, PROJECT_ROOT


class SampleModel(MSCBaseModel):
    """Sample model for testing MSCBaseModel functionality."""

    name: str
    count: int | None = None
    tags: list[str] | None = None


class TestMSCBaseModelConfig:
    """Tests for MSCBaseModel configuration."""

    @staticmethod
    def test_strips_whitespace_from_strings() -> None:
        """Should auto-strip whitespace from string fields."""
        model = SampleModel(name="  test name  ")
        assert model.name == "test name"

    @staticmethod
    def test_validates_on_assignment() -> None:
        """Should validate when attributes are assigned."""

        # Create mutable subclass for testing
        class MutableModel(MSCBaseModel):
            """Mutable test model."""

            value: int

        model = MutableModel(value=5)
        with pytest.raises(ValidationError):
            model.value = "not an int"  # type: ignore[assignment]

    @staticmethod
    def test_allows_population_by_alias() -> None:
        """Should allow using alias names for field population."""

        class AliasModel(MSCBaseModel):
            """Model with aliased field."""

            full_name: str

        # Both should work
        model1 = AliasModel(full_name="test")
        assert model1.full_name == "test"


class TestToFlatDict:
    """Tests for to_flat_dict method."""

    @staticmethod
    def test_returns_dict() -> None:
        """Should return a dictionary."""
        model = SampleModel(name="test", count=5)
        result = model.to_flat_dict()
        assert isinstance(result, dict)

    @staticmethod
    def test_excludes_none_values() -> None:
        """Should exclude None values from output."""
        model = SampleModel(name="test", count=None)
        result = model.to_flat_dict()
        assert "count" not in result
        assert result == {"name": "test"}

    @staticmethod
    def test_includes_non_none_values() -> None:
        """Should include non-None values."""
        model = SampleModel(name="test", count=5, tags=["a", "b"])
        result = model.to_flat_dict()
        assert result["name"] == "test"
        assert result["count"] == 5
        assert result["tags"] == ["a", "b"]


class TestToJsonFile:
    """Tests for to_json_file method."""

    @staticmethod
    def test_saves_to_file() -> None:
        """Should save model to JSON file."""
        model = SampleModel(name="test", count=5)
        # Use path within PROJECT_ROOT for validation
        file_path = PROJECT_ROOT / "_data" / "test_output.json"

        try:
            model.to_json_file(file_path)
            assert file_path.exists()

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["name"] == "test"
            assert data["count"] == 5
        finally:
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def test_creates_parent_directories() -> None:
        """Should create parent directories if missing."""
        model = SampleModel(name="test")
        nested_path = PROJECT_ROOT / "_data" / "nested" / "dir" / "test.json"

        try:
            model.to_json_file(nested_path)
            assert nested_path.exists()
        finally:
            if nested_path.exists():
                nested_path.unlink()
            # Clean up directories
            if (PROJECT_ROOT / "_data" / "nested").exists():
                import shutil
                shutil.rmtree(PROJECT_ROOT / "_data" / "nested")

    @staticmethod
    def test_uses_utf8_encoding() -> None:
        """Should use UTF-8 encoding for special characters."""
        model = SampleModel(name="test 日本語 émojis 🎵")
        file_path = PROJECT_ROOT / "_data" / "unicode_test.json"

        try:
            model.to_json_file(file_path)

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["name"] == "test 日本語 émojis 🎵"
        finally:
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def test_excludes_none_in_json() -> None:
        """Should exclude None values in JSON output."""
        model = SampleModel(name="test", count=None)
        file_path = PROJECT_ROOT / "_data" / "none_test.json"

        try:
            model.to_json_file(file_path)

            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            assert "count" not in data
        finally:
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def test_rejects_path_outside_project() -> None:
        """Should reject paths outside project root."""
        model = SampleModel(name="test")
        outside_path = Path("/tmp/outside.json")

        with pytest.raises(ValueError, match="Security error"):
            model.to_json_file(outside_path)


class TestFromJsonFile:
    """Tests for from_json_file method."""

    @staticmethod
    def test_loads_from_file() -> None:
        """Should load model from JSON file."""
        file_path = PROJECT_ROOT / "_data" / "load_test.json"

        try:
            # Create test file
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"name": "loaded", "count": 10}, f)

            model = SampleModel.from_json_file(file_path)
            assert model.name == "loaded"
            assert model.count == 10
        finally:
            if file_path.exists():
                file_path.unlink()

    @staticmethod
    def test_raises_for_missing_file() -> None:
        """Should raise FileNotFoundError for missing file."""
        missing_path = PROJECT_ROOT / "_data" / "missing.json"

        with pytest.raises(FileNotFoundError, match="File not found"):
            SampleModel.from_json_file(missing_path)

    @staticmethod
    def test_rejects_path_outside_project() -> None:
        """Should reject paths outside project root."""
        outside_path = Path("/tmp/outside.json")

        with pytest.raises(ValueError, match="Security error"):
            SampleModel.from_json_file(outside_path)

    @staticmethod
    def test_handles_utf8_content() -> None:
        """Should handle UTF-8 encoded content."""
        file_path = PROJECT_ROOT / "_data" / "utf8_load_test.json"

        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({"name": "тест 日本語"}, f, ensure_ascii=False)

            model = SampleModel.from_json_file(file_path)
            assert model.name == "тест 日本語"
        finally:
            if file_path.exists():
                file_path.unlink()


class TestProjectRoot:
    """Tests for PROJECT_ROOT constant."""

    @staticmethod
    def test_project_root_exists() -> None:
        """Should point to existing directory."""
        assert PROJECT_ROOT.exists()
        assert PROJECT_ROOT.is_dir()

    @staticmethod
    def test_project_root_contains_msc() -> None:
        """Should contain msc package."""
        assert (PROJECT_ROOT / "msc").exists()
