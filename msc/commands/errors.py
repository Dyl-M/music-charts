"""CLI error handling infrastructure.

Provides custom exception classes and a centralized error handler registry
for generating helpful, multi-line error messages with suggestions.
"""

# Standard library
from typing import Callable


class CLIError(Exception):
    """Base exception for CLI-specific errors."""


class MissingAPIKeyError(CLIError):
    """Raised when Songstats API key is not found."""


class InvalidDataFileError(CLIError):
    """Raised when data file has invalid structure or content."""


class NetworkError(CLIError):
    """Raised when API requests fail due to network issues."""


class ErrorHandler:
    """Central error handler registry with decorator-based registration.

    Maps exception types to handler functions that generate
    helpful multi-line error messages with suggestions.
    """

    _HANDLERS: dict[type[Exception], Callable[[Exception], str]] = {}

    @classmethod
    def register(cls, exc_type: type[Exception]) -> Callable:
        """Decorator to register an error handler for an exception type.

        Args:
            exc_type: Exception type to handle

        Returns:
            Decorator function

        Example:
            @ErrorHandler.register(MissingAPIKeyError)
            def handle_missing_key(error: MissingAPIKeyError) -> str:
                return "Help text here..."
        """

        def decorator(handler: Callable[[Exception], str]) -> Callable:
            """Register handler function.

            Args:
                handler: Function that generates error message

            Returns:
                Original handler function
            """
            cls._HANDLERS[exc_type] = handler
            return handler

        return decorator

    @classmethod
    def handle(cls, error: Exception) -> str:
        """Get formatted help text for an error.

        Args:
            error: Exception to handle

        Returns:
            Formatted error message with suggestions
        """
        # Try exact match first
        handler = cls._HANDLERS.get(type(error))

        if handler:
            return handler(error)

        # Try parent classes
        for exc_type, handler in cls._HANDLERS.items():
            if isinstance(error, exc_type):
                return handler(error)

        # Fallback to generic handler
        return cls._format_generic_error(error)

    @staticmethod
    def _format_generic_error(error: Exception) -> str:
        """Format generic error message.

        Args:
            error: Exception to format

        Returns:
            Generic error message
        """
        return f"""
❌ Error: {error!s}

If this error persists, please check:
  • Your configuration in .env or environment variables
  • File paths and permissions
  • Network connectivity
  • API credentials validity

For more help, see: https://github.com/Dyl-M/music-charts
"""

    @staticmethod
    def format_multiline_help(
            error_msg: str,
            suggestions: list[str],
            docs_url: str | None = None,
    ) -> str:
        """Format error with suggestions and documentation links.

        Args:
            error_msg: Main error message
            suggestions: List of actionable suggestions
            docs_url: Optional documentation URL

        Returns:
            Formatted multi-line help text
        """
        lines = [f"\n❌ {error_msg}\n"]

        if suggestions:
            lines.append("Suggestions:")
            for i, suggestion in enumerate(suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        if docs_url:
            lines.append(f"\nDocumentation: {docs_url}")

        return "\n".join(lines)


# ============================================================================
# Register handlers for specific exception types
# ============================================================================


@ErrorHandler.register(MissingAPIKeyError)
def _handle_missing_api_key(_error: MissingAPIKeyError) -> str:
    """Handle missing Songstats API key error.

    Args:
        _error: MissingAPIKeyError exception

    Returns:
        Formatted help text
    """
    suggestions = [
        "Set environment variable: export MSC_SONGSTATS_API_KEY=your_key_here",
        "Create file: echo 'your_key' > _tokens/songstats_key.txt",
        "Add to .env file: MSC_SONGSTATS_API_KEY=your_key_here",
    ]

    return ErrorHandler.format_multiline_help(
        error_msg="Songstats API key not found",
        suggestions=suggestions,
        docs_url="https://github.com/Dyl-M/music-charts#configuration",
    )


@ErrorHandler.register(NetworkError)
def _handle_network_error(error: NetworkError) -> str:
    """Handle network-related API errors.

    Args:
        error: NetworkError exception

    Returns:
        Formatted help text
    """
    suggestions = [
        "Check your internet connection",
        "Verify API service status (https://status.songstats.com)",
        "Try again in a few moments",
        "Check firewall settings if behind corporate network",
    ]

    return ErrorHandler.format_multiline_help(
        error_msg=f"Network error: {error!s}",
        suggestions=suggestions,
        docs_url="https://github.com/Dyl-M/music-charts#troubleshooting",
    )


@ErrorHandler.register(InvalidDataFileError)
def _handle_invalid_data_file(error: InvalidDataFileError) -> str:
    """Handle invalid data file errors.

    Args:
        error: InvalidDataFileError exception

    Returns:
        Formatted help text
    """
    suggestions = [
        "Check file format - must be valid JSON",
        "Verify file encoding is UTF-8",
        "Run 'msc validate <file>' to see specific validation errors",
        "Compare with examples in _demos/ directory",
    ]

    return ErrorHandler.format_multiline_help(
        error_msg=f"Invalid data file: {error!s}",
        suggestions=suggestions,
        docs_url="https://github.com/Dyl-M/music-charts#data-formats",
    )


@ErrorHandler.register(FileNotFoundError)
def _handle_file_not_found(error: FileNotFoundError) -> str:
    """Handle file not found errors.

    Args:
        error: FileNotFoundError exception

    Returns:
        Formatted help text
    """
    suggestions = [
        "Verify the file path is correct",
        "Use absolute paths to avoid confusion",
        "Check file permissions",
        "Run 'msc init' to create directory structure",
    ]

    return ErrorHandler.format_multiline_help(
        error_msg=f"File not found: {error!s}",
        suggestions=suggestions,
    )


@ErrorHandler.register(ValueError)
def _handle_value_error(error: ValueError) -> str:
    """Handle value errors (e.g., configuration issues).

    Args:
        error: ValueError exception

    Returns:
        Formatted help text
    """
    # Check if it's an API key error
    if "API key" in str(error):
        return _handle_missing_api_key(MissingAPIKeyError(str(error)))

    suggestions = [
        "Check your configuration in .env file",
        "Verify environment variables are set correctly",
        "See .env.example for configuration template",
    ]

    return ErrorHandler.format_multiline_help(
        error_msg=f"Configuration error: {error!s}",
        suggestions=suggestions,
        docs_url="https://github.com/Dyl-M/music-charts#configuration",
    )
