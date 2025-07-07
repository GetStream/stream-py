"""
Location discovery for video streaming.

This module provides functionality to discover the optimal location for video streaming
connections based on CloudFront POP headers.
"""

import logging
import http.client
import functools
from typing import Optional, Protocol
from contextlib import contextmanager

# Constants matching the Go implementation
HEADER_CLOUDFRONT_POP = "X-Amz-Cf-Pop"
FALLBACK_LOCATION_NAME = "IAD"
STREAM_PROD_URL = "https://hint.stream-io-video.com/"

# Create a logger for the location discovery module
logger = logging.getLogger(__name__)


class HTTPClient(Protocol):
    """Protocol defining the HTTP client interface."""

    def request(self, method: str, url: str, body=None, headers=None, **kwargs):
        """Make an HTTP request."""
        ...

    @contextmanager
    def response(self):
        """Get the HTTP response."""
        ...


class HTTPHintLocationDiscovery:
    """Implementation of location discovery using CloudFront headers."""

    def __init__(
        self,
        url: str = STREAM_PROD_URL,
        max_retries: int = 3,
        client: Optional[HTTPClient] = None,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize the location discovery service.

        Args:
            url: The URL to use for discovery
            max_retries: Maximum number of retries for discovery
            client: HTTP client to use
            logger: Logger instance
        """
        self.url = url
        self.max_retries = max_retries
        self.client = client or create_default_http_client()
        # Use the provided logger or fall back to the module-level logger
        self.logger = logger or globals()["logger"]

    @functools.lru_cache(maxsize=1)
    def discover(self, context=None) -> str:
        """
        Discover the closest location based on CloudFront pop.

        Args:
            context: Optional context (for compatibility with Go implementation)

        Returns:
            The 3-character location code (e.g. "IAD", "FRA")
        """
        parsed_url = self.url.split("://", 1)
        if len(parsed_url) != 2:
            self.logger.warning("Invalid URL format: %s", self.url)
            return FALLBACK_LOCATION_NAME

        protocol, host_path = parsed_url
        host = host_path.split("/", 1)[0]
        path = "/" + host_path.split("/", 1)[1] if "/" in host_path else "/"

        for i in range(self.max_retries):
            self.logger.info("Discovering location, attempt %d", i + 1)
            try:
                if protocol.lower() == "https":
                    conn = http.client.HTTPSConnection(host, timeout=1)
                else:
                    conn = http.client.HTTPConnection(host, timeout=1)

                conn.request("HEAD", path)
                response = conn.getresponse()

                if response.status != 200:
                    self.logger.warning("Unexpected status code: %d", response.status)
                    continue

                pop_name = response.getheader(HEADER_CLOUDFRONT_POP, "")
                response.read()  # Read and discard the response body
                conn.close()

                if len(pop_name) < 3:
                    self.logger.warning("Invalid pop name: %s", pop_name)
                    return FALLBACK_LOCATION_NAME

                location = pop_name[:3]
                self.logger.info(f"Discovered location: {location}")
                return location

            except Exception as e:
                self.logger.warning("HEAD request failed: %s", str(e))
                continue

        self.logger.info(
            "Failed to discover location after %d attempts, using fallback %s",
            self.max_retries,
            FALLBACK_LOCATION_NAME,
        )
        return FALLBACK_LOCATION_NAME


def create_default_http_client():
    """
    Create a default HTTP client with appropriate timeouts.

    Returns:
        A simple HTTP client
    """

    class SimpleHTTPClient:
        def request(self, method, url, body=None, headers=None, **kwargs):
            self.parsed_url = url.split("://", 1)
            if len(self.parsed_url) != 2:
                raise ValueError(f"Invalid URL format: {url}")

            self.protocol, host_path = self.parsed_url
            self.host = host_path.split("/", 1)[0]
            self.path = "/" + host_path.split("/", 1)[1] if "/" in host_path else "/"
            self.method = method
            self.body = body
            self.headers = headers or {}

        @contextmanager
        def response(self):
            try:
                if self.protocol.lower() == "https":
                    conn = http.client.HTTPSConnection(self.host, timeout=1)
                else:
                    conn = http.client.HTTPConnection(self.host, timeout=1)

                conn.request(self.method, self.path, self.body, self.headers)
                resp = conn.getresponse()
                yield resp
                resp.read()
            finally:
                conn.close()

    return SimpleHTTPClient()
