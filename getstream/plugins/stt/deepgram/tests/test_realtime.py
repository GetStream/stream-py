import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from getstream.plugins.stt.deepgram import Deepgram
from getstream.video.rtc.track_util import PcmData


# Mock the Deepgram client for testing real-time transcript emission
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


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_real_time_transcript_emission():
    """
    Test that transcripts are emitted in real-time without needing a second audio chunk.

    This test verifies that:
    1. A transcript can be emitted immediately after receiving it from the server
    2. The background dispatcher correctly processes items in the queue
    3. The events are properly emitted to listeners
    """
    # Create the Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Collection for events
    transcript_events = []
    partial_transcript_events = []
    error_events = []

    # Register event handlers
    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcript_events.append((text, metadata))

    @stt.on("partial_transcript")
    def on_partial_transcript(text, metadata):
        partial_transcript_events.append((text, metadata))

    @stt.on("error")
    def on_error(error):
        error_events.append(error)

    # Send some audio data to ensure the connection is active
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Immediately trigger a transcript from the server
    stt.dg_connection.emit_transcript("hello world", is_final=True)

    # Wait a small amount of time for the background dispatcher to process the event
    await asyncio.sleep(0.05)

    # Check that we received the transcript event
    assert len(transcript_events) == 1, "Expected 1 transcript event"
    assert transcript_events[0][0] == "hello world", "Incorrect transcript text"
    assert transcript_events[0][1]["is_final"], "Transcript should be marked as final"

    # No errors should have occurred
    assert len(error_events) == 0, f"Unexpected errors: {error_events}"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_real_time_partial_transcript_emission():
    """
    Test that partial transcripts are emitted in real-time.
    """
    # Create the Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Collection for events
    transcript_events = []
    partial_transcript_events = []

    # Register event handlers
    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcript_events.append((text, metadata))

    @stt.on("partial_transcript")
    def on_partial_transcript(text, metadata):
        partial_transcript_events.append((text, metadata))

    # Send some audio data to ensure the connection is active
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Emit a partial transcript
    stt.dg_connection.emit_transcript("typing in prog", is_final=False)

    # Wait a small amount of time for the background dispatcher
    await asyncio.sleep(0.05)

    # Emit another partial transcript
    stt.dg_connection.emit_transcript("typing in progress", is_final=False)

    # Wait again
    await asyncio.sleep(0.05)

    # Emit the final transcript
    stt.dg_connection.emit_transcript("typing in progress complete", is_final=True)

    # Wait a small amount of time for the background dispatcher to process the events
    await asyncio.sleep(0.05)

    # Check that we received the partial transcript events
    assert len(partial_transcript_events) == 2, "Expected 2 partial transcript events"
    assert (
        partial_transcript_events[0][0] == "typing in prog"
    ), "Incorrect partial transcript text"
    assert (
        partial_transcript_events[1][0] == "typing in progress"
    ), "Incorrect partial transcript text"

    # Check that we received the final transcript event
    assert len(transcript_events) == 1, "Expected 1 final transcript event"
    assert (
        transcript_events[0][0] == "typing in progress complete"
    ), "Incorrect final transcript text"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_real_time_error_emission():
    """
    Test that errors are emitted in real-time.
    """
    # Create the Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Collection for events
    error_events = []

    # Register event handler
    @stt.on("error")
    def on_error(error):
        error_events.append(error)

    # Send some audio data to ensure the connection is active
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Trigger an error by manually inserting to the queue
    error = Exception("Test error message")
    stt._dispatcher.add_item(error)

    # Wait a small amount of time for the background dispatcher to process the event
    await asyncio.sleep(0.05)

    # Check that we received the error event
    assert len(error_events) == 1, "Expected 1 error event"
    assert str(error_events[0]) == "Test error message", "Incorrect error message"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.stt.deepgram.stt.DeepgramClient", MockDeepgramClient)
async def test_dispatcher_shutdown():
    """
    Test that the dispatcher is properly shutdown when the STT service is closed.
    """
    # Create the Deepgram STT instance
    stt = Deepgram(api_key="test-api-key")

    # Verify the dispatcher is running
    assert stt._dispatcher.running, "Dispatcher should be running after initialization"

    # Close the STT service
    await stt.close()

    # Verify the dispatcher has been stopped
    assert not stt._dispatcher.running, "Dispatcher should be stopped after close"
    assert stt._dispatcher.task is None, "Dispatcher task should be None after close"

    # Try to emit a transcript after closing (should not crash but no events should be received)
    transcript_events = []

    @stt.on("transcript")
    def on_transcript(text, metadata):
        transcript_events.append((text, metadata))

    # Attempt to emit a transcript
    try:
        stt.dg_connection.emit_transcript("this should not be received")
    except Exception:
        pass  # It's okay if this fails

    # Wait a small amount of time
    await asyncio.sleep(0.05)

    # No events should have been received
    assert len(transcript_events) == 0, "Should not receive events after close"
