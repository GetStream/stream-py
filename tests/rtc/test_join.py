import pytest
from getstream.stream import Stream
from getstream.video import rtc
import os  # Import os for path manipulation
import asyncio


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
async def test_detect_video_properties(client: Stream):
    from aiortc.contrib.media import MediaPlayer
    from getstream.video.rtc.connection_manager import (
        detect_video_properties,
        BufferedMediaTrack,
    )

    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Check if file exists before running test, skip if not
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    try:
        # Create a media player from the file
        player = MediaPlayer(file_path)

        # Ensure we have a video track
        assert player.video is not None, "No video track found in test file"

        # Create a buffered track to safely inspect properties
        buffered_track = BufferedMediaTrack(player.video)

        # Detect video properties before adding to the connection
        video_props = await detect_video_properties(buffered_track)
        print(f"Detected video properties: {video_props}")

        # Verify detected properties match expectations
        assert "width" in video_props, "Width not detected"
        assert "height" in video_props, "Height not detected"
        assert (
            video_props["width"] == 1280
        ), f"Incorrect width detected: {video_props['width']}"
        assert (
            video_props["height"] == 720
        ), f"Incorrect height detected: {video_props['height']}"
        assert video_props["fps"] == 25, "Invalid FPS value"
        assert (
            1000 <= video_props["bitrate"] <= 2000
        ), f"Unexpected bitrate: {video_props['bitrate']}"

    finally:
        # Ensure player is properly closed
        if "player" in locals() and hasattr(player, "video") and player.video:
            buffered_track.stop()  # Stop the buffered track

            # Give a moment for cleanup
            await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_play_file(client: Stream):
    from aiortc.contrib.media import MediaPlayer

    call = client.video.call("default", "mQbx3HG7wtTj")

    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Check if file exists before running test, skip if not
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    player = MediaPlayer(file_path)

    async with await rtc.join(call, "test-user") as connection:
        # Use add_tracks which now automatically detects properties
        await connection.add_tracks(
            video=player.video,
            audio=player.audio,
        )

        await connection.wait()
