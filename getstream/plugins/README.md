# GetStream Plugins

This package contains various plugins for the GetStream SDK, organized by functionality:

## Directory Structure

```
getstream/plugins/
├── stt/                # Speech-to-Text functionality
│   ├── deepgram/       # Deepgram STT implementation
│   └── ...             # Other STT implementations
├── tts/                # Text-to-Speech functionality
│   ├── elevenlabs/     # ElevenLabs TTS implementation
│   └── ...             # Other TTS implementations
└── vad/                # Voice Activity Detection
    ├── silero/         # Silero VAD implementation
    └── ...             # Other VAD implementations
```

## Available Plugins

### Speech-to-Text (STT)

- **Deepgram**: High-quality speech-to-text using the Deepgram API
  ```python
  from getstream.plugins.stt.deepgram import Deepgram

  stt = Deepgram(api_key="your_deepgram_api_key")
  ```

### Text-to-Speech (TTS)

- **ElevenLabs**: High-quality text-to-speech using the ElevenLabs API
  ```python
  from getstream.plugins.tts.elevenlabs import ElevenLabs

  tts = ElevenLabs(api_key="your_elevenlabs_api_key")
  ```

### Voice Activity Detection (VAD)

- **Silero**: Fast and accurate voice activity detection
  ```python
  from getstream.plugins.vad.silero import Silero

  vad = Silero()
  ```

## Using Plugins

All plugins follow a consistent API within their category. You can access the base classes directly:

```python
from getstream.plugins import STT, TTS, VAD
```

For more detailed usage instructions, see the documentation for each specific plugin.
