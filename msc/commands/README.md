# Commands Module

CLI utilities for error handling, validation, formatting, export, and cache management.

## Modules

| Module          | Purpose                                               |
|-----------------|-------------------------------------------------------|
| `errors.py`     | Custom exceptions and error handler registry          |
| `validators.py` | File validation with automatic format detection       |
| `formatters.py` | Rich display formatters for quota, validation, export |
| `exporters.py`  | Data export to CSV, ODS, HTML formats                 |
| `cache.py`      | Cache statistics and cleanup utilities                |

## Error Handling

Custom exceptions with user-friendly suggestions.

```python
from msc.commands.errors import (
    MSCError,
    ConfigurationError,
    APIError,
    ValidationError,
    ExportError,
    ErrorHandler,
)

# Raise with helpful suggestion
raise ConfigurationError(
    message="Songstats API key not found",
    suggestion="Set MSC_SONGSTATS_API_KEY or create _tokens/songstats_key.txt"
)

# Error handler for CLI
handler = ErrorHandler()

try:
# ... operation
except Exception as e:
    handler.handle(e)  # Formats and displays error with suggestion
```

## File Validation

Validate JSON files against Pydantic models with auto-detection.

```python
from msc.commands.validators import FileValidator
from pathlib import Path

validator = FileValidator()

# Validate with auto-detection (detects Track, TrackWithStats, PowerRankingResults)
result = validator.validate(Path("_data/output/2025/stats.json"))

if result.valid:
    print(f"Valid {result.detected_type}: {result.record_count} records")
else:
    print(f"Validation failed: {result.error_message}")
    for error in result.validation_errors[:5]:
        print(f"  - {error}")

# Force specific type
result = validator.validate(
    path=Path("data.json"),
    expected_type="TrackWithStats"
)
```

## Display Formatters

Rich console output for CLI commands.

```python
from msc.commands.formatters import (
    QuotaFormatter,
    ValidationFormatter,
    ExportFormatter,
)

# Format quota display (msc billing)
quota_data = {"requests_used": 1500, "requests_limit": 10000, "reset_date": "2025-02-01"}
QuotaFormatter.display(quota_data)
# ┌─────────────────────────┐
# │ Songstats API Quota     │
# ├─────────────────────────┤
# │ Used: 1,500 / 10,000    │
# │ Remaining: 8,500 (85%)  │
# │ Resets: 2025-02-01      │
# └─────────────────────────┘

# Format validation result (msc validate)
ValidationFormatter.display(result)

# Format export result (msc export)
export_result = ExportResult(success=True, file_path=Path("out.csv"), row_count=100, ...)
ExportFormatter.display(export_result)
```

## Data Export

Export rankings and statistics to multiple formats.

```python
from msc.commands.exporters import DataExporter, ExportResult
from msc.storage.json_repository import JSONStatsRepository
from pathlib import Path

# Initialize with repository
repo = JSONStatsRepository(file_path=Path("_data/output/2025/stats.json"))
exporter = DataExporter(repository=repo)

# Export to CSV
result = exporter.export_csv(output_path=Path("rankings.csv"))
print(f"Exported {result.row_count} rows to {result.file_path}")

# Export to ODS (LibreOffice/OpenOffice)
result = exporter.export_ods(output_path=Path("rankings.ods"))

# Export to HTML (with styling)
result = exporter.export_html(output_path=Path("rankings.html"))

# Check result
if result.success:
    print(f"File size: {result.file_size_bytes / 1024:.1f} KB")
    print(f"Duration: {result.duration_seconds:.2f}s")
```

## Cache Management

Statistics and cleanup for cached API responses.

```python
from msc.commands.cache import CacheManager
from pathlib import Path

# Initialize with cache directory
manager = CacheManager(cache_dir=Path("_data/cache"))

# Get cache statistics
stats = manager.get_statistics()
print(f"Total files: {stats['file_count']}")
print(f"Total size: {stats['total_size_mb']:.1f} MB")
print(f"Oldest file: {stats['oldest_file']}")

# List files (for dry run)
files = manager.list_files(older_than_days=7)
for f in files:
    print(f"  {f.name} ({f.stat().st_size / 1024:.1f} KB)")

# Clean cache (dry run)
result = manager.clean(dry_run=True)
print(f"Would delete {result['files_deleted']} files ({result['space_freed_mb']:.1f} MB)")

# Actually clean
result = manager.clean(dry_run=False, older_than_days=7)
print(f"Deleted {result['files_deleted']} files")
```

## CLI Integration

These utilities power the `msc` CLI commands:

| Command        | Modules Used                                                 |
|----------------|--------------------------------------------------------------|
| `msc billing`  | `formatters.QuotaFormatter`                                  |
| `msc validate` | `validators.FileValidator`, `formatters.ValidationFormatter` |
| `msc export`   | `exporters.DataExporter`, `formatters.ExportFormatter`       |
| `msc clean`    | `cache.CacheManager`                                         |
| `msc stats`    | `cache.CacheManager`, formatters                             |
| All commands   | `errors.ErrorHandler`                                        |
