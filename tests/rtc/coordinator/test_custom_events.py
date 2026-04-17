"""
Integration tests for custom event pub/sub via coordinator WebSocket.

Tests the full round-trip: send a custom event via REST, receive it on the
coordinator WS through ConnectionManager.coordinator_ws property.

Requires Stream API credentials (STREAM_API_KEY, STREAM_API_SECRET).
"""

import asyncio
import logging
import uuid

import pytest
import pytest_asyncio

from getstream import AsyncStream
from getstream.models import CallRequest, UserRequest
from getstream.video import rtc
from getstream.video.rtc.connection_utils import ConnectionState
from tests.conftest import skip_on_rate_limit

logger = logging.getLogger(__name__)


@pytest_asyncio.fixture()
async def test_users(async_client: AsyncStream):
    user_ids = [f"test-user-{uuid.uuid4()}" for _ in range(2)]
    await async_client.upsert_users(*[UserRequest(id=uid) for uid in user_ids])
    yield user_ids
    try:
        await async_client.delete_users(
            user_ids=user_ids, user="hard", conversations="hard", messages="hard"
        )
    except Exception:
        logger.warning("Failed to clean up test users %s", user_ids, exc_info=True)


@pytest.mark.asyncio
@pytest.mark.integration
@skip_on_rate_limit
async def test_custom_event_round_trip(async_client: AsyncStream, test_users: list):
    """Send a custom event via REST and verify it arrives on coordinator_ws."""
    sender, receiver = test_users

    call = async_client.video.call("default", str(uuid.uuid4()))
    await call.get_or_create(data=CallRequest(created_by_id=sender))

    async with await rtc.join(call, receiver) as connection:
        assert connection.connection_state == ConnectionState.JOINED

        ws = connection.coordinator_ws
        assert ws is not None

        received_event = None
        event_received = asyncio.Event()

        @ws.on("custom")
        def on_custom(event):
            nonlocal received_event
            received_event = event
            event_received.set()

        await call.send_call_event(
            user_id=sender,
            custom={"type": "test_event", "payload": "hello from sender"},
        )

        await asyncio.wait_for(event_received.wait(), timeout=10.0)

        assert received_event is not None
        custom_data = received_event.get("custom", {})
        assert custom_data.get("type") == "test_event"
        assert custom_data.get("payload") == "hello from sender"
        assert received_event.get("user", {}).get("id") == sender
