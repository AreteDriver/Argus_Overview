"""
ESI Client - HTTP wrapper for EVE Swagger Interface with rate limiting.

Handles:
- Rate limiting via X-ESI-Error-Limit headers
- Exponential backoff on 502/503/504
- Connection pooling
"""

import logging
import time
from typing import Any, Optional

import httpx
from PySide6.QtCore import QObject, Signal


class ESIClient(QObject):
    """
    HTTP client for ESI with rate limiting and error handling.

    Uses httpx for async-capable HTTP with connection pooling.
    Respects ESI rate limits and implements exponential backoff.
    """

    BASE_URL = "https://esi.evetech.net/latest"

    # Signals for status updates
    rate_limited = Signal(int)  # seconds until reset
    error_occurred = Signal(str)  # error message

    def __init__(self, timeout: float = 10.0, parent: Optional[QObject] = None):
        """
        Initialize ESI client.

        Args:
            timeout: Request timeout in seconds
            parent: Parent QObject
        """
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.timeout = timeout

        # Rate limiting state
        self._error_limit_remain = 100
        self._error_limit_reset = 0
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # 100ms between requests

        # Backoff state
        self._consecutive_errors = 0
        self._max_backoff = 60  # seconds

        # HTTP client (created on demand)
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Argus-Overview/2.9 (https://github.com/AreteDriver/Argus_Overview)",
                },
            )
        return self._client

    def get(
        self,
        endpoint: str,
        params: Optional[dict] = None,
    ) -> Optional[Any]:
        """
        Make GET request to ESI endpoint.

        Args:
            endpoint: API endpoint (e.g., "/route/123/456/")
            params: Query parameters

        Returns:
            Parsed JSON response, or None on error
        """
        # Rate limiting
        self._wait_if_needed()

        # Check error limit
        if self._error_limit_remain <= 5:
            wait_time = max(1, self._error_limit_reset - int(time.time()))
            self.logger.warning(f"ESI error limit low, waiting {wait_time}s")
            self.rate_limited.emit(wait_time)
            time.sleep(wait_time)

        try:
            response = self.client.get(endpoint, params=params)
            self._update_rate_limits(response)

            if response.status_code == 200:
                self._consecutive_errors = 0
                return response.json()

            if response.status_code == 304:
                # Not modified - return None, caller should use cache
                self._consecutive_errors = 0
                return None

            if response.status_code in (502, 503, 504):
                # Server error - backoff and retry
                self._handle_server_error()
                return None

            if response.status_code == 404:
                self.logger.debug(f"ESI 404: {endpoint}")
                return None

            if response.status_code == 420:
                # Error limit exceeded
                wait_time = max(1, self._error_limit_reset - int(time.time()))
                self.logger.warning(f"ESI rate limited, waiting {wait_time}s")
                self.rate_limited.emit(wait_time)
                time.sleep(wait_time)
                return None

            self.logger.warning(f"ESI error {response.status_code}: {endpoint}")
            self.error_occurred.emit(f"ESI error: {response.status_code}")
            return None

        except httpx.TimeoutException:
            self.logger.warning(f"ESI timeout: {endpoint}")
            self._handle_server_error()
            return None

        except httpx.RequestError as e:
            self.logger.warning(f"ESI request error: {e}")
            self._handle_server_error()
            return None

    def post(
        self,
        endpoint: str,
        json_data: Any = None,
        params: Optional[dict] = None,
    ) -> Optional[Any]:
        """
        Make POST request to ESI endpoint.

        Args:
            endpoint: API endpoint
            json_data: JSON body data
            params: Query parameters

        Returns:
            Parsed JSON response, or None on error
        """
        self._wait_if_needed()

        if self._error_limit_remain <= 5:
            wait_time = max(1, self._error_limit_reset - int(time.time()))
            self.logger.warning(f"ESI error limit low, waiting {wait_time}s")
            time.sleep(wait_time)

        try:
            response = self.client.post(endpoint, json=json_data, params=params)
            self._update_rate_limits(response)

            if response.status_code == 200:
                self._consecutive_errors = 0
                return response.json()

            if response.status_code in (502, 503, 504):
                self._handle_server_error()
                return None

            self.logger.warning(f"ESI error {response.status_code}: {endpoint}")
            return None

        except httpx.TimeoutException:
            self.logger.warning(f"ESI timeout: {endpoint}")
            self._handle_server_error()
            return None

        except httpx.RequestError as e:
            self.logger.warning(f"ESI request error: {e}")
            self._handle_server_error()
            return None

    def _wait_if_needed(self):
        """Enforce minimum interval between requests."""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            time.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    def _update_rate_limits(self, response: httpx.Response):
        """Update rate limit state from response headers."""
        try:
            if "X-ESI-Error-Limit-Remain" in response.headers:
                self._error_limit_remain = int(response.headers["X-ESI-Error-Limit-Remain"])

            if "X-ESI-Error-Limit-Reset" in response.headers:
                reset_seconds = int(response.headers["X-ESI-Error-Limit-Reset"])
                self._error_limit_reset = int(time.time()) + reset_seconds

        except (ValueError, KeyError):
            pass

    def _handle_server_error(self):
        """Handle server error with exponential backoff."""
        self._consecutive_errors += 1
        backoff = min(2**self._consecutive_errors, self._max_backoff)
        self.logger.warning(f"ESI server error, backing off {backoff}s")
        time.sleep(backoff)

    def close(self):
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __del__(self):
        """Cleanup on destruction."""
        self.close()
