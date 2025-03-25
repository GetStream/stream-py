# Stream Video SDK Python Examples

This directory contains examples demonstrating how to use the Stream Video SDK for Python.

## Examples

### Real-time Audio Transcription (`jfk_transcription.py`)

This example demonstrates how to:

1. Create a mock call with simulated participants
2. Stream audio from a speech file (WAV or MP3)
3. Process audio packets in real-time
4. Convert audio to the format OpenAI expects (16-bit PCM, 24kHz, mono)
5. Use direct WebSocket connection to OpenAI's Realtime API
6. Display transcription results as they arrive

#### Requirements

- Python 3.8+
- Stream SDK dependencies
- Additional packages:
  - `websocket-client` (for WebSocket connection to OpenAI)
  - `numpy` (for audio processing)
  - `python-dotenv`

You can install the required packages with:

```bash
uv pip install websocket-client numpy python-dotenv
```

#### Setup

1. Make sure you have an OpenAI API key and Stream credentials in your `.env` file at the root of the project:

```
STREAM_API_KEY=your_stream_api_key
STREAM_API_SECRET=your_stream_api_secret
OPENAI_API_KEY=your_openai_api_key
```

2. The example will try to use a JFK speech WAV file first. If it's not found, it will look for:
   - Any WAV files in the `tests/assets` directory
   - If no WAV files are found, it will use any MP3 files (like the included `test_speech.mp3`)

#### Running the Example

From the root of the project:

```bash
python examples/video/jfk_transcription.py
```

The example will:
1. Connect to the OpenAI Realtime API via WebSocket
2. Find and use an available audio file
3. Join a mock Stream call with a simulated audio participant
4. Stream audio packets from the speech file to OpenAI
5. Display both partial and final transcription results

#### Audio Processing

The example demonstrates how to handle real-world audio format differences:

1. Stream's audio is typically 16-bit PCM at 48kHz with 2 channels (stereo)
2. OpenAI expects 16-bit PCM at 24kHz with 1 channel (mono)

The code:
- Converts stereo to mono by averaging the channels
- Downsamples from 48kHz to 24kHz by keeping every other sample
- Ensures proper byte order (little-endian) for OpenAI
- Base64 encodes the audio for transmission

#### WebSocket Implementation

This example uses a direct WebSocket implementation rather than the OpenAI Python client:

- Connection via `websocket-client` library
- Non-blocking threaded message queue for sending audio
- Event-based handlers for WebSocket events (open, message, error, close)
- Proper cleanup of resources when the session ends

#### Adding Your Own Audio Files

You can add your own audio files to `tests/assets` to use them with this example:

- Supported formats: WAV and MP3
- The example will automatically use your files if they're found in the search path
- Recommended: Use clear speech audio for best transcription results

#### Features Demonstrated

- Creating and configuring a mock call
- Setting up mock participants with audio
- Processing audio packets from a Stream call
- Converting audio to the format expected by OpenAI
- Direct WebSocket integration with OpenAI's Realtime API
- Configuring server-side Voice Activity Detection (VAD)
- Handling both partial and final transcription results
