import pytest
from getstream.stream import Stream
from getstream.video import rtc


@pytest.mark.asyncio
async def test_join(client: Stream):
    call = client.video.call("default", "test-join")

    async with await rtc.join(call, "test-user") as _:
        pass
