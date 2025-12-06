# Standard library
from abc import ABC, abstractmethod
from typing import Any

# Third-party
import requests

# Local
from msc.config.constants import DEFAULT_HEADERS
from msc.utils.logging import get_logger
from msc.utils.retry import RateLimiter, retry_with_backoff

"""Abstract base class for external API clients."""


class BaseClient(ABC):
    """Abstract base class for all API clients.

    Provides common functionality for authentication, rate limiting,
    retry logic, and logging.
    """

    def __init__(
            self,
            api_key: str | None = None,
            rate_limit: int = 10,
            timeout: int = 30,
    ):
        """Initialize the base client.

        Args:
            api_key: API key for authentication.
            rate_limit: Maximum requests per second.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limiter = RateLimiter(rate_limit)
        self.logger = get_logger(self.__class__.__name__)
        self._session: requests.Session | None = None

    @property
    def session(self) -> requests.Session:
        """Get or create a requests session."""
        if self._session is None:
            self._session = requests.Session()
            self._session.headers.update(self._get_default_headers())
        return self._session

    def _get_default_headers(self) -> dict[str, str]:
        """Get default headers for requests.

        Override in subclasses to add authentication headers.
        """
        headers = dict(DEFAULT_HEADERS)
        if self.api_key:
            headers["apikey"] = self.api_key
        return headers

    @abstractmethod
    def health_check(self) -> bool:
        """Verify API connectivity.

        Returns:
            True if the API is reachable and responding.
        """
        raise NotImplementedError("Subclasses must implement health_check()")

    @abstractmethod
    def get_quota(self) -> dict[str, Any]:
        """Get current quota/billing status.

        Returns:
            Dictionary with quota information.
        """
        raise NotImplementedError("Subclasses must implement get_quota()")

    @retry_with_backoff(max_retries=3)
    def _request(
            self,
            method: str,
            url: str,
            params: dict[str, Any] | None = None,
            json_data: dict[str, Any] | None = None,
    ) -> requests.Response:
        """Make an HTTP request with rate limiting and retry.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            params: Query parameters.
            json_data: JSON body data.

        Returns:
            Response object.

        Raises:
            requests.HTTPError: If request fails after retries.
        """
        with self.rate_limiter:
            self.logger.debug(f"{method} {url}", params=params)

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=self.timeout,
            )

            response.raise_for_status()
            return response

    def get(
            self,
            url: str,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a GET request and return JSON response.

        Args:
            url: Request URL.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        response = self._request("GET", url, params=params)
        return response.json()

    def post(
            self,
            url: str,
            json_data: dict[str, Any] | None = None,
            params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make a POST request and return JSON response.

        Args:
            url: Request URL.
            json_data: JSON body data.
            params: Query parameters.

        Returns:
            Parsed JSON response.
        """
        response = self._request("POST", url, params=params, json_data=json_data)
        return response.json()

    def close(self) -> None:
        """Close the session and clean up resources."""
        if self._session is not None:
            self._session.close()
            self._session = None

    def __enter__(self) -> "BaseClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: object) -> None:
        """Context manager exit."""
        self.close()
