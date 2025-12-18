"""Unit tests for BaseClient abstract class."""

# Standard library
from typing import Any
from unittest.mock import MagicMock, Mock, patch

# Third-party
import pytest
import requests

# Local
from msc.clients.base import BaseClient
from msc.config.constants import DEFAULT_HEADERS


class ConcreteClient(BaseClient):
    """Concrete implementation of BaseClient for testing."""

    def health_check(self) -> bool:
        """Mock health check implementation."""
        return True

    def get_quota(self) -> dict[str, Any]:
        """Mock quota implementation."""
        return {"limit": 1000, "used": 100}


class TestBaseClientInit:
    """Tests for BaseClient initialization."""

    @staticmethod
    def test_init_with_defaults() -> None:
        """Should initialize with default values."""
        client = ConcreteClient()

        assert client.api_key is None
        assert client.timeout == 30
        assert client.rate_limiter.requests_per_second == 10
        assert client._session is None

    @staticmethod
    def test_init_with_custom_values() -> None:
        """Should initialize with custom values."""
        client = ConcreteClient(api_key="test_key", rate_limit=5, timeout=60)

        assert client.api_key == "test_key"
        assert client.timeout == 60
        assert client.rate_limiter.requests_per_second == 5


class TestSessionProperty:
    """Tests for the session property."""

    @staticmethod
    def test_session_lazy_initialization() -> None:
        """Should create session on first access."""
        client = ConcreteClient()

        assert client._session is None
        session = client.session
        assert session is not None
        assert isinstance(session, requests.Session)

    @staticmethod
    def test_session_returns_same_instance() -> None:
        """Should return the same session instance."""
        client = ConcreteClient()

        session1 = client.session
        session2 = client.session
        assert session1 is session2

    @staticmethod
    def test_session_sets_default_headers() -> None:
        """Should set default headers on session."""
        client = ConcreteClient(api_key="test_key")

        session = client.session
        assert "User-Agent" in session.headers
        assert session.headers["apikey"] == "test_key"


class TestGetDefaultHeaders:
    """Tests for _get_default_headers method."""

    @staticmethod
    def test_includes_default_headers() -> None:
        """Should include default headers from constants."""
        client = ConcreteClient()

        headers = client._get_default_headers()
        for key, value in DEFAULT_HEADERS.items():
            assert headers[key] == value

    @staticmethod
    def test_adds_api_key_when_present() -> None:
        """Should add apikey header when API key is set."""
        client = ConcreteClient(api_key="test_key")

        headers = client._get_default_headers()
        assert headers["apikey"] == "test_key"

    @staticmethod
    def test_no_api_key_when_none() -> None:
        """Should not add apikey header when API key is None."""
        client = ConcreteClient()

        headers = client._get_default_headers()
        assert "apikey" not in headers


class TestPostMethod:
    """Tests for the post() method."""

    @staticmethod
    def test_post_success() -> None:
        """Should make POST request and return JSON."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.json.return_value = {"status": "success", "id": 123}

        with patch.object(client, "_request", return_value=mock_response) as mock_request:
            result = client.post("https://api.example.com/resource", json_data={"name": "test"})

            mock_request.assert_called_once_with(
                "POST",
                "https://api.example.com/resource",
                params=None,
                json_data={"name": "test"}
            )
            assert result == {"status": "success", "id": 123}

    @staticmethod
    def test_post_with_params() -> None:
        """Should make POST request with query parameters."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.json.return_value = {"created": True}

        with patch.object(client, "_request", return_value=mock_response) as mock_request:
            result = client.post(
                "https://api.example.com/resource",
                json_data={"name": "test"},
                params={"key": "value"}
            )

            mock_request.assert_called_once_with(
                "POST",
                "https://api.example.com/resource",
                params={"key": "value"},
                json_data={"name": "test"}
            )
            assert result == {"created": True}

    @staticmethod
    def test_post_without_json_data() -> None:
        """Should make POST request without body."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}

        with patch.object(client, "_request", return_value=mock_response) as mock_request:
            result = client.post("https://api.example.com/action")

            mock_request.assert_called_once_with(
                "POST",
                "https://api.example.com/action",
                params=None,
                json_data=None
            )
            assert result == {"ok": True}


class TestGetMethod:
    """Tests for the get() method."""

    @staticmethod
    def test_get_success() -> None:
        """Should make GET request and return JSON."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.json.return_value = {"data": "value"}

        with patch.object(client, "_request", return_value=mock_response) as mock_request:
            result = client.get("https://api.example.com/resource")

            mock_request.assert_called_once_with("GET", "https://api.example.com/resource", params=None)
            assert result == {"data": "value"}


class TestRequestMethod:
    """Tests for the _request() method."""

    @staticmethod
    def test_request_with_rate_limiting() -> None:
        """Should apply rate limiting before request."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.status_code = 200

        with patch.object(client.session, "request", return_value=mock_response), \
                patch.object(client.rate_limiter, "wait") as mock_wait:
            client._request("GET", "https://api.example.com/test")

            mock_wait.assert_called_once()

    @staticmethod
    def test_request_raises_for_status() -> None:
        """Should raise HTTPError for non-200 responses."""
        client = ConcreteClient()

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")

        with patch.object(client.session, "request", return_value=mock_response):
            with pytest.raises(requests.HTTPError, match="404 Not Found"):
                client._request("GET", "https://api.example.com/notfound")


class TestContextManager:
    """Tests for context manager functionality."""

    @staticmethod
    def test_enter_returns_self() -> None:
        """Should return self on __enter__."""
        client = ConcreteClient()

        with client as ctx:
            assert ctx is client

    @staticmethod
    def test_exit_closes_session() -> None:
        """Should close session on __exit__."""
        client = ConcreteClient()

        # Access session to create it
        _ = client.session

        with client:
            pass

        assert client._session is None

    @staticmethod
    def test_context_manager_integration() -> None:
        """Should work as context manager."""
        with ConcreteClient() as client:
            assert client is not None
            # Session should be created if accessed
            _ = client.session
            assert client._session is not None

        # Session should be closed after exit
        assert client._session is None


class TestCloseMethod:
    """Tests for the close() method."""

    @staticmethod
    def test_close_when_session_exists() -> None:
        """Should close session when it exists."""
        client = ConcreteClient()

        # Create session
        session = client.session
        mock_close = MagicMock()
        session.close = mock_close

        client.close()

        mock_close.assert_called_once()
        assert client._session is None

    @staticmethod
    def test_close_when_no_session() -> None:
        """Should handle close when session is None."""
        client = ConcreteClient()

        # Should not raise
        client.close()
        assert client._session is None
