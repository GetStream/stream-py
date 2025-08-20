# AssemblyAI Speech-to-Text Plugin

A high-quality Speech-to-Text (STT) plugin for GetStream that uses the AssemblyAI API.

## Installation

```bash
pip install getstream-plugins-assemblyai
```

## Usage

```python
from getstream.plugins.assemblyai import AssemblyAISTT

# Initialize with API key from environment variable
stt = AssemblyAISTT()

# Or specify API key directly
stt = AssemblyAISTT(api_key="your_assemblyai_api_key")

# Register event handlers
@stt.on("transcript")
def on_transcript(text, user, metadata):
    print(f"Final transcript from {user}: {text}")

@stt.on("partial_transcript")
def on_partial(text, user, metadata):
    print(f"Partial transcript from {user}: {text}")

# Process audio
await stt.process_audio(pcm_data)

# When done
await stt.close()
```

## Configuration Options

- `api_key`: AssemblyAI API key (default: reads from ASSEMBLYAI_API_KEY environment variable)
- `sample_rate`: Sample rate of the audio in Hz (default: 48000)
- `language`: Language code for transcription (default: "en")
- `interim_results`: Whether to emit interim results (default: True)
- `enable_partials`: Whether to enable partial results (default: True)
- `enable_automatic_punctuation`: Whether to enable automatic punctuation (default: True)
- `enable_utterance_end_detection`: Whether to enable utterance end detection (default: True)

## Requirements

- Python 3.10+
- assemblyai>=0.43.1
- numpy>=2.2.6,<2.3

## Features

- Real-time streaming transcription
- Partial and final transcript results
- Automatic punctuation
- Utterance end detection
- Multi-language support
- High-quality transcription models

## Environment Variables

Set the following environment variable for API access:

```bash
export ASSEMBLYAI_API_KEY="your_api_key_here"
```

## API Reference

For more information about AssemblyAI's API, visit:
https://www.assemblyai.com/docs
