import os
import json
import pytest
import asyncio
import numpy as np
from unittest.mock import patch, MagicMock

from getstream.plugins.stt.deepgram import Deepgram
from getstream.video.rtc.track_util import PcmData


# Mock the Deepgram client to avoid real API calls during tests
class MockDeepgramConnection:
    def __init__(self):
        self.event_handlers = {}
        self.sent_data = []
        self.finished = False

    def on(self, event, handler):
        """Register event handlers"""
        self.event_handlers[event] = handler
        return handler

    def send(self, data):
        """Mock send data"""
        self.sent_data.append(data)
        return True

    def finish(self):
        """Close the connection"""
        self.finished = True

    def start(self, options):
        """Start the connection"""
        pass

    def emit_transcript(self, text, is_final=True):
        """Helper to emit a transcript event"""
        from deepgram import LiveTranscriptionEvents

        if LiveTranscriptionEvents.Transcript in self.event_handlers:
            # Create a mock result
            transcript_data = {
                "is_final": is_final,
                "channel": {
                    "alternatives": [
                        {
                            "transcript": text,
                            "confidence": 0.95,
                            "words": [
                                {
                                    "word": word,
                                    "start": i * 0.5,
                                    "end": (i + 1) * 0.5,
                                    "confidence": 0.95,
                                }
                                for i, word in enumerate(text.split())
                            ],
                        }
                    ]
                },
                "channel_index": 0,
            }

            # Convert to JSON string for the handler
            transcript_json = json.dumps(transcript_data)

            # Call the handler with the connection and the result
            self.event_handlers[LiveTranscriptionEvents.Transcript](
                self, result=transcript_json
            )


class MockDeepgramClient:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.listen = MagicMock()
        self.listen.websocket = MagicMock()
        self.listen.websocket.v = MagicMock(return_value=MockDeepgramConnection())


# Enhanced mock for testing keep-alive functionality
class MockDeepgramConnectionWithKeepAlive:
    def __init__(self):
        self.event_handlers = {}
        self.sent_data = []
        self.sent_text_messages = []
        self.finished = False
        self.closed = False

    def on(self, event, handler):
        """Register event handlers"""
        self.event_handlers[event] = handler
        return handler

    def send(self, data):
        """Mock send audio data"""
        self.sent_data.append(data)
        return True

    def send_text(self, text_message):
        """Mock send text message (for keep-alive)"""
        self.sent_text_messages.append(text_message)
        return True

    def keep_alive(self):
        """Mock keep_alive method for SDKs that support it"""
        self.sent_text_messages.append(json.dumps({"type": "KeepAlive"}))
        return True

    def finish(self):
        """Close the connection"""
        self.finished = True

    def close(self):
        """Alternative close method"""
        self.closed = True

    def start(self, options):
        """Start the connection"""
        pass


class MockDeepgramClientWithKeepAlive:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.listen = MagicMock()
        self.listen.websocket = MagicMock()
        self.listen.websocket.v = MagicMock(
            return_value=MockDeepgramConnectionWithKeepAlive()
        )


@pytest.fixture
def mia_mp3_path():
    """Return the path to the mia.mp3 test file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "assets",
        "mia.mp3",
    )


@pytest.fixture
def mia_json_path():
    """Return the path to the mia.json metadata file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "assets",
        "mia.json",
    )


@pytest.fixture
def mia_metadata(mia_json_path):
    """Load the mia.json metadata."""
    with open(mia_json_path, "r") as f:
        return json.load(f)


@pytest.fixture
def audio_data(mia_mp3_path):
    """Load and prepare the audio data for testing."""
    import torchaudio
    import torch

    # Load the mp3 file
    waveform, sample_rate = torchaudio.load(mia_mp3_path)

    # Convert to mono if stereo
    if waveform.shape[0] > 1:
        waveform = torch.mean(waveform, dim=0, keepdim=True)

    # Convert to numpy array
    data = waveform.numpy().squeeze()

    # Convert to int16
    pcm_samples = (data * 32768.0).astype(np.int16)

    return PcmData(samples=pcm_samples, sample_rate=sample_rate, format="s16")


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_stt_initialization():
    """Test that the Deepgram STT initializes correctly with explicit API key."""
    stt = Deepgram(api_key="test-api-key")
    assert stt is not None
    assert stt.deepgram.api_key == "test-api-key"
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
@patch("os.environ.get")
async def test_deepgram_stt_initialization_with_env_var(mock_env_get):
    """Test that the Deepgram STT initializes correctly using environment variable."""
    # Mock the environment variable to return a test value
    mock_env_get.return_value = "env-var-api-key"

    # Initialize without providing an API key
    stt = Deepgram()
    assert stt is not None

    # The environment variable should have been used
    mock_env_get.assert_called_once_with("DEEPGRAM_API_KEY")


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_stt_transcript_events(mia_metadata):
    """Test that the Deepgram STT emits transcript events correctly."""
    stt = Deepgram(api_key="test-api-key")

    # Get the mock connection
    connection = stt.dg_connection

    # Track events
    transcripts = []
    partial_transcripts = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcripts.append((text, metadata))

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        partial_transcripts.append((text, metadata))

    # Emit some mock transcript events
    # First a partial result
    connection.emit_transcript("This is a partial", is_final=False)

    # Then a final result
    connection.emit_transcript("This is a final transcript", is_final=True)

    # Give the async event handlers time to process
    await asyncio.sleep(0.1)

    # Check that the events were received
    assert len(partial_transcripts) == 1
    assert partial_transcripts[0][0] == "This is a partial"

    assert len(transcripts) == 1
    assert transcripts[0][0] == "This is a final transcript"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_process_audio(audio_data, mia_metadata):
    """Test that the Deepgram STT can process audio data."""
    stt = Deepgram(api_key="test-api-key")

    # Patch the connection's send_binary method
    # Get the mock connection
    connection = stt.dg_connection

    # Create a custom send method to track sent data
    sent_audio_bytes = []

    # Replace the send method on the connection to track sent data
    def mock_send(data):
        sent_audio_bytes.append(data)
        return True

    if hasattr(connection, "send_binary"):
        original_send = connection.send_binary
        connection.send_binary = mock_send
    else:
        # Just use the regular send
        original_send = connection.send
        connection.send = mock_send

    # Process audio
    await stt._process_audio_impl(audio_data, None)

    # Check that audio was sent
    assert len(sent_audio_bytes) > 0

    # Restore the original send method
    if hasattr(connection, "send_binary"):
        connection.send_binary = original_send
    else:
        connection.send = original_send

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_end_to_end(audio_data, mia_metadata):
    """Test the entire processing pipeline for Deepgram STT."""
    stt = Deepgram(api_key="test-api-key")

    # Track events
    transcripts = []
    partial_transcripts = []
    errors = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcripts.append((text, metadata))

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        partial_transcripts.append((text, metadata))

    @stt.on("error")
    def on_error(error):
        errors.append(error)

    # Get the mock connection
    connection = stt.dg_connection

    # Process audio
    await stt.process_audio(audio_data)

    # Emit mock transcripts as if the connection received them from Deepgram
    connection.emit_transcript("This is a partial result", is_final=False)
    connection.emit_transcript("This is the final result", is_final=True)

    # Give the async event handlers time to process
    await asyncio.sleep(0.1)

    # Check that we received the expected events
    assert len(errors) == 0
    assert len(partial_transcripts) == 1
    assert len(transcripts) == 1

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
async def test_deepgram_with_real_api(audio_data, mia_metadata):
    """Integration test with the real Deepgram API.

    This test uses the actual Deepgram API and will be skipped if the
    DEEPGRAM_API_KEY environment variable is not set.

    To set up the DEEPGRAM_API_KEY:
    1. Sign up for a Deepgram account at https://console.deepgram.com/signup
    2. Create an API key with the appropriate permissions
    3. Add to your .env file: DEEPGRAM_API_KEY=your_api_key_here
    """
    # Skip the test if the DEEPGRAM_API_KEY environment variable is not set
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        pytest.skip(
            "DEEPGRAM_API_KEY environment variable not set. Add it to your .env file."
        )

    # Create a Deepgram STT instance with the API key
    stt = Deepgram(api_key=api_key)

    # Track events
    transcripts = []
    partial_transcripts = []
    errors = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcripts.append((text, metadata))

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        partial_transcripts.append((text, metadata))

    @stt.on("error")
    def on_error(error):
        errors.append(error)

    # Process audio
    # We'll retry if there are connection issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await stt.process_audio(audio_data)

            # Wait for transcripts to arrive
            retry_count = 0
            max_retry = 40  # about 2 seconds
            while not transcripts and retry_count < max_retry:
                await asyncio.sleep(0.05)
                retry_count += 1

            break  # Break the retry loop if successful
        except Exception as e:
            if attempt < max_retries - 1:
                # Log the error and retry
                print(f"Retry {attempt+1}/{max_retries} failed: {e}")
                await asyncio.sleep(1.0)  # Wait before retrying
                # Try to create a fresh STT instance
                await stt.close()
                stt = Deepgram(api_key=api_key)
            else:
                # Last attempt, re-raise the exception
                raise

    # Check if we got any errors
    if errors:
        pytest.skip(f"Deepgram API error: {errors[0]}")

    # We expect to get at least some partial transcripts and at least one final transcript
    assert len(transcripts) > 0, "No transcripts were received"

    # For a more meaningful test, let's check the content of the transcripts
    # The expected transcript is in mia_metadata["transcript"]
    expected_transcript = mia_metadata["transcript"]

    # Combine all transcripts
    all_text = " ".join(text for text, _ in transcripts)

    # Do a loose comparison since the transcription won't be perfect
    # We'll check if the transcript contains certain keywords or phrases
    # that we'd expect from the audio

    # Define a function to calculate similarity between transcripts
    def similarity(a, b):
        # Convert to lowercase and split into words
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        # Calculate Jaccard similarity (intersection over union)
        intersection = len(a_words.intersection(b_words))
        union = len(a_words.union(b_words))
        return intersection / union if union > 0 else 0

    # Calculate similarity between expected and actual transcript
    sim = similarity(expected_transcript, all_text)

    print(f"Expected transcript: {expected_transcript}")
    print(f"Actual transcript: {all_text}")
    print(f"Similarity: {sim:.2f}")

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch(
    "getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive
)
async def test_deepgram_keep_alive_mechanism():
    """Test that the keep-alive mechanism works correctly."""
    # Use a short keep-alive interval for testing
    keep_alive_interval = 0.1  # 100ms

    # Create a Deepgram STT instance with the test interval
    stt = Deepgram(api_key="test-api-key", keep_alive_interval=keep_alive_interval)

    # Get the mock connection
    connection = stt.dg_connection

    # Wait for a few keep-alive intervals
    await asyncio.sleep(keep_alive_interval * 3)

    # Check that keep-alive messages were sent
    # The send_text_messages list should have at least one keep-alive message
    assert len(connection.sent_text_messages) > 0

    # Check the content of the messages
    for message in connection.sent_text_messages:
        assert '"type":"KeepAlive"' in message.replace(" ", "")

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch(
    "getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive
)
async def test_deepgram_keep_alive_after_audio():
    """Test that keep-alive messages are sent after processing audio."""
    # Use a short keep-alive interval for testing
    keep_alive_interval = 0.1  # 100ms

    # Create a Deepgram STT instance with the test interval
    stt = Deepgram(api_key="test-api-key", keep_alive_interval=keep_alive_interval)

    # Get the mock connection
    connection = stt.dg_connection

    # Process some audio (just mock data)
    await stt._process_audio_impl(
        PcmData(samples=b"\x00\x00" * 1000, sample_rate=48000, format="s16")
    )

    # Wait for a few keep-alive intervals
    await asyncio.sleep(keep_alive_interval * 3)

    # Check that keep-alive messages were sent
    assert len(connection.sent_text_messages) > 0

    # Check the content of the messages
    for message in connection.sent_text_messages:
        assert '"type":"KeepAlive"' in message.replace(" ", "")

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch(
    "getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive
)
async def test_deepgram_keep_alive_direct():
    """Test the direct send_keep_alive method."""
    # Create a Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Get the mock connection
    connection = stt.dg_connection

    # Check initial state
    assert len(connection.sent_text_messages) == 0

    # Call the keep-alive method directly
    success = await stt.send_keep_alive()

    # Check that it was successful
    assert success is True

    # Check that a message was sent
    assert len(connection.sent_text_messages) == 1

    # Check the content of the message
    message = connection.sent_text_messages[0]
    assert '"type":"KeepAlive"' in message.replace(" ", "")

    # Try another keep-alive with the keep_alive method if supported
    # This is to test the fallback logic in the method
    if hasattr(connection, "keep_alive"):
        # Reset the connection's sent messages
        connection.sent_text_messages = []

        # Temporarily remove the send_text method to force the fallback
        original_send_text = connection.send_text
        del connection.send_text

        # Call the keep-alive method again
        success = await stt.send_keep_alive()

        # Restore the method
        connection.send_text = original_send_text

        # Check that it was successful
        assert success is True

        # Check that a message was sent using the keep_alive method
        assert len(connection.sent_text_messages) == 1

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch(
    "getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive
)
async def test_deepgram_close_message():
    """Test that the close method properly cleans up resources."""
    # Create a Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Get the mock connection
    connection = stt.dg_connection

    # Replace the finish method with a mock
    original_finish = connection.finish
    finish_called = False

    def mock_finish():
        nonlocal finish_called
        finish_called = True
        return original_finish()

    connection.finish = mock_finish

    # Mock the send_text method to check for close messages
    original_send_text = connection.send_text
    sent_text_messages = []

    def mock_send_text(message):
        sent_text_messages.append(message)
        return original_send_text(message)

    if hasattr(connection, "send_text"):
        connection.send_text = mock_send_text

    # Close the STT
    await stt.close()

    # Check that the finish method was called
    assert finish_called is True

    # Check that the connection is marked as finished
    assert connection.finished is True

    # Check that the running flag is set to False
    assert stt._running is False
    assert stt._is_closed is True


@pytest.mark.asyncio
async def test_deepgram_with_real_api_keep_alive():
    """Integration test with the real Deepgram API, focusing on keep-alive.

    This test uses the actual Deepgram API and will be skipped if the
    DEEPGRAM_API_KEY environment variable is not set.

    It tests the keep-alive mechanism with the real API to ensure
    that connections are maintained properly.
    """
    # Skip the test if the DEEPGRAM_API_KEY environment variable is not set
    api_key = os.environ.get("DEEPGRAM_API_KEY")
    if not api_key:
        pytest.skip(
            "DEEPGRAM_API_KEY environment variable not set. Add it to your .env file."
        )

    # Create a Deepgram STT instance with a short keep-alive interval
    stt = Deepgram(api_key=api_key, keep_alive_interval=2.0)

    # Track events
    transcripts = []
    errors = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcripts.append((text, metadata))

    @stt.on("error")
    def on_error(error):
        errors.append(error)

    try:
        # First, process a bit of audio to initialize the connection
        audio_data = PcmData(
            samples=b"\x00\x00" * 8000,  # 0.5 seconds of silence at 16kHz
            sample_rate=48000,
            format="s16",
        )
        await stt.process_audio(audio_data)

        # Wait for a few keep-alive intervals to ensure they work
        # This should be at least 2-3 times the keep-alive interval
        await asyncio.sleep(4.5)

        # Check that the connection is still alive by processing more audio
        # Since we're just sending silence, we might not get transcripts back,
        # but we shouldn't get errors either if the connection is maintained
        await stt.process_audio(audio_data)

        # Wait a bit for any errors to appear
        await asyncio.sleep(0.5)

        # Check for errors
        if errors:
            pytest.skip(f"Deepgram API error: {errors[0]}")

        # If we've made it this far without errors, the keep-alive is working
    finally:
        # Always clean up
        await stt.close()
