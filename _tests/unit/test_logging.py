import logging
import pytest

from unittest.mock import patch

from msc.utils.logging import PipelineLogger, get_logger, setup_logging

"""Unit tests for logging utilities."""


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
        assert "%(asctime)s" in handler.formatter._fmt  # type: ignore

    @staticmethod
    def test_uses_custom_format() -> None:
        """Should use custom format string when provided."""
        custom_format = "%(message)s"
        setup_logging(format_string=custom_format)
        handler = logging.getLogger().handlers[0]
        assert handler.formatter._fmt == custom_format  # type: ignore

    @staticmethod
    def test_reduces_third_party_noise() -> None:
        """Should set third-party loggers to WARNING level."""
        setup_logging()
        assert logging.getLogger("urllib3").level == logging.WARNING
        assert logging.getLogger("requests").level == logging.WARNING
        assert logging.getLogger("google").level == logging.WARNING


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

    @staticmethod
    def test_format_message_without_context() -> None:
        """Should return message unchanged when no context."""
        result = PipelineLogger._format_message("test", {})
        assert result == "test"

    @staticmethod
    def test_format_message_with_context() -> None:
        """Should format message with context."""
        result = PipelineLogger._format_message("test", {"key": "value", "num": 42})
        assert "test |" in result
        assert "key=value" in result
        assert "num=42" in result
