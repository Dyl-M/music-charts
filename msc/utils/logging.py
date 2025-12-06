# Standard library
import logging
import sys
from typing import Literal

"""Structured logging setup for the Music Charts pipeline."""

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def setup_logging(
        level: LogLevel = "INFO",
        format_string: str | None = None,
) -> None:
    """Configure the root logger with consistent formatting.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format_string: Custom format string. Uses default if None.
    """
    if format_string is None:
        format_string = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

    logging.basicConfig(
        level=getattr(logging, level),
        format=format_string,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

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
