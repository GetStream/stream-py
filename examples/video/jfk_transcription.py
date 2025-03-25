#!/usr/bin/env python3
import asyncio
import os
import json
import uuid
import dotenv
import threading
import queue
import websocket
from pathlib import Path

from getstream import Stream
from getstream.video.rtc.audio import audio_event_to_openai_pcm
from getstream.video.rtc.rtc import (
    MockConfig,
    MockParticipant,
    MockAudioConfig,
    on_event,
)

import logging

logging.basicConfig(level=logging.WARNING)

# Load environment variables from root .env file
dotenv.load_dotenv(Path(__file__).parent.parent.parent / ".env")


class OpenAIException(Exception):
    pass


class OpenAITranscriptionClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.ws = None
        self.message_queue = queue.Queue()
        self.ws_thread = None
        self.loop = asyncio.get_event_loop()
        self.running = False
        self.connected_event = asyncio.Event()

    def on_open(self, ws):
        """Called when WebSocket connection is established."""
        print("WebSocket connection opened")

        # Initialize the session
        session_update = {
            "type": "transcription_session.update",
            "session": {
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "gpt-4o-transcribe",
                    "prompt": "",
                    "language": "en",
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 500,
                },
                "input_audio_noise_reduction": {"type": "near_field"},
                "include": [
                    "item.input_audio_transcription.logprobs",
                ],
            },
        }

        ws.send(json.dumps(session_update))

    def on_message(self, ws, message):
        """Called when a message is received from the server."""

        try:
            data = json.loads(message)
            event_type = data.get("type", "unknown")

            if event_type == "transcription_session.updated":
                print("transcription_session.updated")
                # Set the connected event in the asyncio loop
                asyncio.run_coroutine_threadsafe(self._set_connected(), self.loop)
            elif event_type == "conversation.item.input_audio_transcription.delta":
                print(f"PARTIAL: {data['delta']}")
            elif event_type == "transcription.segment.done":
                print(f"\nFINAL: {data['transcript']}")
            elif event_type == "error":
                if not self.connected_event.is_set():
                    raise OpenAIException(message)
                print(f"ERROR: {data.get('error', 'Unknown error')}")
            else:
                # Other events
                print(f"OAI EVENT: {message}")
        except json.JSONDecodeError:
            print(f"Received non-JSON message: {message}")

    def on_error(self, ws, error):
        """Called when a WebSocket error occurs."""
        print(f"WebSocket error: {error}")
        asyncio.run_coroutine_threadsafe(self._set_error(str(error)), self.loop)

    def on_close(self, ws, close_status_code, close_msg):
        """Called when the WebSocket connection is closed."""
        print(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.running = False

    async def _set_connected(self):
        """Set the connected event from a coroutine context."""
        self.connected_event.set()

    async def _set_error(self, error_msg):
        """Signal an error condition."""
        self.running = False
        if not self.connected_event.is_set():
            self.connected_event.set()  # Unblock any waiters
        print(f"Connection failed: {error_msg}")

    def _websocket_thread(self):
        """Thread function to run the WebSocket connection."""
        url = "wss://api.openai.com/v1/realtime?intent=transcription"
        headers = ["Authorization: Bearer " + self.api_key, "OpenAI-Beta: realtime=v1"]

        print(f"Connecting to {url}")
        self.ws = websocket.WebSocketApp(
            url,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )

        # Run the WebSocket connection with ping/pong for keepalive
        self.ws.run_forever()

    def _message_thread(self):
        """Thread function to process the message queue."""
        try:
            # Get a message with timeout
            message = self.message_queue.get(timeout=0.2)

            # Send the message if connected
            if self.ws and self.ws.sock and self.ws.sock.connected:
                self.ws.send(message)
            else:
                print("WebSocket not connected, discarding message")

            self.message_queue.task_done()
        except queue.Empty:
            # No messages in the queue
            pass
        except Exception as e:
            print(f"Error sending message: {e}")

    async def connect(self):
        """Connect to OpenAI's WebSocket API asynchronously."""
        print("Connecting to OpenAI Realtime API...")

        # Reset state
        self.running = True
        self.connected_event.clear()

        # Start the WebSocket thread
        self.ws_thread = threading.Thread(target=self._websocket_thread)
        self.ws_thread.daemon = True
        self.ws_thread.start()

        # Start the message processing thread
        self.message_thread = threading.Thread(target=self._message_thread)
        self.message_thread.daemon = True
        self.message_thread.start()

        await asyncio.wait_for(self.connected_event.wait(), timeout=10.0)

    async def send_audio_event(self, event):
        """Converts an audio event from Stream and sends its data to OpenAI."""
        audio_data = audio_event_to_openai_pcm(event)
        if audio_data:
            audio_message = json.dumps(
                {"type": "input_audio_buffer.append", "audio": audio_data}
            )
            self.message_queue.put(audio_message)


async def main():
    # Initialize Stream client
    stream_client = Stream(
        api_key=os.environ.get("STREAM_API_KEY"),
        api_secret=os.environ.get("STREAM_API_SECRET"),
    )

    # Create a call object with a unique ID
    call_id = str(uuid.uuid4())
    rtc_call = stream_client.video.rtc_call("default", call_id)

    # Set up the JFK audio file path (adjust as needed for your system)
    audio_file = "/Users/tommaso/src/data-samples/audio/samples_jfk.wav"

    # Check if the file exists, otherwise look for alternatives
    if not os.path.exists(audio_file):
        # Try to find audio files in the tests/assets directory
        test_assets_dir = Path(__file__).parent.parent.parent / "tests" / "assets"

        # First check for WAV files
        wav_files = list(test_assets_dir.glob("*.wav"))
        if wav_files:
            audio_file = str(wav_files[0])
        # If no WAV files, use MP3 files as a fallback
        else:
            mp3_files = list(test_assets_dir.glob("*.mp3"))
            if mp3_files:
                audio_file = str(mp3_files[0])
            else:
                raise FileNotFoundError(
                    "No suitable audio files found in tests/assets directory"
                )

    print(f"Using audio file: {audio_file}")

    # Create a mock participant with the selected audio file
    mock_audio = MockAudioConfig(
        audio_file_path=audio_file,
        realtime_clock=True,  # Use real-time clock for realistic timing
    )

    # Determine participant name based on file name
    audio_name = Path(audio_file).stem
    participant_id = f"{audio_name}-speaker"

    mock_participant = MockParticipant(
        user_id=participant_id,
        name=f"{audio_name.title()} Speaker",
        audio=mock_audio,
    )

    # Set up the mock configuration
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Create OpenAI client
    openai_client = OpenAITranscriptionClient(os.environ.get("OPENAI_API_KEY"))

    await openai_client.connect()

    async with rtc_call.join("transcription-client", timeout=60.0) as connection:

        async def on_audio_packet(event):
            await openai_client.send_audio_event(event)

        await on_event(connection, "audio_packet", on_audio_packet)

        print("Processing audio events (press Ctrl+C to stop)...")

        # TODO: this needs to be replaced
        async for _ in connection:
            pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt")
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback

        traceback.print_exc()
