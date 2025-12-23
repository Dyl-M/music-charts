"""Unit tests for CLI cache manager."""

# Standard library
import time
from pathlib import Path

# Third-party
import pytest

# Local
from msc.commands.cache import CacheManager, CacheStats


class TestCacheStats:
    """Tests for CacheStats dataclass."""

    @staticmethod
    def test_create_cache_stats() -> None:
        """Should create cache statistics."""
        stats = CacheStats(
            file_count=10,
            total_size_bytes=1024,
            oldest_file_age_days=5,
            cache_dir=Path("/cache"),
        )

        assert stats.file_count == 10
        assert stats.total_size_bytes == 1024
        assert stats.oldest_file_age_days == 5

    @staticmethod
    def test_cache_stats_frozen() -> None:
        """Should be immutable (frozen dataclass)."""
        stats = CacheStats(
            file_count=10,
            total_size_bytes=1024,
            oldest_file_age_days=5,
            cache_dir=Path("/cache"),
        )

        with pytest.raises(AttributeError):
            setattr(stats, "file_count", 20)


class TestCacheManagerGetStats:
    """Tests for cache statistics calculation."""

    @staticmethod
    def test_get_stats_empty_cache(tmp_path: Path) -> None:
        """Should return zero stats for empty cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        manager = CacheManager(cache_dir)
        stats = manager.get_stats()

        assert stats.file_count == 0
        assert stats.total_size_bytes == 0
        assert stats.oldest_file_age_days == 0

    @staticmethod
    def test_get_stats_nonexistent_cache() -> None:
        """Should handle nonexistent cache directory."""
        manager = CacheManager(Path("/nonexistent/cache"))
        stats = manager.get_stats()

        assert stats.file_count == 0
        assert stats.total_size_bytes == 0

    @staticmethod
    def test_get_stats_with_files(tmp_path: Path) -> None:
        """Should calculate stats for files in cache."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create test files
        (cache_dir / "file1.json").write_text("test data 1", encoding="utf-8")
        (cache_dir / "file2.json").write_text("test data 2", encoding="utf-8")

        manager = CacheManager(cache_dir)
        stats = manager.get_stats()

        assert stats.file_count == 2
        assert stats.total_size_bytes > 0
        assert stats.cache_dir == cache_dir

    @staticmethod
    def test_get_stats_with_subdirectories(tmp_path: Path) -> None:
        """Should count files in subdirectories."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        subdir = cache_dir / "subdir"
        subdir.mkdir()

        # Create files in subdirectory
        (subdir / "file1.json").write_text("test", encoding="utf-8")
        (cache_dir / "file2.json").write_text("test", encoding="utf-8")

        manager = CacheManager(cache_dir)
        stats = manager.get_stats()

        assert stats.file_count == 2


class TestCacheManagerClean:
    """Tests for cache cleaning operations."""

    @staticmethod
    def test_clean_dry_run(tmp_path: Path) -> None:
        """Should report deletions in dry run mode without deleting."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create test files
        file1 = cache_dir / "file1.json"
        file2 = cache_dir / "file2.json"
        file1.write_text("test", encoding="utf-8")
        file2.write_text("test", encoding="utf-8")

        manager = CacheManager(cache_dir)
        deleted = manager.clean(dry_run=True)

        assert deleted == 2
        # Files should still exist
        assert file1.exists()
        assert file2.exists()

    @staticmethod
    def test_clean_actually_delete(tmp_path: Path) -> None:
        """Should delete files when not in dry run mode."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create test files
        file1 = cache_dir / "file1.json"
        file2 = cache_dir / "file2.json"
        file1.write_text("test", encoding="utf-8")
        file2.write_text("test", encoding="utf-8")

        manager = CacheManager(cache_dir)
        deleted = manager.clean(dry_run=False)

        assert deleted == 2
        # Files should be deleted
        assert not file1.exists()
        assert not file2.exists()
        # Cache directory should be recreated
        assert cache_dir.exists()

    @staticmethod
    def test_clean_nonexistent_cache() -> None:
        """Should handle nonexistent cache directory."""
        manager = CacheManager(Path("/nonexistent/cache"))
        deleted = manager.clean(dry_run=True)

        assert deleted == 0

    @staticmethod
    def test_clean_with_age_filter(tmp_path: Path) -> None:
        """Should only delete files older than specified days."""
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()

        # Create old file
        old_file = cache_dir / "old.json"
        old_file.write_text("old", encoding="utf-8")

        # Make it old by modifying timestamp
        old_time = time.time() - (10 * 24 * 60 * 60)  # 10 days ago
        old_file.touch()
        import os
        os.utime(old_file, (old_time, old_time))

        # Create new file
        new_file = cache_dir / "new.json"
        new_file.write_text("new", encoding="utf-8")

        manager = CacheManager(cache_dir)
        deleted = manager.clean(dry_run=True, older_than_days=7)

        # Should only count the old file
        assert deleted == 1


class TestCacheManagerFormatSize:
    """Tests for file size formatting."""

    @staticmethod
    def test_format_size_bytes() -> None:
        """Should format bytes correctly."""
        manager = CacheManager(Path("/cache"))

        assert manager.format_size(0) == "0 B"
        assert manager.format_size(512) == "512 B"
        assert manager.format_size(1023) == "1023 B"

    @staticmethod
    def test_format_size_kb() -> None:
        """Should format KB correctly."""
        manager = CacheManager(Path("/cache"))

        assert manager.format_size(1024) == "1.0 KB"
        assert manager.format_size(2048) == "2.0 KB"

    @staticmethod
    def test_format_size_mb() -> None:
        """Should format MB correctly."""
        manager = CacheManager(Path("/cache"))

        assert manager.format_size(1024 * 1024) == "1.0 MB"
        assert manager.format_size(1024 * 1024 * 2) == "2.0 MB"

    @staticmethod
    def test_format_size_gb() -> None:
        """Should format GB correctly."""
        manager = CacheManager(Path("/cache"))

        assert manager.format_size(1024 ** 3) == "1.00 GB"
        assert manager.format_size(1024 ** 3 * 2) == "2.00 GB"
