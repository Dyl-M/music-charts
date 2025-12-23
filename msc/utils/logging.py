"""Structured logging setup for the Music Charts pipeline."""

# Standard library
import logging
import sys
from pathlib import Path
from typing import Literal

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(
        level: LogLevel = "INFO",
        format_string: str | None = None,
        console_level: LogLevel | None = None,
        log_file: Path | None = None,
) -> None:
    """Configure the root logger with consistent formatting.

    Args:
        level: Base logging level for file output (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom format string. Uses default if None.
        console_level: Separate level for console output. If None, uses `level`.
        log_file: Optional file path for file logging. If None, no file logging.
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    # Set root logger to most verbose level (file or console)
    root_level = level
    if console_level:
        # Use whichever is more verbose (lower level number)
        root_level = level if getattr(logging, level) <= getattr(logging, console_level) else console_level

    # Clear existing handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(getattr(logging, root_level))

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, console_level or level))
    console_handler.setFormatter(
        logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
    )
    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setLevel(getattr(logging, level))
        file_handler.setFormatter(
            logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")
        )
        root_logger.addHandler(file_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__ from the calling module).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)


class PipelineLogger:
    """Context-aware logger for pipeline stages."""

    def __init__(self, stage_name: str):
        """Initialize the pipeline logger.

        Args:
            stage_name: Name of the pipeline stage for context.
        """
        self._logger = logging.getLogger(f"msc.pipeline.{stage_name}")
        self.stage_name = stage_name

    def info(self, message: str, **kwargs: object) -> None:
        """Log an info message with optional context."""
        self._logger.info(self._format_message(message, kwargs))

    def debug(self, message: str, **kwargs: object) -> None:
        """Log a debug message with optional context."""
        self._logger.debug(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs: object) -> None:
        """Log a warning message with optional context."""
        self._logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs: object) -> None:
        """Log an error message with optional context."""
        self._logger.error(self._format_message(message, kwargs))

    def progress(self, current: int, total: int, item: str = "") -> None:
        """Log progress update."""
        percentage = (current / total) * 100 if total > 0 else 0
        msg = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if item:
            msg += f" - {item}"
        self._logger.info(msg)

    @staticmethod
    def _format_message(message: str, context: dict[str, object]) -> str:
        """Format message with optional context."""
        if context:
            context_str = " | ".join(f"{k}={v}" for k, v in context.items())
            return f"{message} | {context_str}"
        return message
