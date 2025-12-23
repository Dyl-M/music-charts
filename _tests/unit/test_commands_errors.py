"""Unit tests for CLI error handlers."""

# Local
from msc.commands.errors import (
    CLIError,
    ErrorHandler,
    InvalidDataFileError,
    MissingAPIKeyError,
    NetworkError,
)


class TestCustomExceptions:
    """Tests for custom exception classes."""

    @staticmethod
    def test_cli_error_is_exception() -> None:
        """Should be a standard Exception subclass."""
        error = CLIError("test error")

        assert isinstance(error, Exception)
        assert str(error) == "test error"

    @staticmethod
    def test_missing_api_key_error() -> None:
        """Should create MissingAPIKeyError."""
        error = MissingAPIKeyError("API key not found")

        assert isinstance(error, CLIError)
        assert str(error) == "API key not found"

    @staticmethod
    def test_invalid_data_file_error() -> None:
        """Should create InvalidDataFileError."""
        error = InvalidDataFileError("Invalid JSON")

        assert isinstance(error, CLIError)
        assert str(error) == "Invalid JSON"

    @staticmethod
    def test_network_error() -> None:
        """Should create NetworkError."""
        error = NetworkError("Connection failed")

        assert isinstance(error, CLIError)
        assert str(error) == "Connection failed"


class TestErrorHandlerRegistry:
    """Tests for error handler registration."""

    @staticmethod
    def test_register_handler() -> None:
        """Should register custom error handler."""
        # Define custom exception
        class CustomError(Exception):
            pass

        # Register handler
        @ErrorHandler.register(CustomError)
        def handle_custom(_error: CustomError) -> str:
            """Handle custom error."""
            return "Custom error handled"

        # Test handler is registered
        error = CustomError("test")
        result = ErrorHandler.handle(error)

        assert "Custom error handled" in result

    @staticmethod
    def test_handler_returns_original_function() -> None:
        """Should return the original handler function after registration."""

        class TestError(Exception):
            pass

        @ErrorHandler.register(TestError)
        def my_handler(_error: TestError) -> str:
            """Test handler."""
            return "handled"

        # Handler should still be callable
        assert callable(my_handler)
        assert my_handler(TestError()) == "handled"


class TestErrorHandlerHandle:
    """Tests for error handling."""

    @staticmethod
    def test_handle_missing_api_key_error() -> None:
        """Should handle MissingAPIKeyError with helpful message."""
        error = MissingAPIKeyError("Key not found")
        result = ErrorHandler.handle(error)

        assert "Songstats API key not found" in result
        assert "MSC_SONGSTATS_API_KEY" in result
        assert "Suggestions:" in result

    @staticmethod
    def test_handle_network_error() -> None:
        """Should handle NetworkError with helpful message."""
        error = NetworkError("Connection timeout")
        result = ErrorHandler.handle(error)

        assert "Network error" in result
        assert "Connection timeout" in result
        assert "internet connection" in result

    @staticmethod
    def test_handle_invalid_data_file_error() -> None:
        """Should handle InvalidDataFileError."""
        error = InvalidDataFileError("Malformed JSON")
        result = ErrorHandler.handle(error)

        assert "Invalid data file" in result
        assert "Malformed JSON" in result
        assert "valid JSON" in result

    @staticmethod
    def test_handle_file_not_found_error() -> None:
        """Should handle FileNotFoundError."""
        error = FileNotFoundError("test.json")
        result = ErrorHandler.handle(error)

        assert "File not found" in result
        assert "test.json" in result

    @staticmethod
    def test_handle_value_error_with_api_key() -> None:
        """Should detect API key errors in ValueError."""
        error = ValueError("API key is required")
        result = ErrorHandler.handle(error)

        assert "Songstats API key not found" in result

    @staticmethod
    def test_handle_generic_value_error() -> None:
        """Should handle generic ValueError."""
        error = ValueError("Invalid configuration")
        result = ErrorHandler.handle(error)

        assert "Configuration error" in result
        assert "Invalid configuration" in result

    @staticmethod
    def test_handle_unknown_error_type() -> None:
        """Should provide generic help for unknown errors."""

        class UnknownError(Exception):
            pass

        error = UnknownError("Something went wrong")
        result = ErrorHandler.handle(error)

        assert "Error: Something went wrong" in result
        assert "configuration" in result.lower()


class TestErrorHandlerFormatMultilineHelp:
    """Tests for multiline help formatting."""

    @staticmethod
    def test_format_with_suggestions() -> None:
        """Should format error with suggestions."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Test error occurred",
            suggestions=["Try this", "Or try that"],
        )

        assert "Test error occurred" in result
        assert "Suggestions:" in result
        assert "1. Try this" in result
        assert "2. Or try that" in result

    @staticmethod
    def test_format_with_docs_url() -> None:
        """Should include documentation URL."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Test error",
            suggestions=[],
            docs_url="https://example.com/docs",
        )

        assert "Documentation: https://example.com/docs" in result

    @staticmethod
    def test_format_minimal() -> None:
        """Should work with minimal arguments."""
        result = ErrorHandler.format_multiline_help(
            error_msg="Simple error",
            suggestions=[],
        )

        assert "Simple error" in result
