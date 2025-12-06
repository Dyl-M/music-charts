# Standard library
import functools
import logging
from collections.abc import Callable
from typing import ParamSpec, TypeVar

# Third-party
import requests
from tenacity import (
    RetryError,
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

"""Retry utilities with exponential backoff for API calls."""

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def retry_with_backoff(
        max_retries: int = 3,
        min_wait: float = 1.0,
        max_wait: float = 60.0,
        retry_exceptions: tuple[type[Exception], ...] | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts.
        min_wait: Minimum wait time between retries in seconds.
        max_wait: Maximum wait time between retries in seconds.
        retry_exceptions: Tuple of exception types to retry on.
            Defaults to common network/API exceptions.

    Returns:
        Decorated function with retry logic.

    Example:
        @retry_with_backoff(max_retries=3)
        def call_api():
            return requests.get("https://api.example.com/data")
    """
    if retry_exceptions is None:
        retry_exceptions = (
            requests.exceptions.RequestException,
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            ConnectionError,
            TimeoutError,
        )

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @functools.wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            retryer = retry(
                stop=stop_after_attempt(max_retries),
                wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                retry=retry_if_exception_type(retry_exceptions),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )
            try:
                return retryer(func)(*args, **kwargs)
            except RetryError as e:
                logger.error(f"All {max_retries} retries failed for {func.__name__}: {e}")
                raise

        return wrapper

    return decorator


def is_retryable_status(status_code: int) -> bool:
    """Check if an HTTP status code should trigger a retry.

    Args:
        status_code: HTTP response status code.

    Returns:
        True if the request should be retried.
    """
    # Retry on server errors (5xx) and rate limiting (429)
    return status_code >= 500 or status_code == 429


class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""

    def __init__(self, requests_per_second: int = 10):
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum requests allowed per second.
        """
        import time

        self.requests_per_second = requests_per_second
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
        self._time = time

    def wait(self) -> None:
        """Wait if necessary to respect the rate limit."""
        current_time = self._time.time()
        elapsed = current_time - self.last_request_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            self._time.sleep(sleep_time)

        self.last_request_time = self._time.time()

    def __enter__(self) -> "RateLimiter":
        """Context manager entry - wait before proceeding."""
        self.wait()
        return self

    # TODO: Remove skipcq if cleanup logic is added
    def __exit__(self, *args: object) -> None:  # skipcq: PYL-R6301
        """Context manager exit."""
        pass
