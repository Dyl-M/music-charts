"""Tests for path utilities module.

Tests path validation and secure file writing utilities for preventing
directory traversal attacks.
"""

# Standard library
from pathlib import Path

# Third-party
import pytest

# Local
from msc.utils.path_utils import secure_write, validate_path_within_base


class TestValidatePathWithinBase:
    """Tests for validate_path_within_base function."""

    @staticmethod
    def test_valid_path_within_base(tmp_path: Path) -> None:
        """Test validation succeeds for path within base directory."""
        base = tmp_path / "allowed"
        target = base / "subdir" / "file.txt"

        result = validate_path_within_base(target, base, "test")

        assert result.is_absolute()
        assert result.is_relative_to(base)

    @staticmethod
    def test_path_outside_base_raises_error(tmp_path: Path) -> None:
        """Test validation fails for path outside base directory."""
        base = tmp_path / "allowed"
        target = tmp_path / "forbidden" / "file.txt"

        with pytest.raises(ValueError, match="Security error.*outside allowed directory"):
            validate_path_within_base(target, base, "test")

    @staticmethod
    def test_directory_traversal_attempt(tmp_path: Path) -> None:
        """Test validation prevents directory traversal attack."""
        base = tmp_path / "allowed"
        target = base / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValueError, match="Security error.*outside allowed directory"):
            validate_path_within_base(target, base, "malicious")

    @staticmethod
    def test_creates_base_directory(tmp_path: Path) -> None:
        """Test base directory is created if it doesn't exist."""
        base = tmp_path / "new_base"
        target = base / "file.txt"

        assert not base.exists()
        validate_path_within_base(target, base, "test")
        assert base.exists()

    @staticmethod
    def test_custom_purpose_in_error_message(tmp_path: Path) -> None:
        """Test custom purpose appears in error message."""
        base = tmp_path / "allowed"
        target = tmp_path / "forbidden" / "file.txt"

        with pytest.raises(ValueError, match="export path.*outside allowed directory"):
            validate_path_within_base(target, base, purpose="export")


class TestSecureWrite:
    """Tests for secure_write context manager."""

    @staticmethod
    def test_write_with_base_validation(tmp_path: Path) -> None:
        """Test secure write with base directory validation."""
        base = tmp_path / "output"
        file_path = base / "test.txt"

        with secure_write(file_path, base_dir=base, encoding="utf-8") as f:
            f.write("test content")

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "test content"

    @staticmethod
    def test_write_without_validation(tmp_path: Path) -> None:
        """Test secure write without base directory validation."""
        file_path = tmp_path / "test.txt"

        with secure_write(file_path, encoding="utf-8") as f:
            f.write("test content")

        assert file_path.exists()
        assert file_path.read_text(encoding="utf-8") == "test content"

    @staticmethod
    def test_creates_parent_directories(tmp_path: Path) -> None:
        """Test parent directories are created automatically."""
        file_path = tmp_path / "nested" / "deep" / "file.txt"

        assert not file_path.parent.exists()

        with secure_write(file_path, encoding="utf-8") as f:
            f.write("test")

        assert file_path.parent.exists()
        assert file_path.exists()

    @staticmethod
    def test_write_outside_base_raises_error(tmp_path: Path) -> None:
        """Test writing outside base directory raises error."""
        base = tmp_path / "allowed"
        file_path = tmp_path / "forbidden" / "file.txt"

        with pytest.raises(ValueError, match="Security error"), secure_write(file_path, base_dir=base, purpose="export", encoding="utf-8") as f:
            f.write("test")

    @staticmethod
    def test_custom_file_mode(tmp_path: Path) -> None:
        """Test using custom file mode."""
        file_path = tmp_path / "test.txt"

        # Write initial content
        file_path.write_text("initial", encoding="utf-8")

        # Append mode
        with secure_write(file_path, mode="a", encoding="utf-8") as f:
            f.write(" appended")

        assert file_path.read_text(encoding="utf-8") == "initial appended"

    @staticmethod
    def test_custom_open_kwargs(tmp_path: Path) -> None:
        """Test passing custom kwargs to open()."""
        file_path = tmp_path / "test.txt"

        with secure_write(file_path, mode="w", encoding="utf-8", newline="\n") as f:
            f.write("line1\nline2\n")

        content = file_path.read_text(encoding="utf-8")
        assert "line1\nline2\n" in content
