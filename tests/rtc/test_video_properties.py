import pytest
import os
import asyncio
from aiortc.contrib.media import MediaPlayer
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc.track_util import (
    detect_video_properties,
    BufferedMediaTrack,
)
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import TRACK_TYPE_VIDEO


@pytest.mark.asyncio
async def test_detect_video_properties():
    """Test that video properties are correctly detected from a video file."""
    # Path to the test video file
    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Skip test if the file doesn't exist
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    buffered_track = None

    try:
        # Create a media player from the file
        player = MediaPlayer(file_path)

        # Ensure we have a video track
        assert player.video is not None, "No video track found in test file"

        # Create a buffered track for testing
        buffered_track = BufferedMediaTrack(player.video)

        # Test the property detection function
        properties = await detect_video_properties(buffered_track)

        # Verify detected properties match expectations
        assert "width" in properties, "Width not detected"
        assert "height" in properties, "Height not detected"
        assert "fps" in properties, "FPS not detected"
        assert "bitrate" in properties, "Bitrate not estimated"

        # Since we know this specific file is 1280x720, verify those dimensions
        assert properties["width"] == 1280, (
            f"Incorrect width detected: {properties['width']}"
        )
        assert properties["height"] == 720, (
            f"Incorrect height detected: {properties['height']}"
        )

        # FPS should be a reasonable value (typically around 25-30 for this test video)
        assert 20 <= properties["fps"] <= 60, f"Unexpected FPS: {properties['fps']}"

        # Calculate expected bitrate range
        # For 1280x720 at 25fps with 0.08 bits per pixel:
        # 1280 * 720 * 25 * 0.08 / 1000 ≈ 1843 kbps
        # Allow some margin for different FPS values
        fps = properties["fps"]
        expected_bitrate = int(1280 * 720 * fps * 0.08 / 1000)
        margin = 100  # Allow some variance

        # Verify bitrate is within expected range
        assert (
            expected_bitrate - margin
            <= properties["bitrate"]
            <= expected_bitrate + margin
        ), (
            f"Unexpected bitrate: {properties['bitrate']}, expected around {expected_bitrate}"
        )

        print(f"Detected video properties: {properties}")
        print(f"Expected bitrate calculation: {expected_bitrate} kbps")

    finally:
        # Ensure resources are cleaned up properly
        if buffered_track:
            buffered_track.stop()
        # Give some time for cleanup
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_buffered_media_track():
    """Test that BufferedMediaTrack correctly buffers frames."""
    # Path to the test video file
    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Skip test if the file doesn't exist
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    player = None
    buffered_track = None

    try:
        # Create a media player from the file
        player = MediaPlayer(file_path)

        # Ensure we have a video track
        assert player.video is not None, "No video track found in test file"

        # Create a buffered track
        buffered_track = BufferedMediaTrack(player.video)

        # Peek at a frame - this should buffer the frame but not consume it
        frame1 = await buffered_track.peek()

        # Peek again should return the same frame without consuming it
        frame2 = await buffered_track.peek()
        assert frame1 is frame2, "Peeking multiple times should return the same frame"

        # Now receive a frame, which should be the one we peeked
        frame3 = await buffered_track.recv()
        assert frame1 is frame3, "Receiving after peek should return the peeked frame"

        # Receiving again should get a new frame since buffer is now empty
        frame4 = await buffered_track.recv()
        assert frame3 is not frame4, (
            "Receiving after consuming the buffer should get a new frame"
        )

        # Now let's get multiple frames in sequence to see if PTS values work as expected
        frame5 = await buffered_track.recv()
        frame6 = await buffered_track.recv()

        # Check if the frames have presentation timestamps
        assert hasattr(frame5, "pts"), "Frame should have a pts attribute"
        assert hasattr(frame6, "pts"), "Frame should have a pts attribute"
        assert hasattr(frame5, "time_base"), "Frame should have a time_base attribute"

        # If pts are properly set, the second frame's pts should be greater than the first
        if frame5.pts is not None and frame6.pts is not None:
            assert frame6.pts > frame5.pts, "Frame PTS should increase over time"

            # Calculate delta in seconds
            if hasattr(frame5, "time_base") and frame5.time_base:
                delta_ticks = frame6.pts - frame5.pts
                delta_seconds = delta_ticks * frame5.time_base
                estimated_fps = int(1 / delta_seconds) if delta_seconds > 0 else 0

                # For a normal video, this should be a reasonable FPS value
                assert 20 <= estimated_fps <= 60, (
                    f"Calculated FPS ({estimated_fps}) outside expected range"
                )
                print(f"Calculated FPS from frames: {estimated_fps}")

    finally:
        # Ensure resources are cleaned up properly
        if buffered_track:
            buffered_track.stop()
        # Give some time for cleanup
        await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_prepare_video_track_info(client: Stream):
    """Test that prepare_video_track_info correctly processes a video track."""
    # Path to the test video file
    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Skip test if the file doesn't exist
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    player = None
    buffered_track = None
    connection = None

    try:
        # Create a media player from the file
        player = MediaPlayer(file_path)

        # Ensure we have a video track
        assert player.video is not None, "No video track found in test file"

        # Create a connection manager
        call = client.video.call("default", "video-props-test-prepare")
        connection = await rtc.join(call, "test-user")

        # Test the prepare_video_track_info method
        track_info, buffered_track = await connection.prepare_video_track_info(
            player.video
        )

        # Verify the returned values
        assert track_info is not None, "Track info not returned"
        assert buffered_track is not None, "Buffered track not returned"

        # Verify track_info fields
        assert track_info.track_type == TRACK_TYPE_VIDEO, "Incorrect track type"
        assert len(track_info.layers) == 1, "Expected one video layer"

        layer = track_info.layers[0]
        assert layer.video_dimension.width == 1280, (
            f"Incorrect width: {layer.video_dimension.width}"
        )
        assert layer.video_dimension.height == 720, (
            f"Incorrect height: {layer.video_dimension.height}"
        )
        assert 20 <= layer.fps <= 60, f"Unexpected FPS: {layer.fps}"

        # Verify that the buffered track wraps the original track
        assert buffered_track.id == player.video.id, "Track ID mismatch"
        assert buffered_track.kind == "video", "Track kind mismatch"

        print(f"Track info: {track_info}")
        print(
            f"Video layer properties: width={layer.video_dimension.width}, height={layer.video_dimension.height}, fps={layer.fps}, bitrate={layer.bitrate}"
        )

    finally:
        # Clean up resources
        if buffered_track:
            buffered_track.stop()
        if connection and connection.running:
            await connection.leave()
        # Give some time for cleanup
        await asyncio.sleep(0.1)
