"""Cache management utilities for CLI commands.

Provides tools for analyzing and cleaning cached data files including
API response caches, checkpoints, and temporary files.
"""

# Standard library
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

# Local
from msc.config.settings import get_settings


@dataclass(frozen=True)
class CacheStats:
    """Cache statistics.

    Attributes:
        file_count: Total number of files in cache
        total_size_bytes: Combined size of all cache files
        oldest_file_age_days: Age of oldest file in days
        cache_dir: Path to cache directory
    """

    file_count: int
    total_size_bytes: int
    oldest_file_age_days: int
    cache_dir: Path


class CacheManager:
    """Manager for cache directory operations.

    Handles calculation of cache statistics and safe deletion
    of cached files with dry-run mode for safety.
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize cache manager.

        Args:
            cache_dir: Path to cache directory (uses settings default if None)
        """
        if cache_dir is None:
            settings = get_settings()
            cache_dir = settings.cache_dir

        self.cache_dir = cache_dir

    def get_stats(self) -> CacheStats:
        """Calculate current cache statistics.

        Returns:
            CacheStats with file counts, sizes, and age information

        Note:
            Returns stats with zero values if cache directory doesn't exist
        """
        if not self.cache_dir.exists():
            return CacheStats(
                file_count=0,
                total_size_bytes=0,
                oldest_file_age_days=0,
                cache_dir=self.cache_dir,
            )

        # Collect all files (single comprehension)
        cache_files = [f for f in self.cache_dir.rglob("*") if f.is_file()]

        if not cache_files:
            return CacheStats(
                file_count=0,
                total_size_bytes=0,
                oldest_file_age_days=0,
                cache_dir=self.cache_dir,
            )

        # Cache stat results to avoid calling stat() twice per file
        file_stats = [f.stat() for f in cache_files]
        total_size = sum(s.st_size for s in file_stats)
        oldest_mtime = min(s.st_mtime for s in file_stats)
        oldest_date = datetime.fromtimestamp(oldest_mtime)
        age_days = (datetime.now() - oldest_date).days

        return CacheStats(
            file_count=len(cache_files),
            total_size_bytes=total_size,
            oldest_file_age_days=age_days,
            cache_dir=self.cache_dir,
        )

    def clean(
            self,
            dry_run: bool = True,
            older_than_days: int | None = None,
    ) -> int:
        """Remove cache files.

        Args:
            dry_run: If True, only report what would be deleted without deleting
            older_than_days: Only delete files older than N days (None = all files)

        Returns:
            Number of files that were (or would be) deleted

        Note:
            Creates cache directory if it doesn't exist after cleaning
        """
        if not self.cache_dir.exists():
            return 0

        # Collect files to delete
        all_files = list(self.cache_dir.rglob("*"))
        files_to_delete = [f for f in all_files if f.is_file()]

        # Filter by age if specified
        if older_than_days is not None:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            files_to_delete = [
                f
                for f in files_to_delete
                if datetime.fromtimestamp(f.stat().st_mtime) < cutoff_date
            ]

        if dry_run:
            # Just report what would be deleted
            return len(files_to_delete)

        # Actually delete files
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                file_path.unlink()
                deleted_count += 1

            except OSError:
                # Skip files that can't be deleted
                continue

        # Clean up empty directories
        self._remove_empty_dirs(self.cache_dir)

        # Recreate cache directory structure
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        return deleted_count

    def _remove_empty_dirs(self, directory: Path) -> None:
        """Recursively remove empty directories.

        Args:
            directory: Directory to clean

        Note:
            Does not remove the root directory itself
        """
        if not directory.exists() or directory == self.cache_dir:
            return

        # Process subdirectories first (bottom-up)
        for subdir in [d for d in directory.iterdir() if d.is_dir()]:
            self._remove_empty_dirs(subdir)

        # Remove directory if empty
        try:
            if directory != self.cache_dir and not any(directory.iterdir()):
                directory.rmdir()

        except OSError:
            # Skip if directory can't be removed
            pass

    # File size formatting rules: (threshold, divisor, unit, precision)
    # Checked in order from largest to smallest
    _SIZE_UNITS: list[tuple[int, int, str, int]] = [
        (1024 ** 3, 1024 ** 3, "GB", 2),  # >= 1 GB
        (1024 ** 2, 1024 ** 2, "MB", 1),  # >= 1 MB
        (1024, 1024, "KB", 1),  # >= 1 KB
        (0, 1, "B", 0),  # < 1 KB
    ]

    @staticmethod
    def format_size(size_bytes: int) -> str:
        """Format byte size as human-readable string.

        Args:
            size_bytes: Size in bytes

        Returns:
            Formatted string (e.g., "1.5 MB", "234 KB")
        """
        for threshold, divisor, unit, precision in CacheManager._SIZE_UNITS:
            if size_bytes >= threshold:
                value = size_bytes / divisor
                return f"{value:.{precision}f} {unit}"

        # Fallback (should never reach here due to final rule with threshold=0)
        return f"{size_bytes} B"
