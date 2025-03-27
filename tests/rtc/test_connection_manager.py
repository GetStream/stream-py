import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from getstream.video.rtc.connection_manager import ConnectionManager, ConnectionError
from getstream.base import StreamResponse


@pytest.mark.asyncio
async def test_connection_manager_init():
    """Test that the ConnectionManager initializes correctly."""
    # Create mocks
    mock_call = MagicMock()
    mock_call.call_type = "default"
    mock_call.id = "test-call-id"

    # Initialize ConnectionManager
    cm = ConnectionManager(call=mock_call, user_id="test-user")

    # Check init state
    assert cm.call == mock_call
    assert cm.user_id == "test-user"
    assert cm.create is True  # Default value
    assert cm.running is False
    assert cm.join_response is None


@pytest.mark.asyncio
async def test_connection_manager_enter_calls_discovery():
    """Test that __aenter__ calls location discovery."""
    # Create mocks
    mock_call = MagicMock()
    mock_call.call_type = "default"
    mock_call.id = "test-call-id"

    # Create a fake response to return from the join_call_coordinator_request
    mock_response = MagicMock(spec=StreamResponse)
    mock_response.data = MagicMock()
    mock_response.data.credentials = MagicMock()
    mock_response.data.credentials.server = MagicMock()
    mock_response.data.credentials.server.url = "https://fake-sfu-url.com"

    # Patch location discovery and join call
    with (
        patch(
            "getstream.video.rtc.connection_manager.HTTPHintLocationDiscovery"
        ) as mock_discovery_class,
        patch(
            "getstream.video.rtc.connection_manager.join_call_coordinator_request",
            new_callable=AsyncMock,
        ) as mock_join,
    ):
        # Setup mock discovery
        mock_discovery = MagicMock()
        mock_discovery.discover.return_value = "FRA"
        mock_discovery_class.return_value = mock_discovery

        # Setup mock join response
        mock_join.return_value = mock_response

        # Initialize and enter ConnectionManager
        cm = ConnectionManager(call=mock_call, user_id="test-user")
        await cm.__aenter__()

        # Check that discovery was called
        mock_discovery_class.assert_called_once()
        mock_discovery.discover.assert_called_once()

        # Check that join was called with the right parameters
        mock_join.assert_called_once_with(
            mock_call,
            "test-user",
            create=True,
            location="FRA",
        )

        # Check that running is set to True
        assert cm.running is True
        assert cm.join_response is mock_response


@pytest.mark.asyncio
async def test_connection_manager_discovery_error_fallback():
    """Test that __aenter__ falls back to a default location if discovery fails."""
    # Create mocks
    mock_call = MagicMock()

    # Create a fake response
    mock_response = MagicMock(spec=StreamResponse)
    mock_response.data = MagicMock()
    mock_response.data.credentials = MagicMock()
    mock_response.data.credentials.server = MagicMock()
    mock_response.data.credentials.server.url = "https://fake-sfu-url.com"

    # Patch location discovery and join call
    with (
        patch(
            "getstream.video.rtc.connection_manager.HTTPHintLocationDiscovery"
        ) as mock_discovery_class,
        patch(
            "getstream.video.rtc.connection_manager.join_call_coordinator_request",
            new_callable=AsyncMock,
        ) as mock_join,
    ):
        # Setup mock discovery to raise an exception
        mock_discovery = MagicMock()
        mock_discovery.discover.side_effect = Exception("Discovery failed")
        mock_discovery_class.return_value = mock_discovery

        # Setup mock join response
        mock_join.return_value = mock_response

        # Initialize and enter ConnectionManager
        cm = ConnectionManager(call=mock_call, user_id="test-user")
        await cm.__aenter__()

        # Check that discovery was called and failed
        mock_discovery_class.assert_called_once()
        mock_discovery.discover.assert_called_once()

        # Check that join was called with the fallback location
        mock_join.assert_called_once_with(
            mock_call,
            "test-user",
            create=True,
            location="FRA",  # This is the fallback
        )


@pytest.mark.asyncio
async def test_connection_manager_join_error():
    """Test that __aenter__ raises ConnectionError if join fails."""
    # Create mocks
    mock_call = MagicMock()

    # Patch location discovery and join call
    with (
        patch(
            "getstream.video.rtc.connection_manager.HTTPHintLocationDiscovery"
        ) as mock_discovery_class,
        patch(
            "getstream.video.rtc.connection_manager.join_call_coordinator_request",
            new_callable=AsyncMock,
        ) as mock_join,
    ):
        # Setup mock discovery
        mock_discovery = MagicMock()
        mock_discovery.discover.return_value = "FRA"
        mock_discovery_class.return_value = mock_discovery

        # Setup mock join to raise an exception
        mock_join.side_effect = Exception("Join failed")

        # Initialize ConnectionManager
        cm = ConnectionManager(call=mock_call, user_id="test-user")

        # Check that entering raises ConnectionError
        with pytest.raises(ConnectionError) as exc_info:
            await cm.__aenter__()

        # Check the error message
        assert "Failed to join call" in str(exc_info.value)

        # Check that join was called
        mock_join.assert_called_once()


@pytest.mark.asyncio
async def test_connection_manager_leave():
    """Test that leave stops yielding events."""
    # Create mocks
    mock_call = MagicMock()

    # Create a fake response
    mock_response = MagicMock(spec=StreamResponse)
    mock_response.data = MagicMock()
    mock_response.data.credentials = MagicMock()
    mock_response.data.credentials.server = MagicMock()
    mock_response.data.credentials.server.url = "https://fake-sfu-url.com"

    # Patch location discovery and join call
    with (
        patch(
            "getstream.video.rtc.connection_manager.HTTPHintLocationDiscovery"
        ) as mock_discovery_class,
        patch(
            "getstream.video.rtc.connection_manager.join_call_coordinator_request",
            new_callable=AsyncMock,
        ) as mock_join,
    ):
        # Setup mock discovery
        mock_discovery = MagicMock()
        mock_discovery.discover.return_value = "FRA"
        mock_discovery_class.return_value = mock_discovery

        # Setup mock join response
        mock_join.return_value = mock_response

        # Initialize and enter ConnectionManager
        cm = ConnectionManager(call=mock_call, user_id="test-user")
        await cm.__aenter__()

        # Get one event
        event = await cm.__anext__()
        assert event == "helloworld"

        # Leave the call
        await cm.leave()

        # Trying to get another event should raise StopAsyncIteration
        with pytest.raises(StopAsyncIteration):
            await cm.__anext__()


@pytest.mark.asyncio
async def test_connection_manager_async_context_manager():
    """Test that ConnectionManager works properly as an async context manager."""
    # Create mocks
    mock_call = MagicMock()

    # Create a fake response
    mock_response = MagicMock(spec=StreamResponse)
    mock_response.data = MagicMock()
    mock_response.data.credentials = MagicMock()
    mock_response.data.credentials.server = MagicMock()
    mock_response.data.credentials.server.url = "https://fake-sfu-url.com"

    # Patch location discovery and join call
    with (
        patch(
            "getstream.video.rtc.connection_manager.HTTPHintLocationDiscovery"
        ) as mock_discovery_class,
        patch(
            "getstream.video.rtc.connection_manager.join_call_coordinator_request",
            new_callable=AsyncMock,
        ) as mock_join,
    ):
        # Setup mock discovery
        mock_discovery = MagicMock()
        mock_discovery.discover.return_value = "FRA"
        mock_discovery_class.return_value = mock_discovery

        # Setup mock join response
        mock_join.return_value = mock_response

        # Use ConnectionManager as an async context manager
        events = []
        async with ConnectionManager(call=mock_call, user_id="test-user") as cm:
            # Get one event
            event = await cm.__anext__()
            events.append(event)
            # We don't call leave() explicitly, it should be called in __aexit__

        # Check that we got the event
        assert events == ["helloworld"]

        # Check that leave was called (running should be False)
        assert cm.running is False
