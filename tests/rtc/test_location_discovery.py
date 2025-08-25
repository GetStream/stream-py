import unittest
from unittest.mock import MagicMock, patch

import pytest

from getstream.video.rtc.location_discovery import (
    FALLBACK_LOCATION_NAME,
    HEADER_CLOUDFRONT_POP,
    STREAM_PROD_URL,
    HTTPHintLocationDiscovery,
)


class TestLocationDiscovery(unittest.TestCase):
    """Unit tests for the HTTPHintLocationDiscovery class."""

    def setUp(self):
        self.logger_mock = MagicMock()
        self.client_mock = MagicMock()
        self.discovery = HTTPHintLocationDiscovery(
            url=STREAM_PROD_URL,
            max_retries=3,
            client=self.client_mock,
            logger=self.logger_mock,
        )

    def test_init_default_values(self):
        """Test that default values are set correctly."""
        discovery = HTTPHintLocationDiscovery()
        self.assertEqual(discovery.url, STREAM_PROD_URL)
        self.assertEqual(discovery.max_retries, 3)
        self.assertIsNotNone(discovery.client)
        self.assertIsNotNone(discovery.logger)

    def test_init_custom_values(self):
        """Test that custom values are set correctly."""
        custom_url = "https://custom.example.com/"
        custom_max_retries = 5
        discovery = HTTPHintLocationDiscovery(
            url=custom_url,
            max_retries=custom_max_retries,
            client=self.client_mock,
            logger=self.logger_mock,
        )
        self.assertEqual(discovery.url, custom_url)
        self.assertEqual(discovery.max_retries, custom_max_retries)
        self.assertEqual(discovery.client, self.client_mock)
        self.assertEqual(discovery.logger, self.logger_mock)

    @patch("http.client.HTTPSConnection")
    def test_discover_success(self, mock_https_connection):
        """Test successful location discovery."""
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getheader.return_value = "IAD12"

        # Setup the mock connection
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_conn

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, "IAD")

        # Verify that the correct HTTP request was made
        mock_conn.request.assert_called_once_with("HEAD", "/")
        mock_response.getheader.assert_called_once_with(HEADER_CLOUDFRONT_POP, "")
        mock_response.read.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("http.client.HTTPSConnection")
    def test_discover_invalid_pop_name(self, mock_https_connection):
        """Test discovering with an invalid POP name."""
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getheader.return_value = "AB"  # Too short

        # Setup the mock connection
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_conn

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, FALLBACK_LOCATION_NAME)

        # Verify that the warning was logged
        self.logger_mock.warning.assert_called_with("Invalid pop name: %s", "AB")

    @patch("http.client.HTTPSConnection")
    def test_discover_non_200_status(self, mock_https_connection):
        """Test discovering with a non-200 status code."""
        # Setup the mock response
        mock_response = MagicMock()
        mock_response.status = 404  # Not found

        # Setup the mock connection
        mock_conn = MagicMock()
        mock_conn.getresponse.return_value = mock_response
        mock_https_connection.return_value = mock_conn

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, FALLBACK_LOCATION_NAME)

        # Verify that the warning was logged
        self.logger_mock.warning.assert_called_with("Unexpected status code: %d", 404)

    @patch("http.client.HTTPSConnection")
    def test_discover_exception(self, mock_https_connection):
        """Test discovering with an exception during the request."""
        # Setup the mock connection to raise an exception
        mock_conn = MagicMock()
        mock_conn.request.side_effect = Exception("Connection error")
        mock_https_connection.return_value = mock_conn

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, FALLBACK_LOCATION_NAME)

        # Verify that the warning was logged
        self.logger_mock.warning.assert_called_with(
            "HEAD request failed: %s",
            "Connection error",
        )

    @patch("http.client.HTTPSConnection")
    def test_discover_max_retries(self, mock_https_connection):
        """Test that discovery respects the max_retries parameter."""
        # Setup the mock connection to raise an exception every time
        mock_conn = MagicMock()
        mock_conn.request.side_effect = Exception("Connection error")
        mock_https_connection.return_value = mock_conn

        # Set a custom max retries value
        self.discovery.max_retries = 2

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, FALLBACK_LOCATION_NAME)

        # Verify that the request was attempted the correct number of times
        self.assertEqual(mock_conn.request.call_count, 2)

    def test_discover_invalid_url(self):
        """Test discovering with an invalid URL."""
        # Set an invalid URL
        self.discovery.url = "invalid-url"

        # Call the discover method
        location = self.discovery.discover()

        # Verify the result
        self.assertEqual(location, FALLBACK_LOCATION_NAME)

        # Verify that the warning was logged
        self.logger_mock.warning.assert_called_with(
            "Invalid URL format: %s",
            "invalid-url",
        )

    def test_discover_caching(self):
        """Test that discover results are cached."""
        # Create a mock for the HTTP connection
        with patch("http.client.HTTPSConnection") as mock_https_connection:
            # Setup the mock response
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.getheader.return_value = "IAD12"

            # Setup the mock connection
            mock_conn = MagicMock()
            mock_conn.getresponse.return_value = mock_response
            mock_https_connection.return_value = mock_conn

            # Call the discover method twice
            location1 = self.discovery.discover()
            location2 = self.discovery.discover()

            # Verify the results
            self.assertEqual(location1, "IAD")
            self.assertEqual(location2, "IAD")

            # Verify that the request was only made once
            mock_conn.request.assert_called_once()


@pytest.mark.integration
def test_real_discovery():
    """Integration test that uses the actual network to discover a location."""
    discovery = HTTPHintLocationDiscovery()
    location = discovery.discover()
    assert location is not None
    assert len(location) == 3
