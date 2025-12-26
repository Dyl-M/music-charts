"""Unit tests for CLI error handling infrastructure.

Tests custom exception classes and ErrorHandler registry.
"""

# Third-party
import pytest

# Local
from msc.commands.errors import (
    CLIError,
    MissingAPIKeyError,
    InvalidDataFileError,
    NetworkError,
    ErrorHandler,
)


class TestCLIErrorHierarchy:
    """Tests for CLI exception class hierarchy."""

    @staticmethod
    def test_cli_error_is_exception() -> None:
        """Should inherit from Exception."""
        assert issubclass(CLIError, Exception)

    @staticmethod
    def test_missing_api_key_is_cli_error() -> None:
        """MissingAPIKeyError should inherit from CLIError."""
        assert issubclass(MissingAPIKeyError, CLIError)

    @staticmethod
    def test_invalid_data_file_is_cli_error() -> None:
        """InvalidDataFileError should inherit from CLIError."""
        assert issubclass(InvalidDataFileError, CLIError)

    @staticmethod
    def test_network_error_is_cli_error() -> None:
        """NetworkError should inherit from CLIError."""
        assert issubclass(NetworkError, CLIError)

    @staticmethod
    def test_can_raise_cli_error() -> None:
        """Should be able to raise CLIError."""
        with pytest.raises(CLIError, match="test error"):
            raise CLIError("test error")

    @staticmethod
    def test_can_raise_missing_api_key() -> None:
        """Should be able to raise MissingAPIKeyError."""
        with pytest.raises(MissingAPIKeyError, match="key not found"):
            raise MissingAPIKeyError("key not found")

    @staticmethod
    def test_can_raise_invalid_data_file() -> None:
        """Should be able to raise InvalidDataFileError."""
        with pytest.raises(InvalidDataFileError, match="invalid format"):
            raise InvalidDataFileError("invalid format")

    @staticmethod
    def test_can_raise_network_error() -> None:
        """Should be able to raise NetworkError."""
        with pytest.raises(NetworkError, match="connection failed"):
            raise NetworkError("connection failed")


class TestErrorHandlerRegister:
    """Tests for ErrorHandler.register decorator."""

    @staticmethod
    def test_registers_handler() -> None:
        """Should register handler for exception type."""

        class CustomError(Exception):
            """Custom test error."""

        @ErrorHandler.register(CustomError)
        def handle_custom(_e: CustomError) -> str:
            """Handle custom error."""
            return "custom handler"

        assert CustomError in ErrorHandler._HANDLERS
        assert ErrorHandler._HANDLERS[CustomError](_e=CustomError()) == "custom handler"

    @staticmethod
    def test_decorator_returns_original_function() -> None:
        """Decorator should return original handler function."""

        class TestError(Exception):
            """Test error."""

        @ErrorHandler.register(TestError)
        def my_handler(_e: TestError) -> str:
            """Test handler."""
            return "test"

        assert callable(my_handler)
        assert my_handler(TestError()) == "test"


class TestErrorHandlerHandle:
    """Tests for ErrorHandler.handle method."""

    @staticmethod
    def test_handles_registered_exception() -> None:
        """Should use registered handler for exact match."""
        result = ErrorHandler.handle(MissingAPIKeyError())
        assert "Songstats API key not found" in result

    @staticmethod
    def test_handles_network_error() -> None:
        """Should handle NetworkError with suggestions."""
        result = ErrorHandler.handle(NetworkError("timeout"))
        assert "Network error" in result
        assert "internet connection" in result.lower()

    @staticmethod
    def test_handles_invalid_data_file() -> None:
        """Should handle InvalidDataFileError with suggestions."""
        result = ErrorHandler.handle(InvalidDataFileError("corrupt"))
        assert "Invalid data file" in result
        assert "JSON" in result

    @staticmethod
    def test_handles_file_not_found() -> None:
        """Should handle FileNotFoundError."""
        result = ErrorHandler.handle(FileNotFoundError("missing.txt"))
        assert "File not found" in result

    @staticmethod
    def test_handles_value_error() -> None:
        """Should handle ValueError."""
        result = ErrorHandler.handle(ValueError("bad config"))
        assert "Configuration error" in result

    @staticmethod
    def test_handles_value_error_with_api_key() -> None:
        """Should redirect API key ValueErrors to API key handler."""
        result = ErrorHandler.handle(ValueError("API key missing"))
        assert "Songstats API key" in result

    @staticmethod
    def test_handles_parent_class() -> None:
        """Should use handler for parent exception class."""
        # NetworkError is a CLIError subclass
        result = ErrorHandler.handle(NetworkError("test"))
        assert "Network error" in result

    @staticmethod
    def test_generic_fallback() -> None:
        """Should use generic handler for unknown exceptions."""

        class UnknownError(Exception):
            """Unknown error type."""

        result = ErrorHandler.handle(UnknownError("unknown"))
        assert "Error:" in result
        assert "configuration" in result.lower()


class TestErrorHandlerFormatGenericError:
    """Tests for ErrorHandler._format_generic_error method."""

    @staticmethod
    def test_includes_error_message() -> None:
        """Should include error message in output."""
        error = Exception("specific error message")
        result = ErrorHandler._format_generic_error(error)
        assert "specific error message" in result

    @staticmethod
    def test_includes_help_suggestions() -> None:
        """Should include help suggestions."""
        error = Exception("test")
        result = ErrorHandler._format_generic_error(error)
        assert "configuration" in result.lower()
        assert "file paths" in result.lower()
        assert "network connectivity" in result.lower()

    @staticmethod
    def test_includes_github_link() -> None:
        """Should include GitHub link for help."""
        error = Exception("test")
        result = ErrorHandler._format_generic_error(error)
        assert "github.com" in result.lower()


class TestErrorHandlerFormatMultilineHelp:
    """Tests for ErrorHandler.format_multiline_help method."""

    @staticmethod
    def test_includes_error_message() -> None:
        """Should include error message with emoji."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Test error",
            suggestions=[],
        )
        assert "❌" in result
        assert "Test error" in result

    @staticmethod
    def test_formats_suggestions() -> None:
        """Should format suggestions as numbered list."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Error",
            suggestions=["First suggestion", "Second suggestion"],
        )
        assert "1. First suggestion" in result
        assert "2. Second suggestion" in result

    @staticmethod
    def test_includes_suggestions_header() -> None:
        """Should include 'Suggestions:' header when suggestions provided."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Error",
            suggestions=["Do this"],
        )
        assert "Suggestions:" in result

    @staticmethod
    def test_no_suggestions_header_when_empty() -> None:
        """Should not include 'Suggestions:' header when no suggestions."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Error",
            suggestions=[],
        )
        assert "Suggestions:" not in result

    @staticmethod
    def test_includes_docs_url() -> None:
        """Should include documentation URL when provided."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Error",
            suggestions=[],
            docs_url="https://example.com/docs",
        )
        assert "Documentation:" in result
        assert "https://example.com/docs" in result

    @staticmethod
    def test_no_docs_url_when_none() -> None:
        """Should not include Documentation line when no URL."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Error",
            suggestions=[],
            docs_url=None,
        )
        assert "Documentation:" not in result

    @staticmethod
    def test_full_message_formatting() -> None:
        """Should format complete help message correctly."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Connection failed",
            suggestions=["Check network", "Retry later"],
            docs_url="https://docs.example.com",
        )
        assert "❌ Connection failed" in result
        assert "Suggestions:" in result
        assert "1. Check network" in result
        assert "2. Retry later" in result
        assert "https://docs.example.com" in result


class TestRegisteredHandlers:
    """Tests for pre-registered error handlers."""

    @staticmethod
    def test_missing_api_key_handler() -> None:
        """Missing API key handler should provide setup instructions."""
        error = MissingAPIKeyError()
        result = ErrorHandler.handle(error)
        assert "MSC_SONGSTATS_API_KEY" in result
        assert "_tokens/songstats_key.txt" in result

    @staticmethod
    def test_network_error_handler() -> None:
        """Network error handler should suggest troubleshooting steps."""
        error = NetworkError("timeout")
        result = ErrorHandler.handle(error)
        assert "internet connection" in result.lower()
        assert "firewall" in result.lower()

    @staticmethod
    def test_invalid_data_file_handler() -> None:
        """Invalid data file handler should suggest validation."""
        error = InvalidDataFileError("corrupt data")
        result = ErrorHandler.handle(error)
        assert "msc validate" in result
        assert "UTF-8" in result

    @staticmethod
    def test_file_not_found_handler() -> None:
        """File not found handler should suggest msc init."""
        error = FileNotFoundError("missing.json")
        result = ErrorHandler.handle(error)
        assert "msc init" in result
        assert "absolute paths" in result.lower()
