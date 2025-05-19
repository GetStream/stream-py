import asyncio
import logging
import os
import sys
import uuid

# Add project root to path for easier imports in examples
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from getstream.stream import Stream
from getstream.video import rtc
from getstream.plugins.vad.silero import Silero

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("vad_example")


async def main():
    """
    Example showing how to use VAD with Stream's RTC connection manager.

    This example:
    1. Creates a VAD instance
    2. Joins a Stream video call
    3. Connects the connection's audio events to the VAD
    4. Listens for speech segments detected by the VAD
    """
    # Initialize the Stream client
    # Either set STREAM_API_KEY and STREAM_API_SECRET environment variables,
    # or replace these with your actual keys
    api_key = os.environ.get("STREAM_API_KEY")
    api_secret = os.environ.get("STREAM_API_SECRET")

    if not api_key or not api_secret:
        logger.error(
            "Please set STREAM_API_KEY and STREAM_API_SECRET environment variables"
        )
        return

    client = Stream(api_key=api_key, api_secret=api_secret)

    # Create a unique call ID or use an existing one
    call_id = str(uuid.uuid4())
    logger.info(f"Using call ID: {call_id}")

    # Get the call
    call = client.video.call("default", call_id)

    # Create a Silero VAD instance
    vad = Silero()

    # Set up a listener for speech segments
    speech_segments = []

    @vad.on("audio")
    async def on_speech_detected(pcm_data, user):
        """Handle speech detected by the VAD."""
        # Calculate duration in seconds
        num_samples = len(pcm_data) // 2  # 2 bytes per sample in int16
        duration = num_samples / vad.sample_rate

        # Log the detected speech
        if user:
            logger.info(
                f"Speech detected from {user.get('user_id', 'unknown')}: {duration:.2f} seconds"
            )
        else:
            logger.info(f"Speech detected: {duration:.2f} seconds")

        # Store the speech segment
        speech_segments.append(
            {"duration": duration, "bytes": len(pcm_data), "user": user}
        )

    # Join the call
    try:
        async with await rtc.join(call, "vad-example-user") as connection:
            logger.info("Connected to call")

            # Set up a listener for raw audio from the call
            @connection.on("audio")
            async def on_audio(pcm_data, user):
                # Forward the audio to the VAD for speech detection
                await vad.process_audio(pcm_data, user)

            # Wait for the connection to end (either by timeout or manual intervention)
            logger.info("Listening for speech. Press Ctrl+C to exit.")
            try:
                # Run for a maximum of 5 minutes
                await asyncio.wait_for(connection.wait(), timeout=300)
            except asyncio.TimeoutError:
                logger.info("Connection timeout reached")

    except Exception as e:
        logger.error(f"Error in connection: {e}")
    finally:
        # Close the VAD to free resources
        await vad.close()

    # Print summary of detected speech segments
    logger.info(f"Detected {len(speech_segments)} speech segments")
    total_duration = sum(segment["duration"] for segment in speech_segments)
    logger.info(f"Total speech duration: {total_duration:.2f} seconds")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Example stopped by user")
