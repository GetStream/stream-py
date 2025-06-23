# ElevenLabs Text-to-Speech Plugin

A high-quality Text-to-Speech (TTS) plugin for GetStream that uses the ElevenLabs API.

## Installation

```bash
pip install getstream-plugins-tts-elevenlabs
```

## Usage

```python
from getstream.plugins.tts.elevenlabs import ElevenLabs
from getstream.video.rtc.audio_track import AudioStreamTrack

# Initialize with API key from environment variable
tts = ElevenLabs()

# Or specify API key directly
tts = ElevenLabs(api_key="your_elevenlabs_api_key")

# Create an audio track to output speech
track = AudioStreamTrack(framerate=16000)
tts.set_output_track(track)

# Register event handlers
@tts.on("audio")
def on_audio(audio_data, user):
    print(f"Received audio chunk: {len(audio_data)} bytes")

# Send text to be converted to speech
await tts.send("Hello, this is a test of the ElevenLabs text-to-speech plugin.")
```

## Configuration Options

- `api_key`: ElevenLabs API key (default: reads from ELEVENLABS_API_KEY environment variable)
- `voice_id`: The voice ID to use for synthesis (default: "21m00Tcm4TlvDq8ikWAM")
- `model_id`: The model ID to use for synthesis (default: "eleven_multilingual_v2")

## Requirements

- Python 3.8+
- elevenlabs

## Testing

```bash
pytest -xvs getstream/plugins/tts/elevenlabs/tests/
```
