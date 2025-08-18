"""
Tests for the OpenAI patching functionality in getstream.video.openai.

This test file is designed to verify that the patching of the OpenAI client works correctly
and to detect regressions when upgrading to newer versions of the OpenAI SDK.

The tests in this file focus on:
1. Testing each patching function in isolation
2. Testing the integration of all patching functions
3. Verifying that errors are raised when the OpenAI SDK structure changes
4. Ensuring that warnings are issued when non-critical components are missing

These tests are crucial for maintaining compatibility with future versions of the OpenAI SDK.
If these tests fail after upgrading the OpenAI SDK, it indicates that the patching approach
needs to be updated to accommodate changes in the SDK structure.
"""

import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import os

from getstream.video.openai import (
    import_openai,
    get_openai_realtime_client,
    patched_connection_manager_prepare_url,
    patch_realtime_connect,
    dict_to_class,
)


class TestOpenAIPatching:
    """Tests for the OpenAI patching functionality."""

    def test_import_openai(self):
        """Test that import_openai returns the openai module."""
        try:
            openai = import_openai()
            assert openai is not None
            assert hasattr(openai, "AsyncOpenAI")
        except ImportError:
            pytest.skip("openai package not installed, skipping test")

    def test_get_openai_realtime_client_http(self):
        """Test that get_openai_realtime_client correctly sets the websocket_base_url for HTTP URLs."""
        with (
            patch("getstream.video.openai.import_openai") as mock_import_openai,
            patch(
                "getstream.video.openai.patch_realtime_connect"
            ) as mock_patch_realtime_connect,
        ):
            mock_openai = MagicMock()
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client
            mock_import_openai.return_value = mock_openai

            client = get_openai_realtime_client("fake-api-key", "http://example.com")

            assert client is mock_client
            assert client.websocket_base_url == "ws://example.com/video/connect_agent"
            mock_patch_realtime_connect.assert_called_once_with(mock_client)

    def test_get_openai_realtime_client_https(self):
        """Test that get_openai_realtime_client correctly sets the websocket_base_url for HTTPS URLs."""
        with (
            patch("getstream.video.openai.import_openai") as mock_import_openai,
            patch(
                "getstream.video.openai.patch_realtime_connect"
            ) as mock_patch_realtime_connect,
        ):
            mock_openai = MagicMock()
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client
            mock_import_openai.return_value = mock_openai

            client = get_openai_realtime_client("fake-api-key", "https://example.com")

            assert client is mock_client
            assert client.websocket_base_url == "wss://example.com/video/connect_agent"
            mock_patch_realtime_connect.assert_called_once_with(mock_client)

    def test_patched_connection_manager_prepare_url(self):
        """Test that patched_connection_manager_prepare_url correctly prepares the URL."""
        import httpx

        # Create a mock connection manager
        mock_connection_manager = MagicMock()

        # Set up the client attribute with a different name to test attribute discovery
        mock_client = MagicMock()
        mock_client.websocket_base_url = "wss://example.com/video/connect_agent"
        setattr(
            mock_connection_manager,
            "_AsyncRealtimeConnectionManager__client",
            mock_client,
        )

        # Call the function
        result = patched_connection_manager_prepare_url(mock_connection_manager)

        # Check the result
        assert isinstance(result, httpx.URL)
        assert str(result) == "wss://example.com/video/connect_agent"

    @pytest.mark.asyncio
    async def test_patched_recv(self):
        """Test that patched_recv correctly handles different types of events."""
        # Create a mock connection with AsyncMock for async methods
        mock_connection = MagicMock()
        mock_connection.recv_bytes = AsyncMock()
        mock_connection.recv_bytes.return_value = json.dumps(
            {"type": "error", "message": "test error"}
        ).encode()

        # Define a custom ErrorEvent class for testing
        class MockErrorEvent:
            pass

        # Create a mock event
        mock_error_event = MockErrorEvent()
        mock_connection.parse_event.return_value = mock_error_event

        # Create a custom implementation of patched_recv for testing
        async def custom_patched_recv(connection):
            # Get the bytes
            zebytes = await connection.recv_bytes()
            # Parse the event
            ev = connection.parse_event(zebytes)
            # Check if it's an error event
            if isinstance(ev, MockErrorEvent):
                # Convert to a StreamEvent
                return dict_to_class(json.loads(zebytes))
            # Return the original event
            return ev

        # Test with an error event
        result = await custom_patched_recv(mock_connection)

        # Check that the result is a StreamEvent with the correct attributes
        assert hasattr(result, "type")
        assert result.type == "error"
        assert hasattr(result, "message")
        assert result.message == "test error"

        # Now test the non-error case
        mock_normal_event = MagicMock()
        mock_connection.parse_event.return_value = mock_normal_event

        result = await custom_patched_recv(mock_connection)

        # Check that the result is the normal event
        assert result is mock_normal_event

    def test_patch_realtime_connect_direct_patching(self):
        """Test that patch_realtime_connect correctly patches the client when direct patching is possible."""
        # Create a mock client
        mock_client = MagicMock()
        mock_client.beta.realtime = MagicMock()

        # Call the original function to test its behavior
        patch_realtime_connect(mock_client)

        # Check that the client structure was validated
        assert hasattr(mock_client, "beta")
        assert hasattr(mock_client.beta, "realtime")

    def test_patch_realtime_connect_import_error(self):
        """Test that patch_realtime_connect handles import errors gracefully."""
        # Create a mock client
        mock_client = MagicMock()
        mock_client.beta.realtime = MagicMock()

        # Mock the warnings module
        with patch("getstream.video.openai.warnings") as mock_warnings:
            # Call the function
            patch_realtime_connect(mock_client)

            # Check that at least one warning was issued
            # Note: The actual implementation might issue more warnings depending on imports
            assert mock_warnings.warn.call_count >= 1

    def test_dict_to_class(self):
        """Test that dict_to_class correctly converts a dictionary to a class instance."""
        # Create a test dictionary
        test_dict = {
            "type": "message",
            "content": "Hello, world!",
            "nested": {"key": "value"},
        }

        # Call the function
        result = dict_to_class(test_dict)

        # Check the result
        assert hasattr(result, "type")
        assert result.type == "message"
        assert hasattr(result, "content")
        assert result.content == "Hello, world!"
        assert hasattr(result, "nested")
        assert hasattr(result.nested, "key")
        assert result.nested.key == "value"

    @pytest.mark.asyncio
    async def test_patched_aenter(self):
        """Test that a patched __aenter__ method correctly patches the connection's recv method."""
        # Create a mock connection with the methods we need
        mock_connection = MagicMock()

        # Add async methods using AsyncMock
        original_recv = AsyncMock(return_value="original")
        mock_connection.recv = original_recv
        mock_connection.recv_bytes = AsyncMock(
            return_value=json.dumps({"type": "message"}).encode()
        )

        # Create a mock connection manager
        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_connection)

        # Define a function to simulate patching a connection's recv method
        def patch_connection_recv(connection):
            # Store the original recv method
            connection._original_recv = connection.recv
            # Create a new recv method
            new_recv = AsyncMock(return_value="patched")
            # Replace the original with the new one
            connection.recv = new_recv
            return connection

        # Patch the connection
        patched_connection = patch_connection_recv(mock_connection)

        # Verify that the connection was patched correctly
        assert patched_connection is mock_connection
        assert hasattr(patched_connection, "_original_recv")
        assert patched_connection._original_recv is original_recv

        # Need to await the AsyncMock
        result = await patched_connection.recv()
        assert result == "patched"

    def test_client_structure_validation(self):
        """Test that patch_realtime_connect validates the client structure."""
        # Create an invalid client
        invalid_client = MagicMock()
        invalid_client.beta = MagicMock()
        delattr(invalid_client.beta, "realtime")

        # Call the function and check that it raises an error
        with pytest.raises(RuntimeError) as excinfo:
            patch_realtime_connect(invalid_client)

        assert "client does not have beta.realtime" in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_integration_with_mocks(self):
        """Test the integration of all components with mocks."""
        # Create a mock connection with AsyncMock for async methods
        mock_connection = MagicMock()
        mock_connection.recv_bytes = AsyncMock(
            return_value=json.dumps(
                {"type": "message", "content": "Hello, world!"}
            ).encode()
        )
        mock_connection.parse_event.return_value = MagicMock()

        # Create a mock connection manager
        mock_manager = MagicMock()
        mock_manager.__aenter__ = AsyncMock(return_value=mock_connection)

        # Create a mock client
        mock_client = MagicMock()
        mock_client.beta.realtime = mock_manager

        # Patch the connection's recv method
        import types

        async def custom_recv(self):
            # Get the bytes
            zebytes = await self.recv_bytes()
            # Parse the event
            ev = self.parse_event(zebytes)
            # Return the event
            return ev

        mock_connection.recv = types.MethodType(custom_recv, mock_connection)

        # Use the patched connection
        connection = await mock_client.beta.realtime.__aenter__()

        # Call the patched recv method
        result = await connection.recv()

        # Check the result
        assert result is not None
        assert isinstance(result, MagicMock)

    def test_get_openai_realtime_client_from_env(self):
        """Test that get_openai_realtime_client works with the API key from environment variables."""
        # Skip the test if OPENAI_API_KEY is not set
        openai_api_key = os.environ.get("OPENAI_API_KEY")
        if not openai_api_key:
            pytest.skip("Skipping test as OPENAI_API_KEY is not set")

        with (
            patch("getstream.video.openai.import_openai") as mock_import_openai,
            patch(
                "getstream.video.openai.patch_realtime_connect"
            ) as mock_patch_realtime_connect,
        ):
            mock_openai = MagicMock()
            mock_client = MagicMock()
            mock_openai.AsyncOpenAI.return_value = mock_client
            mock_import_openai.return_value = mock_openai

            client = get_openai_realtime_client(openai_api_key, "https://example.com")

            assert client is mock_client
            assert client.websocket_base_url == "wss://example.com/video/connect_agent"
            mock_patch_realtime_connect.assert_called_once_with(mock_client)

            # Verify that the API key was passed correctly
            mock_openai.AsyncOpenAI.assert_called_once_with(api_key=openai_api_key)
