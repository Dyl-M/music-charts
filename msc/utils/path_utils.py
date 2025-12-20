"""Path utilities for secure file operations.

Provides utilities for validating file paths to prevent directory traversal
and other path-based security vulnerabilities.
"""

# Standard library
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator


def validate_path_within_base(
        target_path: Path, base_dir: Path, purpose: str = "operation"
) -> Path:
    """Validate that target path is within allowed base directory.

    This function prevents directory traversal attacks by ensuring that
    resolved file paths remain within approved base directories.

    Args:
        target_path: Path to validate
        base_dir: Allowed base directory
        purpose: Description of operation (for error messages)

    Returns:
        Resolved path if validation succeeds

    Raises:
        ValueError: If target path is outside allowed base directory

    Example:
        >>> from pathlib import Path
        >>> base = Path("/allowed/dir")
        >>> safe_path = validate_path_within_base(
        ...     Path("output.json"), base, "export"
        ... )
    """
    # Resolve both paths to absolute, normalized forms
    resolved_target = target_path.resolve()
    resolved_base = base_dir.resolve()

    # Ensure base directory exists or can be created
    resolved_base.mkdir(parents=True, exist_ok=True)

    # Check if target is within base directory
    try:
        # relative_to() raises ValueError if paths don't share a common base
        resolved_target.relative_to(resolved_base)

    except ValueError as error:
        raise ValueError(
            f"Security error: {purpose} path '{target_path}' "
            f"is outside allowed directory '{base_dir}'"
        ) from error

    return resolved_target


@contextmanager
def secure_write(
        file_path: Path,
        base_dir: Path | None = None,
        purpose: str = "write",
        mode: str = "w",
        **open_kwargs: Any,
) -> Iterator[Any]:
    """Securely open a file for writing with optional path validation.

    This context manager provides a secure file writing pattern that:
    1. Validates the path against a base directory (if provided)
    2. Resolves the path to prevent directory traversal
    3. Creates parent directories as needed
    4. Opens the file with specified mode and options

    Args:
        file_path: Path to file to write
        base_dir: Optional base directory for validation. If None, only resolve() is used
        purpose: Description of operation (for error messages)
        mode: File mode (default: "w")
        **open_kwargs: Additional arguments for open() (encoding, newline, etc.)

    Yields:
        File handle for writing

    Raises:
        ValueError: If base_dir is provided and path is outside base directory
        OSError: If file cannot be opened or created

    Example:
        >>> # With base directory validation
        >>> with secure_write(
        ...     Path("output.json"),
        ...     base_dir=Path("_data/output"),
        ...     purpose="export",
        ...     encoding="utf-8"
        ... ) as file1:
        ...     json.dump(data, file1)

        >>> # Without validation (configuration-controlled paths)
        >>> with secure_write(Path("/var/log/app.log"), encoding="utf-8") as file2:
        ...     file2.write("Log entry")
    """
    # Validate or resolve path based on whether base_dir is provided
    if base_dir is not None:
        validated_path = validate_path_within_base(file_path, base_dir, purpose)

    else:
        validated_path = file_path.resolve()

    # Ensure parent directory exists
    validated_path.parent.mkdir(parents=True, exist_ok=True)

    # Open file securely with provided options
    with open(validated_path, mode, **open_kwargs) as f:
        yield f
