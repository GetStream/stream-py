import os
import json
import pytest
import asyncio
import numpy as np
from unittest.mock import patch, MagicMock

from getstream.agents.deepgram.stt import Deepgram
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
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "mia.mp3")


@pytest.fixture
def mia_json_path():
    """Return the path to the mia.json metadata file."""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "assets", "mia.json"
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
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_stt_initialization():
    """Test that the Deepgram STT initializes correctly with explicit API key."""
    stt = Deepgram(api_key="test-api-key")
    assert stt is not None
    assert stt.deepgram.api_key == "test-api-key"
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClient)
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

    await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_stt_transcript_events(mia_metadata):
    """Test that the Deepgram STT emits transcript events."""
    # Create STT without specifying API key
    stt = Deepgram()

    # Extract expected text from metadata
    expected_text = " ".join([segment["text"] for segment in mia_metadata["segments"]])

    # Track received transcripts
    received_transcripts = []
    received_partials = []
    transcript_event = asyncio.Event()

    # Set up event handlers
    @stt.on("transcript")
    def on_transcript(text, metadata):
        received_transcripts.append(text)
        transcript_event.set()

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        received_partials.append(text)

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Process audio with a dummy PcmData object to trigger the processing flow
        dummy_audio = np.zeros(1600, dtype=np.int16)  # 0.1s of silence at 16kHz
        dummy_pcm = PcmData(samples=dummy_audio, sample_rate=16000, format="s16")

        # Create a task for processing and emit transcript first
        # This ensures the transcript is ready to be processed
        mock_connection.emit_transcript(expected_text)

        # Now process the audio
        process_task = asyncio.create_task(stt.process_audio(dummy_pcm))

        # Wait for the transcript event or timeout
        try:
            await asyncio.wait_for(transcript_event.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pytest.fail("No transcript event received within timeout")

        # Ensure the process_audio task is completed
        await process_task

        # Verify that we received a transcript
        assert len(received_transcripts) > 0, "No transcripts were received"
        assert (
            received_transcripts[0] == expected_text
        ), "Transcript text doesn't match expected"

    finally:
        await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_process_audio(audio_data, mia_metadata):
    """Test processing audio data with Deepgram STT."""
    # Create STT without specifying API key
    stt = Deepgram()

    # Track processing completion
    processing_done = asyncio.Event()

    # Track sent data
    audio_processed = False

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Check that audio data is sent to Deepgram
        original_send = mock_connection.send

        def mock_send(data):
            nonlocal audio_processed
            result = original_send(data)
            audio_processed = True
            processing_done.set()
            return result

        mock_connection.send = mock_send

        # Process audio data
        await stt.process_audio(audio_data)

        # Wait for processing to complete or timeout
        try:
            await asyncio.wait_for(processing_done.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            pytest.fail("Audio processing didn't complete within timeout")

        # Verify audio was processed
        assert audio_processed, "Audio data was not sent to Deepgram"
        assert len(mock_connection.sent_data) > 0, "No data was sent to Deepgram"

    finally:
        await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_deepgram_end_to_end(audio_data, mia_metadata):
    """Test end-to-end flow with Deepgram STT."""
    # Create STT without specifying API key
    stt = Deepgram()

    # Extract expected text from metadata
    expected_text = " ".join([segment["text"] for segment in mia_metadata["segments"]])

    # Track transcript events
    received_transcripts = []
    received_partials = []
    transcript_event = asyncio.Event()

    @stt.on("transcript")
    def on_transcript(text, metadata):
        received_transcripts.append(text)
        transcript_event.set()

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        received_partials.append(text)

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Start a task to process the audio
        process_task = asyncio.create_task(stt.process_audio(audio_data))

        # Emit a transcript (simulate Deepgram response)
        mock_connection.emit_transcript(expected_text)

        # Wait for transcript events or timeout
        try:
            await asyncio.wait_for(transcript_event.wait(), timeout=3.0)
        except asyncio.TimeoutError:
            pytest.fail("No transcript event received within timeout")

        # Ensure process_audio task completes
        await process_task

        # Verify we received the transcript
        assert len(received_transcripts) > 0, "No transcripts were received"
        assert (
            received_transcripts[0] == expected_text
        ), "Transcript text doesn't match expected"

        # Verify audio was sent to Deepgram
        assert len(mock_connection.sent_data) > 0, "No data was sent to Deepgram"

    finally:
        await stt.close()


@pytest.mark.asyncio
async def test_deepgram_with_real_api(audio_data, mia_metadata):
    """
    Integration test with the real Deepgram API.

    This test uses the actual Deepgram API with the DEEPGRAM_API_KEY environment variable.
    It will be skipped if the environment variable is not set.

    To set up the DEEPGRAM_API_KEY:
    1. Sign up for a Deepgram account
    2. Create an API key in your Deepgram dashboard
    3. Add to your .env file: DEEPGRAM_API_KEY=your_api_key_here
    """
    # Skip the test if the DEEPGRAM_API_KEY environment variable is not set
    if "DEEPGRAM_API_KEY" not in os.environ:
        pytest.skip(
            "DEEPGRAM_API_KEY environment variable not set. Add it to your .env file."
        )

    # Extract expected text from metadata
    expected_text = " ".join([segment["text"] for segment in mia_metadata["segments"]])

    # Create a real Deepgram STT instance with the API key from environment variable
    stt = Deepgram()

    # Track received transcripts
    received_transcripts = []
    received_partials = []
    transcript_event = asyncio.Event()

    # Track API errors
    api_errors = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        received_transcripts.append(text)
        if len(received_transcripts) <= 1:
            # Set the event when we receive the first transcript
            transcript_event.set()

    @stt.on("partial_transcript")
    def on_partial(text, metadata):
        received_partials.append(text)

    @stt.on("error")
    def on_error(error):
        api_errors.append(error)
        transcript_event.set()  # Unblock the waiting

    try:
        # Process the audio data
        process_task = asyncio.create_task(stt.process_audio(audio_data))

        # Wait for transcript events or error
        try:
            await asyncio.wait_for(transcript_event.wait(), timeout=10.0)
        except asyncio.TimeoutError:
            if not api_errors:
                pytest.fail("No transcript or error received within timeout")

        # Now wait a bit longer to collect more transcripts
        # We need to give Deepgram time to process the entire audio file
        # This is necessary because Deepgram breaks down long audio into segments
        try:
            await asyncio.wait_for(process_task, timeout=10.0)
        except asyncio.TimeoutError:
            pass  # It's okay if processing takes longer

        # Give a little more time for any final transcripts to arrive
        await asyncio.sleep(2)

        # Check if we received any errors
        if api_errors:
            pytest.fail(f"API error received: {api_errors[0]}")

        # Verify we received transcripts
        assert len(received_transcripts) > 0, "No transcripts were received"

        # Print all received transcripts for debugging
        print(f"Received {len(received_transcripts)} transcript segments:")
        for i, text in enumerate(received_transcripts):
            print(f"  {i+1}: {text}")

        # Combine all received transcripts into a single text
        combined_transcript = " ".join(received_transcripts)
        print(f"Combined transcript: '{combined_transcript}'")

        # Check if the expected text is similar to the combined transcript
        def similarity(a, b):
            """Calculate similarity between two strings (case insensitive)."""
            from difflib import SequenceMatcher

            return SequenceMatcher(None, a.lower(), b.lower()).ratio()

        # Compare the combined transcript to the expected text
        similarity_score = similarity(combined_transcript, expected_text)
        print(f"Similarity score: {similarity_score:.2f}")

        # Use a more appropriate threshold for combined segments
        assert similarity_score > 0.6, (
            f"Combined transcript not similar enough to expected text.\n"
            f"Expected: '{expected_text}'\n"
            f"Got: '{combined_transcript}'"
        )

    finally:
        # Always clean up
        await stt.close()


# ===== Keep-Alive Functionality Tests =====


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive)
async def test_deepgram_keep_alive_mechanism():
    """Test that keep-alive messages are sent after periods of inactivity."""
    # Create Deepgram STT with shorter keep-alive interval for testing
    keep_alive_interval = 0.5  # 500ms for faster test execution
    stt = Deepgram(api_key="test-api-key", keep_alive_interval=keep_alive_interval)

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Verify the connection was set up
        assert stt.dg_connection is not None

        # Wait a bit longer than the keep-alive interval to ensure a message is sent
        await asyncio.sleep(keep_alive_interval * 2)

        # Verify at least one keep-alive message was sent
        assert len(mock_connection.sent_text_messages) > 0

        # Check that the message format matches what Deepgram expects
        sent_message = json.loads(mock_connection.sent_text_messages[0])
        assert sent_message["type"] == "KeepAlive"

        # Wait a bit longer to ensure multiple keep-alive messages are sent
        await asyncio.sleep(keep_alive_interval * 2)

        # Verify that more keep-alive messages were sent
        assert len(mock_connection.sent_text_messages) >= 2

    finally:
        await stt.close()

        # Verify that the keep-alive task was cancelled
        assert stt.keep_alive_task is None
        assert stt._running is False


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive)
async def test_deepgram_keep_alive_after_audio():
    """Test that keep-alive messages are sent after sending audio."""
    # Create Deepgram STT with shorter keep-alive interval for testing
    keep_alive_interval = 0.5  # 500ms for faster test execution
    stt = Deepgram(api_key="test-api-key", keep_alive_interval=keep_alive_interval)

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Create dummy audio data
        dummy_audio = np.zeros(1600, dtype=np.int16)  # 0.1s of silence at 16kHz
        dummy_pcm = PcmData(samples=dummy_audio, sample_rate=16000, format="s16")

        # Process the audio
        await stt.process_audio(dummy_pcm)

        # Verify audio was sent
        assert len(mock_connection.sent_data) > 0

        # Wait a bit longer than the keep-alive interval
        await asyncio.sleep(keep_alive_interval * 2)

        # Verify a keep-alive message was sent after the audio
        assert len(mock_connection.sent_text_messages) > 0

    finally:
        await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive)
async def test_deepgram_keep_alive_direct():
    """Test the send_keep_alive method directly."""
    # Create Deepgram STT
    stt = Deepgram(api_key="test-api-key")

    try:
        # Get the mock connection
        mock_client = stt.deepgram
        mock_connection = mock_client.listen.websocket.v.return_value

        # Call send_keep_alive directly
        result = await stt.send_keep_alive()

        # Verify the result
        assert result is True

        # Verify a keep-alive message was sent
        assert len(mock_connection.sent_text_messages) == 1

        # Check the message format
        sent_message = json.loads(mock_connection.sent_text_messages[0])
        assert sent_message["type"] == "KeepAlive"

    finally:
        await stt.close()


@pytest.mark.asyncio
@patch("getstream.agents.deepgram.stt.DeepgramClient", MockDeepgramClientWithKeepAlive)
async def test_deepgram_close_message():
    """Test that closing the STT sends a CloseStream message."""
    # Create Deepgram STT
    stt = Deepgram(api_key="test-api-key")

    # Get the mock connection
    mock_client = stt.deepgram
    mock_connection = mock_client.listen.websocket.v.return_value

    # Directly patch send_text to track calls
    original_send_text = mock_connection.send_text
    sent_messages = []

    def mock_send_text(message):
        sent_messages.append(message)
        return original_send_text(message)

    mock_connection.send_text = mock_send_text

    # Close the connection
    await stt.close()

    # Verify a CloseStream message was sent
    close_messages = [msg for msg in sent_messages if "CloseStream" in msg]
    assert len(close_messages) > 0


@pytest.mark.asyncio
async def test_deepgram_with_real_api_keep_alive():
    """
    Integration test with the real Deepgram API to verify keep-alive functionality.

    This test will:
    1. Connect to Deepgram
    2. Send initial audio
    3. Wait longer than 10 seconds (with keep-alive messages being sent)
    4. Send more audio
    5. Verify that the connection stayed open and could still process audio

    This test will be skipped if the DEEPGRAM_API_KEY environment variable is not set.
    """
    # Skip the test if the DEEPGRAM_API_KEY environment variable is not set
    if "DEEPGRAM_API_KEY" not in os.environ:
        pytest.skip(
            "DEEPGRAM_API_KEY environment variable not set. Add it to your .env file."
        )

    # Create a real Deepgram STT instance with shorter keep-alive interval
    stt = Deepgram(sample_rate=16000, keep_alive_interval=3.0)

    # This test should work with spoken words, not just tones
    # Generate a sine wave at 440Hz for 1 second, which should be more detectable
    duration_sec = 1.0
    sample_rate = 16000
    frequencies = [
        440,
        650,
    ]  # Multiple frequencies to make it more likely to trigger transcription

    # Create test audio with multiple frequencies - more likely to trigger transcription
    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), False)
    signal = np.zeros_like(t)
    for freq in frequencies:
        signal += np.sin(2 * np.pi * freq * t)

    # Normalize and convert to int16
    signal = (signal / len(frequencies) * 32767).astype(np.int16)
    audio_pcm = PcmData(samples=signal, sample_rate=sample_rate, format="s16")

    # Set flags to track events
    transcription_received = False
    connection_alive_after_pause = False
    error_occurred = False
    error_message = ""

    # Track connection state
    @stt.on("transcript")
    def on_transcript(text, metadata):
        nonlocal transcription_received
        print(f"Received transcript: '{text}'")
        transcription_received = True

    @stt.on("error")
    def on_error(error):
        nonlocal error_occurred, error_message
        error_occurred = True
        error_message = str(error)
        print(f"Error received: {error}")

    try:
        # Send audio
        print("Sending first audio sample...")
        await stt.process_audio(audio_pcm)

        # Check if we get any transcription results (might not get any since it's just tones)
        # but we want to ensure no errors occur
        for i in range(5):  # Check for up to 5 seconds
            await asyncio.sleep(1)
            if transcription_received or error_occurred:
                break

        # If we got an error, the test fails
        if error_occurred:
            pytest.fail(f"Error in first audio: {error_message}")

        # If we didn't get any transcription, that's ok for this test since it's
        # testing the keep-alive functionality, not transcription accuracy
        if not transcription_received:
            print(
                "No transcription received for first audio sample (expected with tones)"
            )

        # Wait longer than the 10-second Deepgram timeout
        # This is where keep-alive should maintain the connection
        print("Waiting for 12 seconds with keep-alive mechanism active...")
        await asyncio.sleep(12)

        # Send second audio sample to verify connection is still alive
        print("Sending second audio sample...")
        await stt.process_audio(audio_pcm)

        # This should work if the connection is still alive
        # Reset these flags
        error_occurred = False
        connection_alive_after_pause = True

        # Wait to see if we get an error (which would indicate connection closed)
        for i in range(5):  # Check for up to 5 seconds
            await asyncio.sleep(1)
            if error_occurred:
                connection_alive_after_pause = False
                break

        if error_occurred:
            pytest.fail(
                f"Error in second audio after keep-alive period: {error_message}"
            )

        # If we get here without errors, the keep-alive mechanism is working
        assert (
            connection_alive_after_pause
        ), "Connection not alive after keep-alive period"

    finally:
        # Always clean up
        await stt.close()
