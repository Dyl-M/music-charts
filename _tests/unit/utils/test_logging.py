"""Unit tests for logging utilities.

Tests setup_logging function, get_logger function, and PipelineLogger class.
"""

# Standard library
import logging
from pathlib import Path
from unittest.mock import patch

# Third-party
import pytest

# Local
from msc.utils.logging import PipelineLogger, get_logger, setup_logging


class TestSetupLogging:
    """Tests for setup_logging function."""

    @staticmethod
    def test_sets_default_log_level() -> None:
        """Should set INFO level by default."""
        setup_logging()
        assert logging.getLogger().level == logging.INFO

    @staticmethod
    def test_sets_custom_log_level() -> None:
        """Should set custom log level."""
        setup_logging(level="DEBUG")
        assert logging.getLogger().level == logging.DEBUG

    @staticmethod
    def test_uses_default_format_when_none() -> None:
        """Should use default format string when not provided."""
        setup_logging()
        handler = logging.getLogger().handlers[0]
        assert "%(asctime)s" in handler.formatter._fmt  # type: ignore[union-attr]

    @staticmethod
    def test_uses_custom_format() -> None:
        """Should use custom format string when provided."""
        custom_format = "%(message)s"
        setup_logging(format_string=custom_format)
        handler = logging.getLogger().handlers[0]
        assert handler.formatter._fmt == custom_format  # type: ignore[union-attr]

    @staticmethod
    def test_reduces_third_party_noise() -> None:
        """Should set third-party loggers to WARNING level."""
        setup_logging()
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("requests").level == logging.WARNING
        assert logging.getLogger("google").level == logging.WARNING

    @staticmethod
    def test_clears_existing_handlers() -> None:
        """Should clear existing handlers before adding new ones."""
        root_logger = logging.getLogger()
        root_logger.addHandler(logging.StreamHandler())
        initial_count = len(root_logger.handlers)
        assert initial_count >= 1  # Verify handler was added

        setup_logging()

        # Should have exactly 1 handler (console)
        assert len(root_logger.handlers) == 1

    @staticmethod
    def test_console_level_separate_from_file_level() -> None:
        """Should support separate console and file log levels."""
        setup_logging(level="DEBUG", console_level="WARNING")
        root_logger = logging.getLogger()

        # Root should be set to more verbose (DEBUG)
        assert root_logger.level == logging.DEBUG

        # Console handler should be WARNING
        console_handler = root_logger.handlers[0]
        assert console_handler.level == logging.WARNING

    @staticmethod
    def test_file_handler_created_when_log_file_provided(tmp_path: Path) -> None:
        """Should create file handler when log_file is provided."""
        log_file = tmp_path / "test.log"

        setup_logging(log_file=log_file)

        root_logger = logging.getLogger()
        file_handlers = [
            h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
        ]
        assert len(file_handlers) == 1
        assert file_handlers[0].baseFilename == str(log_file)

    @staticmethod
    def test_creates_log_directory(tmp_path: Path) -> None:
        """Should create log directory if it doesn't exist."""
        log_file = tmp_path / "logs" / "test.log"

        setup_logging(log_file=log_file)

        assert log_file.parent.exists()

    @staticmethod
    def test_file_handler_uses_utf8_encoding(tmp_path: Path) -> None:
        """Should use UTF-8 encoding for file handler."""
        log_file = tmp_path / "test.log"

        setup_logging(log_file=log_file)

        root_logger = logging.getLogger()
        file_handler = [
            h for h in root_logger.handlers if isinstance(h, logging.FileHandler)
        ][0]
        assert file_handler.encoding == "utf-8"


class TestGetLogger:
    """Tests for get_logger function."""

    @staticmethod
    def test_returns_logger_instance() -> None:
        """Should return a logging.Logger instance."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)

    @staticmethod
    def test_returns_logger_with_correct_name() -> None:
        """Should return logger with the specified name."""
        logger = get_logger("test.module")
        assert logger.name == "test.module"

    @staticmethod
    def test_returns_same_logger_for_same_name() -> None:
        """Should return same logger instance for same name."""
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        assert logger1 is logger2


class TestPipelineLogger:
    """Tests for PipelineLogger class."""

    @staticmethod
    def test_init_creates_logger_with_stage_name() -> None:
        """Should create logger with msc.pipeline prefix."""
        logger = PipelineLogger("extract")
        assert logger.stage_name == "extract"
        assert logger._logger.name == "msc.pipeline.extract"

    @staticmethod
    def test_info_logs_message() -> None:
        """Should log info message."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test message")
            mock_info.assert_called_once_with("test message")

    @staticmethod
    def test_info_logs_message_with_context() -> None:
        """Should log info message with context."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.info("test message", track="Song", count=5)
            mock_info.assert_called_once()
            call_arg = mock_info.call_args[0][0]
            assert "test message" in call_arg
            assert "track=Song" in call_arg
            assert "count=5" in call_arg

    @staticmethod
    def test_debug_logs_message() -> None:
        """Should log debug message."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "debug") as mock_debug:
            logger.debug("debug message")
            mock_debug.assert_called_once_with("debug message")

    @staticmethod
    def test_warning_logs_message() -> None:
        """Should log warning message."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "warning") as mock_warning:
            logger.warning("warning message")
            mock_warning.assert_called_once_with("warning message")

    @staticmethod
    def test_error_logs_message() -> None:
        """Should log error message."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "error") as mock_error:
            logger.error("error message")
            mock_error.assert_called_once_with("error message")

    @staticmethod
    def test_progress_logs_percentage() -> None:
        """Should log progress with percentage."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.progress(50, 100)
            mock_info.assert_called_once()
            call_arg = mock_info.call_args[0][0]
            assert "50/100" in call_arg
            assert "50.0%" in call_arg

    @staticmethod
    def test_progress_logs_with_item() -> None:
        """Should log progress with item description."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.progress(1, 10, item="Track Name")
            mock_info.assert_called_once()
            call_arg = mock_info.call_args[0][0]
            assert "Track Name" in call_arg

    @staticmethod
    def test_progress_handles_zero_total() -> None:
        """Should handle zero total without division error."""
        logger = PipelineLogger("test")
        with patch.object(logger._logger, "info") as mock_info:
            logger.progress(0, 0)
            mock_info.assert_called_once()
            call_arg = mock_info.call_args[0][0]
            assert "0.0%" in call_arg


class TestFormatMessage:
    """Tests for PipelineLogger._format_message static method."""

    @staticmethod
    def test_format_message_without_context() -> None:
        """Should return message unchanged when no context."""
        result = PipelineLogger._format_message("test", (), {})
        assert result == "test"

    @staticmethod
    def test_format_message_with_context() -> None:
        """Should format message with context."""
        result = PipelineLogger._format_message("test", (), {"key": "value", "num": 42})
        assert "test |" in result
        assert "key=value" in result
        assert "num=42" in result

    @staticmethod
    def test_format_message_with_args() -> None:
        """Should format message with positional args (lazy logging)."""
        result = PipelineLogger._format_message("Starting %s", ("TestStage",), {})
        assert result == "Starting TestStage"

    @staticmethod
    def test_format_message_with_multiple_args() -> None:
        """Should format message with multiple positional args."""
        result = PipelineLogger._format_message(
            "Stage %s failed: %s", ("Test", "error"), {}
        )
        assert result == "Stage Test failed: error"

    @staticmethod
    def test_format_message_with_args_and_context() -> None:
        """Should format message with both args and context."""
        result = PipelineLogger._format_message(
            "Processing %s", ("Track",), {"status": "ok"}
        )
        assert "Processing Track" in result
        assert "status=ok" in result

    @staticmethod
    def test_format_message_preserves_special_characters() -> None:
        """Should preserve special characters in message."""
        result = PipelineLogger._format_message("Test: 100%", (), {})
        assert result == "Test: 100%"

    @staticmethod
    @pytest.mark.parametrize(
        "message,args,context,expected_contains",
        [
            ("Simple", (), {}, ["Simple"]),
            ("With %s", ("arg",), {}, ["With arg"]),
            ("Multi %s %s", ("a", "b"), {}, ["Multi a b"]),
            ("Context", (), {"k": "v"}, ["Context", "k=v"]),
        ],
    )
    def test_format_message_parametrized(
            message: str,
            args: tuple,
            context: dict,
            expected_contains: list[str],
    ) -> None:
        """Should correctly format various message combinations."""
        result = PipelineLogger._format_message(message, args, context)
        for expected in expected_contains:
            assert expected in result
