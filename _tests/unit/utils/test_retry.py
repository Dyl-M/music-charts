"""Unit tests for retry utilities.

Tests retry_with_backoff decorator, is_retryable_status function,
and RateLimiter class.
"""

# Standard library
import time
from unittest.mock import MagicMock

# Third-party
import pytest
import requests

# Local
from msc.utils.retry import RateLimiter, is_retryable_status, retry_with_backoff


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    @staticmethod
    def test_returns_result_on_success() -> None:
        """Should return result when function succeeds."""

        @retry_with_backoff(max_retries=3)
        def successful_func() -> str:
            """Return success message."""
            return "success"

        result = successful_func()
        assert result == "success"

    @staticmethod
    def test_retries_on_connection_error() -> None:
        """Should retry on ConnectionError."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_wait=0.01, max_wait=0.1)
        def flaky_func() -> str:
            """Fail twice then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection failed")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 3

    @staticmethod
    def test_retries_on_timeout_error() -> None:
        """Should retry on TimeoutError."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_wait=0.01, max_wait=0.1)
        def timeout_func() -> str:
            """Fail once then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise TimeoutError("Timeout")
            return "success"

        result = timeout_func()
        assert result == "success"
        assert call_count == 2

    @staticmethod
    def test_retries_on_requests_exception() -> None:
        """Should retry on requests exceptions."""
        call_count = 0

        @retry_with_backoff(max_retries=3, min_wait=0.01, max_wait=0.1)
        def request_func() -> str:
            """Fail once then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise requests.exceptions.ConnectionError("Network error")
            return "success"

        result = request_func()
        assert result == "success"

    @staticmethod
    def test_raises_after_max_retries() -> None:
        """Should raise exception after max retries exhausted."""

        @retry_with_backoff(max_retries=2, min_wait=0.01, max_wait=0.1)
        def always_fails() -> None:
            """Always raise exception."""
            raise ConnectionError("Always fails")

        with pytest.raises(ConnectionError, match="Always fails"):
            always_fails()

    @staticmethod
    def test_does_not_retry_on_unspecified_exception() -> None:
        """Should not retry on exceptions not in retry list."""

        @retry_with_backoff(max_retries=3)
        def value_error_func() -> None:
            """Raise ValueError which is not retried."""
            raise ValueError("Not retryable")

        with pytest.raises(ValueError, match="Not retryable"):
            value_error_func()

    @staticmethod
    def test_custom_retry_exceptions() -> None:
        """Should retry on custom exception types."""
        call_count = 0

        @retry_with_backoff(
            max_retries=3,
            min_wait=0.01,
            max_wait=0.1,
            retry_exceptions=(ValueError,),
        )
        def custom_exception_func() -> str:
            """Fail once with ValueError then succeed."""
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("Retryable value error")
            return "success"

        result = custom_exception_func()
        assert result == "success"

    @staticmethod
    def test_preserves_function_metadata() -> None:
        """Should preserve wrapped function's metadata."""

        @retry_with_backoff()
        def documented_func() -> None:
            """This is the docstring."""
            ...

        assert documented_func.__name__ == "documented_func"
        assert "docstring" in documented_func.__doc__


class TestIsRetryableStatus:
    """Tests for is_retryable_status function."""

    @staticmethod
    @pytest.mark.parametrize(
        "status_code,expected",
        [
            (200, False),
            (201, False),
            (400, False),
            (401, False),
            (403, False),
            (404, False),
            (429, True),  # Rate limit
            (500, True),  # Server error
            (502, True),  # Bad gateway
            (503, True),  # Service unavailable
            (504, True),  # Gateway timeout
        ],
    )
    def test_status_code_retryability(status_code: int, expected: bool) -> None:
        """Should correctly identify retryable status codes."""
        result = is_retryable_status(status_code)
        assert result == expected

    @staticmethod
    def test_rate_limit_429_is_retryable() -> None:
        """Should mark 429 as retryable."""
        assert is_retryable_status(429) is True

    @staticmethod
    def test_server_error_500_is_retryable() -> None:
        """Should mark 500+ as retryable."""
        assert is_retryable_status(500) is True
        assert is_retryable_status(503) is True

    @staticmethod
    def test_client_error_is_not_retryable() -> None:
        """Should not retry client errors except 429."""
        assert is_retryable_status(400) is False
        assert is_retryable_status(404) is False


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @staticmethod
    def test_init_sets_requests_per_second() -> None:
        """Should initialize with correct requests per second."""
        limiter = RateLimiter(requests_per_second=5)
        assert limiter.requests_per_second == 5
        assert limiter.min_interval == 0.2

    @staticmethod
    def test_default_requests_per_second() -> None:
        """Should default to 10 requests per second."""
        limiter = RateLimiter()
        assert limiter.requests_per_second == 10
        assert limiter.min_interval == 0.1

    @staticmethod
    def test_wait_allows_immediate_first_request() -> None:
        """Should allow first request immediately."""
        limiter = RateLimiter(requests_per_second=10)
        limiter.last_request_time = 0.0

        start = time.time()
        limiter.wait()
        elapsed = time.time() - start

        # First request should be nearly immediate
        assert elapsed < 0.1

    @staticmethod
    def test_wait_delays_rapid_requests() -> None:
        """Should delay requests that come too quickly."""
        mock_time = MagicMock()
        mock_time.time.side_effect = [0.0, 0.05, 0.1]  # Simulated times
        mock_time.sleep = MagicMock()

        limiter = RateLimiter(requests_per_second=10)
        limiter._time = mock_time
        limiter.last_request_time = 0.0

        # Second call at 0.05s (need 0.1s interval)
        mock_time.time.side_effect = [0.05, 0.1]
        limiter.wait()

        # Should have slept for ~0.05s
        mock_time.sleep.assert_called()

    @staticmethod
    def test_context_manager_entry() -> None:
        """Should call wait on context manager entry."""
        limiter = RateLimiter(requests_per_second=10)
        limiter.wait = MagicMock()

        with limiter:
            pass

        limiter.wait.assert_called_once()

    @staticmethod
    def test_context_manager_returns_self() -> None:
        """Should return self from context manager."""
        limiter = RateLimiter(requests_per_second=10)

        with limiter as context:
            assert context is limiter

    @staticmethod
    def test_multiple_requests_respect_rate() -> None:
        """Should space out multiple requests."""
        limiter = RateLimiter(requests_per_second=100)  # Fast for testing

        start = time.time()
        for _ in range(3):
            limiter.wait()
        elapsed = time.time() - start

        # Should take at least 2 * min_interval for 3 requests
        assert elapsed >= 0.02  # 2 * 0.01s

    @staticmethod
    def test_exit_does_nothing() -> None:
        """Should not raise on context manager exit."""
        limiter = RateLimiter()

        # Should not raise
        limiter.__exit__(None, None, None)
