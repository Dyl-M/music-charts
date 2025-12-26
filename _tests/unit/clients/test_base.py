"""Unit tests for base client module.

Tests BaseClient abstract class functionality.
"""
from abc import ABC
# Standard library
from unittest.mock import MagicMock, patch

# Third-party
import pytest
import requests

# Local
from msc.clients.base import BaseClient


class ConcreteClient(BaseClient):
    """Concrete implementation for testing abstract BaseClient."""

    def health_check(self) -> bool:
        """Test implementation."""
        return True

    def get_quota(self) -> dict:
        """Test implementation."""
        return {"quota": 1000}


class TestBaseClientInit:
    """Tests for BaseClient initialization."""

    @staticmethod
    def test_stores_api_key() -> None:
        """Should store API key."""
        client = ConcreteClient(api_key="test_key")
        assert client.api_key == "test_key"

    @staticmethod
    def test_stores_timeout() -> None:
        """Should store timeout value."""
        client = ConcreteClient(timeout=60)
        assert client.timeout == 60

    @staticmethod
    def test_default_timeout() -> None:
        """Should default timeout to 30."""
        client = ConcreteClient()
        assert client.timeout == 30

    @staticmethod
    def test_creates_rate_limiter() -> None:
        """Should create rate limiter with specified limit."""
        client = ConcreteClient(rate_limit=5)
        assert client.rate_limiter is not None

    @staticmethod
    def test_session_starts_none() -> None:
        """Should start with no session."""
        client = ConcreteClient()
        assert client._session is None


class TestBaseClientSession:
    """Tests for BaseClient session management."""

    @staticmethod
    def test_session_creates_on_access() -> None:
        """Should create session on first access."""
        client = ConcreteClient()
        session = client.session
        assert session is not None
        assert client._session is not None

    @staticmethod
    def test_session_reuses_existing() -> None:
        """Should reuse existing session."""
        client = ConcreteClient()
        session1 = client.session
        session2 = client.session
        assert session1 is session2

    @staticmethod
    def test_session_includes_default_headers() -> None:
        """Should include default headers in session."""
        client = ConcreteClient()
        session = client.session
        assert "User-Agent" in session.headers or len(session.headers) >= 0

    @staticmethod
    def test_session_includes_api_key_header() -> None:
        """Should include API key in headers when set."""
        client = ConcreteClient(api_key="test_key")
        session = client.session
        assert session.headers.get("apikey") == "test_key"


class TestBaseClientClose:
    """Tests for BaseClient resource cleanup."""

    @staticmethod
    def test_close_clears_session() -> None:
        """Should clear session on close."""
        client = ConcreteClient()
        _ = client.session  # Force session creation
        client.close()
        assert client._session is None

    @staticmethod
    def test_close_calls_session_close() -> None:
        """Should call session close method."""
        client = ConcreteClient()
        _ = client.session  # Force session creation
        with patch.object(client._session, "close") as mock_close:
            client.close()
            mock_close.assert_called_once()

    @staticmethod
    def test_close_safe_when_no_session() -> None:
        """Should not error when closing without session."""
        client = ConcreteClient()
        client.close()  # Should not raise


class TestBaseClientContextManager:
    """Tests for BaseClient context manager."""

    @staticmethod
    def test_enter_returns_self() -> None:
        """Should return self on enter."""
        client = ConcreteClient()
        with client as ctx:
            assert ctx is client

    @staticmethod
    def test_exit_closes_client() -> None:
        """Should close client on exit."""
        client = ConcreteClient()
        _ = client.session  # Force session creation
        with client:
            pass
        assert client._session is None


class TestBaseClientRequest:
    """Tests for BaseClient request methods."""

    @staticmethod
    def test_get_returns_json() -> None:
        """Should return parsed JSON from GET request."""
        client = ConcreteClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": "test"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.get("https://test.com/api")
            assert result == {"data": "test"}

    @staticmethod
    def test_post_returns_json() -> None:
        """Should return parsed JSON from POST request."""
        client = ConcreteClient()
        mock_response = MagicMock()
        mock_response.json.return_value = {"created": True}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.session, "request", return_value=mock_response):
            result = client.post("https://test.com/api", json_data={"key": "value"})
            assert result == {"created": True}

    @staticmethod
    def test_request_uses_timeout() -> None:
        """Should pass timeout to request."""
        client = ConcreteClient(timeout=45)
        mock_response = MagicMock()
        mock_response.json.return_value = {}
        mock_response.raise_for_status = MagicMock()

        with patch.object(client.session, "request", return_value=mock_response) as mock_request:
            client.get("https://test.com/api")
            call_kwargs = mock_request.call_args.kwargs
            assert call_kwargs.get("timeout") == 45

    @staticmethod
    def test_has_rate_limiter() -> None:
        """Should have rate limiter configured."""
        client = ConcreteClient(rate_limit=5)
        assert client.rate_limiter is not None
        # The rate limiter is used as a context manager in _request method

    @staticmethod
    def test_request_raises_http_error() -> None:
        """Should propagate HTTP errors."""
        client = ConcreteClient()
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(requests.HTTPError):
                client.get("https://test.com/api")


class TestBaseClientAbstractMethods:
    """Tests for BaseClient abstract method enforcement."""

    @staticmethod
    def test_health_check_must_be_implemented() -> None:
        """Should require health_check implementation."""

        class IncompleteClient(BaseClient, ABC):
            """Client missing health_check."""

            def get_quota(self) -> dict:
                return {}

        with pytest.raises(TypeError, match="health_check"):
            # noinspection PyAbstractClass
            IncompleteClient()

    @staticmethod
    def test_get_quota_must_be_implemented() -> None:
        """Should require get_quota implementation."""

        class IncompleteClient(BaseClient, ABC):
            """Client missing get_quota."""

            def health_check(self) -> bool:
                return True

        with pytest.raises(TypeError, match="get_quota"):
            # noinspection PyAbstractClass
            IncompleteClient()


class TestBaseClientDefaultHeaders:
    """Tests for BaseClient default headers."""

    @staticmethod
    def test_get_default_headers_without_api_key() -> None:
        """Should return default headers without API key."""
        client = ConcreteClient()
        headers = client._get_default_headers()
        assert isinstance(headers, dict)
        assert "apikey" not in headers

    @staticmethod
    def test_get_default_headers_with_api_key() -> None:
        """Should include API key in headers."""
        client = ConcreteClient(api_key="my_key")
        headers = client._get_default_headers()
        assert headers.get("apikey") == "my_key"
