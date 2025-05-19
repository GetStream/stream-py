# Deepgram Speech-to-Text Plugin

A high-quality Speech-to-Text (STT) plugin for GetStream that uses the Deepgram API.

## Installation

```bash
pip install getstream-plugins-stt-deepgram
```

## Usage

```python
from getstream.plugins.stt.deepgram import Deepgram

# Initialize with API key from environment variable
stt = Deepgram()

# Or specify API key directly
stt = Deepgram(api_key="your_deepgram_api_key")

# Register event handlers
@stt.on("transcript")
def on_transcript(text, metadata):
    print(f"Final transcript: {text}")

@stt.on("partial_transcript")
def on_partial(text, metadata):
    print(f"Partial transcript: {text}")

# Process audio
await stt.process_audio(pcm_data)

# When done
await stt.close()
```

## Configuration Options

- `api_key`: Deepgram API key (default: reads from DEEPGRAM_API_KEY environment variable)
- `options`: Deepgram LiveOptions for configuring the transcription
- `sample_rate`: Sample rate of the audio in Hz (default: 16000)
- `language`: Language code for transcription (default: "en-US")
- `keep_alive_interval`: Interval in seconds to send keep-alive messages (default: 5.0)

## Requirements

- Python 3.8+
- deepgram-sdk
- numpy

## Testing

```bash
pytest -xvs getstream/plugins/stt/deepgram/tests/
```
