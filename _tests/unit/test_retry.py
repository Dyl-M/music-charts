import pytest
import requests
import time

from tenacity import RetryError
from unittest.mock import MagicMock, patch

from msc.utils.retry import RateLimiter, is_retryable_status, retry_with_backoff

"""Unit tests for retry utilities."""


class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""

    @staticmethod
    def test_succeeds_on_first_attempt() -> None:
        """Should return result on successful first attempt."""

        @retry_with_backoff(max_retries=3)
        def always_succeeds() -> str:
            return "success"

        assert always_succeeds() == "success"

    @staticmethod
    def test_retries_on_exception() -> None:
        """Should retry on specified exceptions."""
        mock_func = MagicMock(
            side_effect=[requests.exceptions.ConnectionError(), requests.exceptions.ConnectionError(), "success"]
        )

        @retry_with_backoff(max_retries=3)
        def func_with_retries() -> str:
            return mock_func()

        result = func_with_retries()
        assert result == "success"
        assert mock_func.call_count == 3

    @staticmethod
    def test_raises_after_max_retries() -> None:
        """Should raise original exception after max attempts."""

        @retry_with_backoff(max_retries=2)
        def always_fails() -> None:
            raise requests.exceptions.ConnectionError("Network error")

        with pytest.raises(requests.exceptions.ConnectionError):
            always_fails()

    @staticmethod
    def test_uses_custom_retry_exceptions() -> None:
        """Should only retry on specified exception types."""

        @retry_with_backoff(max_retries=3, retry_exceptions=(ValueError,))
        def raises_value_error() -> None:
            raise ValueError("test")

        with pytest.raises(ValueError):
            raises_value_error()

    @staticmethod
    def test_does_not_retry_unlisted_exceptions() -> None:
        """Should not retry exceptions not in retry_exceptions list."""

        @retry_with_backoff(max_retries=3, retry_exceptions=(ValueError,))
        def raises_type_error() -> None:
            raise TypeError("test")

        with pytest.raises(TypeError):
            raises_type_error()

    @staticmethod
    def test_uses_default_retry_exceptions_when_none() -> None:
        """Should use default exceptions when none provided."""
        mock_func = MagicMock(side_effect=[TimeoutError(), "success"])

        @retry_with_backoff(max_retries=3)
        def func() -> str:
            return mock_func()

        result = func()
        assert result == "success"
        assert mock_func.call_count == 2


class TestIsRetryableStatus:
    """Tests for is_retryable_status function."""

    @staticmethod
    def test_retries_500_status() -> None:
        """Should retry on 500 Internal Server Error."""
        assert is_retryable_status(500) is True

    @staticmethod
    def test_retries_502_status() -> None:
        """Should retry on 502 Bad Gateway."""
        assert is_retryable_status(502) is True

    @staticmethod
    def test_retries_503_status() -> None:
        """Should retry on 503 Service Unavailable."""
        assert is_retryable_status(503) is True

    @staticmethod
    def test_retries_429_status() -> None:
        """Should retry on 429 Too Many Requests."""
        assert is_retryable_status(429) is True

    @staticmethod
    def test_does_not_retry_200_status() -> None:
        """Should not retry on 200 OK."""
        assert is_retryable_status(200) is False

    @staticmethod
    def test_does_not_retry_404_status() -> None:
        """Should not retry on 404 Not Found."""
        assert is_retryable_status(404) is False

    @staticmethod
    def test_does_not_retry_400_status() -> None:
        """Should not retry on 400 Bad Request."""
        assert is_retryable_status(400) is False


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @staticmethod
    def test_init_sets_requests_per_second() -> None:
        """Should set requests per second."""
        limiter = RateLimiter(requests_per_second=5)
        assert limiter.requests_per_second == 5

    @staticmethod
    def test_init_calculates_min_interval() -> None:
        """Should calculate minimum interval between requests."""
        limiter = RateLimiter(requests_per_second=10)
        assert limiter.min_interval == 0.1

    @staticmethod
    def test_init_sets_last_request_time() -> None:
        """Should initialize last_request_time to zero."""
        limiter = RateLimiter()
        assert limiter.last_request_time == 0.0

    @staticmethod
    def test_wait_sleeps_when_too_fast() -> None:
        """Should sleep when requests are too fast."""
        limiter = RateLimiter(requests_per_second=10)
        limiter.last_request_time = time.time() - 0.05  # 50ms ago

        with patch.object(limiter._time, "sleep") as mock_sleep:
            limiter.wait()
            mock_sleep.assert_called_once()
            sleep_time = mock_sleep.call_args[0][0]
            assert 0.04 < sleep_time < 0.06  # Should sleep ~50ms

    @staticmethod
    def test_wait_does_not_sleep_when_interval_passed() -> None:
        """Should not sleep when enough time has passed."""
        limiter = RateLimiter(requests_per_second=10)
        limiter.last_request_time = time.time() - 0.2  # 200ms ago

        with patch.object(limiter._time, "sleep") as mock_sleep:
            limiter.wait()
            mock_sleep.assert_not_called()

    @staticmethod
    def test_wait_updates_last_request_time() -> None:
        """Should update last_request_time after waiting."""
        limiter = RateLimiter()
        before = time.time()
        limiter.wait()
        after = time.time()

        assert limiter.last_request_time >= before
        assert limiter.last_request_time <= after

    @staticmethod
    def test_context_manager_waits_on_enter() -> None:
        """Should call wait() when entering context."""
        limiter = RateLimiter()

        with patch.object(limiter, "wait") as mock_wait:
            with limiter:
                mock_wait.assert_called_once()

    @staticmethod
    def test_context_manager_returns_self() -> None:
        """Should return self from __enter__."""
        limiter = RateLimiter()
        with limiter as result:
            assert result is limiter

    @staticmethod
    def test_context_manager_exit_completes() -> None:
        """Should complete __exit__ without errors."""
        limiter = RateLimiter()
        with limiter:
            pass  # Should not raise
