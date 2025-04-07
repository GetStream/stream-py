import pytest
from getstream.stream import Stream
from getstream.video import rtc
import os  # Import os for path manipulation


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


@pytest.mark.asyncio
async def test_play_file(client: Stream):
    call = client.video.call("default", "mQbx3HG7wtTj")

    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Check if file exists before running test, skip if not
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    async with await rtc.join(call, "test-user") as connection:
        await connection.playFile(file_path)
