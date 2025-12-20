"""Path utilities for secure file operations.

Provides utilities for validating file paths to prevent directory traversal
and other path-based security vulnerabilities.
"""

# Standard library
from pathlib import Path


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
