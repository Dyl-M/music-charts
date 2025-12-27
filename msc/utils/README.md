# Utils Module

Shared utilities for logging, retry logic, text processing, and path security.

## Modules

| Module          | Purpose                                                    |
|-----------------|------------------------------------------------------------|
| `logging.py`    | Structured logging with dual-level output (console + file) |
| `retry.py`      | Exponential backoff decorator and rate limiting            |
| `text.py`       | Text normalization for track titles and artist names       |
| `path_utils.py` | Secure file operations with path traversal protection      |

## Logging

Dual-level logging: console shows only errors, file captures all INFO+ messages.

```python
from msc.utils.logging import setup_logging, get_logger, PipelineLogger
from pathlib import Path

# Configure logging (typically done once at startup)
setup_logging(
    level="INFO",  # File log level
    console_level="ERROR",  # Console shows only errors
    log_file=Path("_data/logs/pipeline.log"),
)

# Get a module logger
logger = get_logger(__name__)
logger.info("Processing started")
logger.error("Something went wrong: %s", error_msg)  # Lazy formatting

# Pipeline-specific logger with stage context
plog = PipelineLogger("extraction")
plog.info("Found %s tracks", count)
plog.progress(current=50, total=100, item="Track Name")
```

## Retry

Automatic retry with exponential backoff for API calls.

```python
from msc.utils.retry import retry_with_backoff, RateLimiter


# Decorator for automatic retry
@retry_with_backoff(max_retries=3, min_wait=1.0, max_wait=60.0)
def fetch_data(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


# Rate limiter for API calls
limiter = RateLimiter(requests_per_second=10)

for item in items:
    with limiter:  # Automatically waits if needed
        result = api.fetch(item)
```

## Text Processing

Normalize track titles and artist names for API search accuracy.

```python
from msc.utils.text import (
    format_title,
    format_artist,
    build_search_query,
    remove_remixer,
    truncate,
)

# Clean track title (removes [Extended Mix], special chars, etc.)
title = format_title("Song Name [Extended Mix]")
# → "song name"

# Clean artist name (removes feat., special separators)
artist = format_artist("Artist A (feat. Artist B)")
# → "artist a"

artist = format_artist("Artist A × Artist B")
# → "artist a artist b"

# Build search query
query = build_search_query("song name", ["artist a", "artist b"])
# → "artist a artist b song name"

# Remove remixers from artist list
artists = remove_remixer("original (artist b remix)", ["artist a", "artist b"])
# → ["artist a"]

# Truncate long text
short = truncate("Very long track name here", max_length=20)
# → "Very long track n..."
```

## Path Security

Prevent directory traversal attacks in file operations.

```python
from msc.utils.path_utils import validate_path_within_base, secure_write
from pathlib import Path
import json

# Validate path is within allowed directory
base_dir = Path("_data/output")
safe_path = validate_path_within_base(
    target_path=Path("2025/tracks.json"),
    base_dir=base_dir,
    purpose="export"
)
# Raises ValueError if path escapes base_dir (e.g., "../../../etc/passwd")

# Secure file writing with automatic validation
with secure_write(
        file_path=Path("output.json"),
        base_dir=Path("_data/output"),
        purpose="export",
        encoding="utf-8"
) as f:
    json.dump(data, f)
```
