import pytest
from getstream.stream import Stream
from getstream.video import rtc


@pytest.mark.asyncio
async def test_join_and_leave(client: Stream):
    call = client.video.call("default", "test-join")

    received_event = None
    # Test the join method as a context manager
    async with await rtc.join(call, "test-user") as connection:
        async for _ in connection:
            received_event = True
            await connection.leave()

    assert received_event is True, "did not receive event"


@pytest.mark.asyncio
async def test_join(client: Stream):
    call = client.video.call("default", "sGSmO6CWmudu")

    received_event = None
    # Test the join method as a context manager
    async with await rtc.join(call, "test-user") as connection:
        async for _ in connection:
            received_event = True

    assert received_event is True, "did not receive event"
