import pytest
from getstream.stream import Stream
from getstream.video import rtc
from getstream.video.rtc import audio_track
import os  # Import os for path manipulation
import asyncio
import uuid
from multiprocessing import Process, Value
import time
from dotenv import load_dotenv
import logging
from typing import Callable, Any

from getstream.video.rtc.track_util import PcmData


CALL_ID = os.getenv("CALL_ID")


# Shared function for process setup and error handling
def run_process_with_stream_client(
    process_type: str,
    call_id: str,
    file_path: str,
    test_timeout: int,
    task_func: Callable[[Stream, Any, str, int, logging.Logger], Any],
    *args,
):
    """
    Common function to handle process setup for Stream client processes.

    Args:
        process_type: String identifier for the process ('SENDER' or 'RECEIVER')
        call_id: The call ID to join
        file_path: Path to the media file
        test_timeout: Timeout in seconds
        task_func: The specific task function to run in the process
        *args: Additional arguments to pass to the task function
    """

    async def _async_runner():
        import logging
        import sys
        from getstream.stream import Stream

        # Configure logging in this process
        logging.basicConfig(
            level=logging.INFO,
            format=f"[{process_type}] %(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )
        logger = logging.getLogger(f"{process_type.lower()}_process")

        # Ensure output is immediately visible
        sys.stdout.flush()
        sys.stderr.flush()

        # Load environment variables in this process
        load_dotenv()

        # Initialize client in this process - use the same env var names as in fixtures.py
        api_key = os.environ.get("STREAM_API_KEY")
        api_secret = os.environ.get("STREAM_API_SECRET")

        if not api_key or not api_secret:
            print(
                f"[{process_type}] Error: API credentials not found in environment variables",
                flush=True,
            )
            print(
                f"[{process_type}] Environment vars: {list(os.environ.keys())}",
                flush=True,
            )
            raise ValueError(
                "API credentials not found. Make sure STREAM_API_KEY and STREAM_API_SECRET are set."
            )

        client = Stream(api_key=api_key, api_secret=api_secret)

        logger.info(f"Starting {process_type.lower()} process")
        try:
            # Run the specific task function
            await task_func(client, call_id, file_path, test_timeout, logger, *args)
        except Exception as e:
            logger.error(f"Error in {process_type.lower()} process: {e}")
            import traceback

            logger.error(traceback.format_exc())

    # Run the async function in this process
    asyncio.run(_async_runner())


# Specific task for the receiver process
async def receiver_task(
    client: Stream,
    call_id: str,
    file_path: str,
    test_timeout: int,
    logger: logging.Logger,
    received_flag: Value,
):
    """Task function for the receiver process."""
    call = client.video.call("default", call_id)
    async with await rtc.join(call, "test-user") as connection:
        logger.info("Connected to call")

        @connection.on("audio")
        async def audio_handler(pcm: PcmData, participant):
            logger.info(
                f"Audio event received: {len(pcm.samples)} bytes of PCM data from {participant}"
            )
            # Set the shared flag to indicate audio was received
            received_flag.value = 1
            # Leave the call
            await connection.leave()

        # Wait for audio event or timeout
        try:
            await asyncio.wait_for(connection.wait(), timeout=test_timeout)
            logger.info("Connection ended normally")
        except asyncio.TimeoutError:
            logger.info("Timed out waiting for audio")
        finally:
            if not connection._stop_event.is_set():
                await connection.leave()
            logger.info("Receiver process complete")


# Specific task for the sender process
async def sender_task(
    client: Stream,
    call_id: str,
    file_path: str,
    test_timeout: int,
    logger: logging.Logger,
):
    """Task function for the sender process."""
    from aiortc.contrib.media import MediaPlayer

    # Create media player
    player = MediaPlayer(file_path)

    call = client.video.call("default", call_id)
    async with await rtc.join(call, "test-user") as connection:
        logger.info("Connected to call, adding audio track")
        await connection.add_tracks(audio=player.audio)

        # Wait for a while to ensure audio is sent
        try:
            await asyncio.sleep(test_timeout)
            logger.info("Sender finished waiting")
        finally:
            await connection.leave()
            logger.info("Sender process complete")


# Function to run the receiver in a separate process - defined at module level
def run_receiver(call_id, received_flag, file_path, test_timeout):
    run_process_with_stream_client(
        "RECEIVER", call_id, file_path, test_timeout, receiver_task, received_flag
    )


# Function to run the sender in a separate process - defined at module level
def run_sender(call_id, file_path, test_timeout):
    run_process_with_stream_client(
        "SENDER", call_id, file_path, test_timeout, sender_task
    )


@pytest.mark.asyncio
async def test_join_and_leave(client: Stream):
    call = client.video.call("default", "test-join")

    async with await rtc.join(call, "test-user") as connection:
        await connection.leave()
        await connection.wait()


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_join_two_users(client: Stream):
    """Test end-to-end audio transmission between two users in the same call.

    Uses separate processes for sender and receiver to ensure complete isolation.
    """

    # Configure logging in the main process
    logger = logging.getLogger("test_join_two_users")

    # Create a unique call ID for this test
    call_id = f"test-audio-{uuid.uuid4()}"
    logger.info(f"Using call ID: {call_id}")

    # Path to the test media file
    file_path = "/Users/tommaso/src/data-samples/video/SampleVideo_1280x720_30mb.mp4"

    # Check if file exists before running test, skip if not
    if not os.path.exists(file_path):
        pytest.skip(f"Test media file not found at {file_path}")

    # Shared variable to track audio reception across processes
    received_audio = Value("i", 0)

    # Set timeout for the entire test (seconds)
    test_timeout = 20

    # Create and start the receiver process first, explicitly connecting to parent's stdout/stderr
    receiver_process = Process(
        target=run_receiver,
        args=(call_id, received_audio, file_path, test_timeout),
        daemon=True,  # Ensure process is killed if parent exits
    )
    receiver_process.start()
    logger.info(f"Started receiver process (PID: {receiver_process.pid})")

    # Wait briefly to ensure receiver is connected
    await asyncio.sleep(3)

    # Create and start the sender process, explicitly connecting to parent's stdout/stderr
    sender_process = Process(
        target=run_sender,
        args=(call_id, file_path, test_timeout),
        daemon=True,  # Ensure process is killed if parent exits
    )
    sender_process.start()
    logger.info(f"Started sender process (PID: {sender_process.pid})")

    # Wait for both processes to complete or timeout
    start_time = time.time()
    while time.time() - start_time < test_timeout:
        # If audio was received, we can exit early
        if received_audio.value == 1:
            logger.info("Audio received, ending test")
            break

        # Check if processes are still running
        if not receiver_process.is_alive() and not sender_process.is_alive():
            logger.info("Both processes completed")
            break

        await asyncio.sleep(0.5)

    # Clean up processes
    for process in [receiver_process, sender_process]:
        if process.is_alive():
            logger.info(f"Terminating process {process.pid}")
            process.terminate()
            process.join(timeout=2)

    # Assert that audio was received
    assert received_audio.value == 1, "No audio event was received"


@pytest.mark.asyncio
async def test_detect_video_properties(client: Stream):
    from aiortc.contrib.media import MediaPlayer
    from getstream.video.rtc.track_util import (
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

    call = client.video.call("default", CALL_ID)

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

        await asyncio.sleep(10)


@pytest.mark.asyncio
async def test_play_audio_track_from_text(client: Stream):
    from getstream.plugins.tts.elevenlabs import ElevenLabs

    audio = audio_track.AudioStreamTrack(framerate=16000)
    tts_instance = ElevenLabs(voice_id="JBFqnCBsd6RMkjVDRZzb")
    tts_instance.set_output_track(audio)
    call = client.video.call("default", CALL_ID)

    async with await rtc.join(call, "test-user") as connection:
        # TODO: make connection.add_tracks block until the track is ready
        await connection.add_tracks(
            audio=audio,
        )

        await tts_instance.send("hey how is it going?")

        await tts_instance.send("do you think Stream is awesome so far?")

        await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_full_echo(client: Stream):
    from getstream.plugins.vad.silero import Silero
    from getstream.plugins.stt.deepgram import Deepgram
    from getstream.plugins.tts.elevenlabs import ElevenLabs

    audio = audio_track.AudioStreamTrack(framerate=16000)
    vad = Silero()
    stt = Deepgram()
    call = client.video.call("default", "mQbx3HG7wtTj")
    tts_instance = ElevenLabs(voice_id="zOImbcIGBTxd0yXmwgRi")
    tts_instance.set_output_track(audio)

    async with await rtc.join(call, "test-user") as connection:
        await connection.add_tracks(
            audio=audio,
        )

        await tts_instance.send("welcome my friend, how's it going?")

        @connection.on("*")
        @connection.on("call.*")
        @connection.on("audio")
        async def on_audio(pcm: PcmData, user):
            await vad.process_audio(pcm, user)

        @vad.on("audio")
        async def on_speech_detected(pcm: PcmData, user):
            print(
                f"{time.time()} Speech detected from user: {user} duration {pcm.duration}"
            )
            await stt.process_audio(pcm, None)

        @stt.on("transcript")
        async def on_transcript(text: str, user: Any, metadata: dict[str, Any]):
            print(
                f"{time.time()} got text from audio, will echo back the transcript {text}"
            )
            await tts_instance.send(text)

        await asyncio.sleep(30)


@pytest.mark.asyncio
async def test_simple_capture(client: Stream):
    call = client.video.call("default", CALL_ID)
    async with await rtc.join(call, "test-user") as connection:

        @connection.on("audio")
        async def on_audio(pcm: PcmData, user):
            print("got audio")

        await asyncio.sleep(10)
