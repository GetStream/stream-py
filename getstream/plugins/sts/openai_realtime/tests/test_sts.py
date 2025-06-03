import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from getstream.plugins.sts.openai_realtime import OpenAIRealtime
from getstream.video.call import Call


@pytest.fixture
def mock_call():
    """Create a mock Call instance."""
    call = MagicMock(spec=Call)
    call.call_type = "default"
    call.id = "test-call"
    return call


@pytest.fixture
def mock_connection():
    """Create a mock OpenAI connection."""
    connection = AsyncMock()
    connection.session = AsyncMock()
    connection.conversation = AsyncMock()
    connection.conversation.item = AsyncMock()
    connection.response = AsyncMock()
    return connection


@pytest.fixture
def mock_connection_cm(mock_connection):
    """Create a mock async context manager for the connection."""
    cm = AsyncMock()
    cm.__aenter__.return_value = mock_connection
    return cm


@pytest.mark.asyncio
async def test_openai_realtime_init():
    """Test OpenAIRealtime initialization."""
    # Test with explicit API key
    sts = OpenAIRealtime(api_key="test-key")
    assert sts.api_key == "test-key"
    assert sts.model == "gpt-4o-realtime-preview"
    assert sts.voice is None
    assert sts.instructions is None

    # Test with environment variable
    with patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"}):
        sts = OpenAIRealtime()
        assert sts.api_key == "env-key"

    # Test with missing API key
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="OPENAI_API_KEY not provided"):
            OpenAIRealtime()


@pytest.mark.asyncio
async def test_openai_realtime_connect(mock_call, mock_connection_cm):
    """Test connecting the OpenAI agent."""
    with patch.object(mock_call, "connect_openai", return_value=mock_connection_cm):
        sts = OpenAIRealtime(api_key="test-key", voice="alloy", instructions="Be helpful")
        events = []

        @sts.on("*")
        async def on_event(event_type, *args):
            events.append(event_type)

        # Connect
        await sts.connect(mock_call, agent_user_id="test-agent")
        await asyncio.sleep(0)

        # Verify connection state
        assert sts.is_connected
        print(events)
        assert "connected" in events

        # Verify session was updated
        mock_connection_cm.__aenter__.return_value.session.update.assert_called_once_with(
            session={"instructions": "Be helpful", "voice": "alloy"}
        )

        # Verify connection was established with correct params
        mock_call.connect_openai.assert_called_once_with(
            "test-key", "test-agent", model="gpt-4o-realtime-preview"
        )


@pytest.mark.asyncio
async def test_openai_realtime_close(mock_call, mock_connection_cm):
    """Test closing the OpenAI agent."""
    with patch.object(mock_call, "connect_openai", return_value=mock_connection_cm):
        sts = OpenAIRealtime(api_key="test-key")
        events = []

        @sts.on("*")
        async def on_event(event_type, *args):
            events.append(event_type)

        # Connect first
        await sts.connect(mock_call)
        assert sts.is_connected

        # Close
        await sts.close()

        # Verify state
        assert not sts.is_connected
        assert "disconnected" in events
        mock_connection_cm.__aexit__.assert_called_once()


@pytest.mark.asyncio
async def test_openai_realtime_send_message(mock_call, mock_connection_cm):
    """Test sending a user message."""
    with patch.object(mock_call, "connect_openai", return_value=mock_connection_cm):
        sts = OpenAIRealtime(api_key="test-key")
        await sts.connect(mock_call)

        # Send message
        await sts.send_user_message("Hello, AI!")

        # Verify message was sent
        mock_connection_cm.__aenter__.return_value.conversation.item.create.assert_called_once_with(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello, AI!"}],
            }
        )
        mock_connection_cm.__aenter__.return_value.response.create.assert_called_once()


@pytest.mark.asyncio
async def test_openai_realtime_update_session(mock_call, mock_connection_cm):
    """Test updating the session configuration."""
    with patch.object(mock_call, "connect_openai", return_value=mock_connection_cm):
        sts = OpenAIRealtime(api_key="test-key")
        await sts.connect(mock_call)

        # Update session
        await sts.update_session(voice="nova", temperature=0.7)

        # Verify session was updated
        mock_connection_cm.__aenter__.return_value.session.update.assert_called_with(
            session={"voice": "nova", "temperature": 0.7}
        )


@pytest.mark.asyncio
async def test_openai_realtime_error_handling(mock_call, mock_connection_cm):
    """Test error handling in the event listener."""
    with patch.object(mock_call, "connect_openai", return_value=mock_connection_cm):
        sts = OpenAIRealtime(api_key="test-key")
        events = []
        errors = []

        @sts.on("*")
        async def on_event(event_type, *args):
            events.append(event_type)

        @sts.on("error")
        async def on_error(error):
            errors.append(error)

        # Connect
        await sts.connect(mock_call)

        # Simulate an error in the event stream
        mock_connection_cm.__aenter__.return_value.__aiter__.side_effect = Exception("Test error")

        # Wait for error to be processed
        await asyncio.sleep(0.1)

        # Verify error was handled
        assert "error" in events
        assert len(errors) == 1
        assert str(errors[0]) == "Test error"
        assert not sts.is_connected
        assert "disconnected" in events 