import pytest
from getstream.stream import Stream
from getstream.video import rtc


@pytest.mark.asyncio
async def test_join(client: Stream):
    call = client.video.call("default", "test-join")

    # Test the join method as a context manager
    async with await rtc.join(call, "test-user") as connection:
        # Connection established
        assert connection is not None
        # Connection manager should have access to the call
        assert connection.call == call
