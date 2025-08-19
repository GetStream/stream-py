import json
import pytest
import asyncio
from unittest.mock import patch, MagicMock

from getstream.plugins.deepgram.stt import DeepgramSTT
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

    async def start(self, options):
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

    def emit_error(self, error_message):
        """Helper to emit an error event"""
        from deepgram import LiveTranscriptionEvents

        if LiveTranscriptionEvents.Error in self.event_handlers:
            # Call the error handler
            self.event_handlers[LiveTranscriptionEvents.Error](
                self, error=error_message
            )


class MockDeepgramClient:
    def __init__(self, config=None):
        # Handle both string API key and DeepgramClientOptions object
        if hasattr(config, 'api_key'):
            self.api_key = config.api_key
        else:
            self.api_key = config
        
        # Create a mock connection instance
        self.mock_connection = MockDeepgramConnection()
        
        # Set up the mock chain properly (for backward compatibility)
        self.listen = MagicMock()
        self.listen.websocket = MagicMock()
        # Make sure v("1") returns our mock connection
        self.listen.websocket.v = MagicMock(return_value=self.mock_connection)
        
        # NEW API: The client itself IS the connection, so add connection methods
        self.event_handlers = {}
        self.sent_data = []
        self.finished = False

    def on(self, event, handler):
        """Register event handlers - NEW API"""
        self.event_handlers[event] = handler
        return handler

    async def send(self, data):
        """Mock send data - NEW API"""
        self.sent_data.append(data)
        return True

    def send_binary(self, data):
        """Mock send binary data - NEW API"""
        self.sent_data.append(data)
        return True

    async def finish(self):
        """Close the connection - NEW API"""
        self.finished = True

    async def start(self, options):
        """Start the connection - NEW API"""
        pass

    def emit_transcript(self, text, is_final=True):
        """Helper to emit a transcript event"""
        from deepgram import LiveTranscriptionEvents
        import json
        
        # Create a mock result object
        transcript_json = {
            "channel": {
                "alternatives": [
                    {
                        "transcript": text,
                        "confidence": 0.99,
                        "words": []
                    }
                ]
            },
            "is_final": is_final,
            "speech_final": is_final
        }
        
        # Convert to JSON string to match real API behavior
        result_json = json.dumps(transcript_json)
        
        # Call the handler if it exists
        if LiveTranscriptionEvents.Transcript in self.event_handlers:
            handler = self.event_handlers[LiveTranscriptionEvents.Transcript]
            # Since the handler is async, we need to handle it properly
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                # For testing, we'll just call it synchronously
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(handler(self, result=result_json))
                except:
                    # If no loop, just skip for testing
                    pass
            else:
                handler(self, result=result_json)

    def emit_error(self, error):
        """Helper to emit an error event"""
        from deepgram import LiveTranscriptionEvents
        
        # Call the error handler if it exists
        if LiveTranscriptionEvents.Error in self.event_handlers:
            handler = self.event_handlers[LiveTranscriptionEvents.Error]
            # Since the handler is async, we need to handle it properly
            import asyncio
            if asyncio.iscoroutinefunction(handler):
                # For testing, we'll just call it synchronously
                try:
                    loop = asyncio.get_event_loop()
                    loop.create_task(handler(self, error=error))
                except:
                    # If no loop, just skip for testing
                    pass
            else:
                handler(self, error=error)


@pytest.mark.asyncio
@patch("getstream.plugins.deepgram.stt.stt.AsyncLiveClient", MockDeepgramClient)
async def test_real_time_transcript_emission():
    """Test that transcript events are emitted in real-time."""
    stt = DeepgramSTT(api_key="test-api-key")

    # Collection for events
    transcript_events = []

    # Register event handler
    @stt.on("transcript")
    def on_transcript(text, user, metadata):
        transcript_events.append((text, user, metadata))

    # Send some audio data
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Trigger a transcript
    stt.dg_connection.emit_transcript("test message", is_final=True)

    # Event should be emitted immediately
    await asyncio.sleep(0.01)
    assert len(transcript_events) == 1, "Event should be emitted immediately"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.deepgram.stt.stt.AsyncLiveClient", MockDeepgramClient)
async def test_real_time_partial_transcript_emission():
    """Test that partial transcript events are emitted in real-time."""
    stt = DeepgramSTT(api_key="test-api-key", interim_results=True)

    # Collection for events
    partial_transcript_events = []

    # Register event handler
    @stt.on("partial_transcript")
    def on_partial_transcript(text, user, metadata):
        partial_transcript_events.append((text, user, metadata))

    # Send some audio data
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Trigger a partial transcript
    stt.dg_connection.emit_transcript("test", is_final=False)

    # Event should be emitted immediately
    await asyncio.sleep(0.01)
    assert len(partial_transcript_events) == 1, "Partial event should be emitted immediately"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.deepgram.stt.stt.AsyncLiveClient", MockDeepgramClient)
async def test_real_time_error_emission():
    """Test that error events are emitted in real-time."""
    stt = DeepgramSTT(api_key="test-api-key")

    # Collection for events
    error_events = []

    # Register event handler
    @stt.on("error")
    def on_error(error):
        error_events.append(error)

    # Send some audio data
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Trigger an error
    stt.dg_connection.emit_error("test error")

    # Event should be emitted immediately
    await asyncio.sleep(0.01)
    assert len(error_events) == 1, "Error event should be emitted immediately"

    # Cleanup
    await stt.close()


@pytest.mark.asyncio
@patch("getstream.plugins.deepgram.stt.stt.AsyncLiveClient", MockDeepgramClient)
async def test_close_cleanup():
    """Test that closing the STT service properly cleans up resources."""
    stt = DeepgramSTT(api_key="test-api-key")

    # Collection for events
    transcript_events = []

    # Register event handler
    @stt.on("transcript")
    def on_transcript(text, user, metadata):
        transcript_events.append((text, user, metadata))

    # Send some audio data
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Close the service
    await stt.close()

    # Try to send more audio - should be ignored
    await stt.process_audio(pcm_data)

    # No new events should be emitted
    assert len(transcript_events) == 0, "Should not receive events after close"


@pytest.mark.asyncio
@patch("getstream.plugins.deepgram.stt.stt.AsyncLiveClient", MockDeepgramClient)
async def test_asynchronous_mode_behavior():
    """
    Test that Deepgram operates in asynchronous mode:
    1. Events are emitted immediately when they arrive
    2. _process_audio_impl always returns None (no result collection)
    """
    # Create the Deepgram STT instance
    stt = DeepgramSTT(api_key="test-api-key")

    # Collection for events
    transcript_events = []

    # Register event handler
    @stt.on("transcript")
    def on_transcript(text, user, metadata):
        transcript_events.append((text, user, metadata))

    # Send some audio data
    pcm_data = PcmData(samples=b"\x00\x00" * 800, sample_rate=48000, format="s16")
    await stt.process_audio(pcm_data)

    # Trigger a transcript
    stt.dg_connection.emit_transcript("test message", is_final=True)

    # Event should be emitted immediately
    await asyncio.sleep(0.01)
    assert len(transcript_events) == 1, "Event should be emitted immediately"

    # _process_audio_impl should always return None in asynchronous mode
    results = await stt._process_audio_impl(pcm_data, {"user_id": "test"})

    # Should always return None for asynchronous mode
    assert results is None, "Asynchronous mode should always return None"

    # Cleanup
    await stt.close()
