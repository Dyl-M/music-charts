"""Unit tests for path utilities.

Tests validate_path_within_base and secure_write functions for security
and proper path handling.
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
    def test_accepts_path_within_base(tmp_path: Path) -> None:
        """Should accept path that is within base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        target = base_dir / "subdir" / "file.txt"

        result = validate_path_within_base(target, base_dir, "test")

        assert result.is_relative_to(base_dir)

    @staticmethod
    def test_rejects_path_outside_base(tmp_path: Path) -> None:
        """Should reject path outside base directory."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"

        with pytest.raises(ValueError, match="Security error"):
            validate_path_within_base(outside_path, base_dir, "test")

    @staticmethod
    def test_rejects_parent_traversal(tmp_path: Path) -> None:
        """Should reject path with parent directory traversal."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        traversal_path = base_dir / ".." / "outside" / "file.txt"

        with pytest.raises(ValueError, match="Security error"):
            validate_path_within_base(traversal_path, base_dir, "test")

    @staticmethod
    def test_creates_base_directory_if_missing(tmp_path: Path) -> None:
        """Should create base directory if it doesn't exist."""
        base_dir = tmp_path / "new_base"
        target = base_dir / "file.txt"

        validate_path_within_base(target, base_dir, "test")

        assert base_dir.exists()

    @staticmethod
    def test_returns_resolved_path(tmp_path: Path) -> None:
        """Should return fully resolved path."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        target = base_dir / "subdir" / ".." / "file.txt"

        result = validate_path_within_base(target, base_dir, "test")

        assert result == (base_dir / "file.txt").resolve()

    @staticmethod
    def test_error_message_includes_purpose(tmp_path: Path) -> None:
        """Should include purpose in error message."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"

        with pytest.raises(ValueError, match="export"):
            validate_path_within_base(outside_path, base_dir, "export")

    @staticmethod
    def test_handles_symlinks_safely(tmp_path: Path) -> None:
        """Should resolve symlinks before validation."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()

        # Create a symlink inside base pointing outside
        symlink = base_dir / "link"
        try:
            symlink.symlink_to(outside_dir)
            target = symlink / "file.txt"

            with pytest.raises(ValueError, match="Security error"):
                validate_path_within_base(target, base_dir, "test")
        except OSError:
            # Skip on Windows if symlinks not supported
            pytest.skip("Symlinks not supported on this platform")


class TestSecureWrite:
    """Tests for secure_write context manager."""

    @staticmethod
    def test_writes_file_successfully(tmp_path: Path) -> None:
        """Should write file content successfully."""
        file_path = tmp_path / "output.txt"

        with secure_write(file_path, encoding="utf-8") as f:
            f.write("test content")

        assert file_path.read_text(encoding="utf-8") == "test content"

    @staticmethod
    def test_creates_parent_directories(tmp_path: Path) -> None:
        """Should create parent directories if missing."""
        file_path = tmp_path / "nested" / "dir" / "output.txt"

        with secure_write(file_path, encoding="utf-8") as f:
            f.write("test")

        assert file_path.exists()

    @staticmethod
    def test_validates_against_base_dir(tmp_path: Path) -> None:
        """Should validate path against base directory when provided."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"

        with pytest.raises(ValueError, match="Security error"):
            with secure_write(outside_path, base_dir=base_dir, purpose="test"):
                pass

    @staticmethod
    def test_skips_validation_without_base_dir(tmp_path: Path) -> None:
        """Should skip validation when base_dir is None."""
        file_path = tmp_path / "output.txt"

        with secure_write(file_path, encoding="utf-8") as f:
            f.write("test")

        assert file_path.exists()

    @staticmethod
    def test_supports_binary_mode(tmp_path: Path) -> None:
        """Should support binary write mode."""
        file_path = tmp_path / "output.bin"

        with secure_write(file_path, mode="wb") as f:
            f.write(b"binary content")

        assert file_path.read_bytes() == b"binary content"

    @staticmethod
    def test_passes_open_kwargs(tmp_path: Path) -> None:
        """Should pass kwargs to open()."""
        file_path = tmp_path / "output.txt"

        with secure_write(file_path, encoding="utf-8", newline="\n") as f:
            f.write("line1\nline2")

        content = file_path.read_text(encoding="utf-8")
        assert "line1\nline2" in content

    @staticmethod
    def test_includes_purpose_in_error(tmp_path: Path) -> None:
        """Should include purpose in validation error."""
        base_dir = tmp_path / "base"
        base_dir.mkdir()
        outside_path = tmp_path / "outside" / "file.txt"

        with pytest.raises(ValueError, match="export"):
            with secure_write(
                    outside_path, base_dir=base_dir, purpose="export", encoding="utf-8"
            ):
                pass
