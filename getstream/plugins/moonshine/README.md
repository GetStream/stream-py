# Moonshine STT Plugin

This plugin provides Speech-to-Text functionality using [Moonshine](https://github.com/usefulsensors/moonshine), a family of speech-to-text models optimized for fast and accurate automatic speech recognition (ASR) on resource-constrained devices.

## Features

- **Fast and Accurate**: Moonshine processes 10-second audio segments 5x faster than Whisper while maintaining the same (or better!) WER
- **Resource Efficient**: Optimized for edge devices and resource-constrained environments
- **Variable Length Processing**: Compute requirements scale with input audio length (unlike Whisper's fixed 30-second chunks)
- **Multiple Models**: Support for both `moonshine/tiny` (~190MB) and `moonshine/base` (~400MB) models
- **Device Flexibility**: ONNX runtime automatically selects optimal execution provider
- **Smart Sample Rate Handling**: Automatic detection and high-quality resampling of WebRTC audio (48kHz → 16kHz)
- **WebRTC Optimized**: Seamless integration with Stream video calling infrastructure
- **Efficient Model Loading**: ONNX version loads models on-demand for optimal memory usage

## Installation (uv)

If your project already uses **uv**, add the plugin to your `pyproject.toml`
and let uv resolve everything:

```toml
[project]
dependencies = [
    # … other deps …
    "getstream-plugins-moonshine",
]

[tool.uv.sources]
getstream-plugins-moonshine = { path = "getstream/plugins/moonshine" }  # or remove for PyPI
```

Then:

```bash
uv sync        # installs useful-moonshine-onnx, onnxruntime, etc.
```

### Classic pip (optional)

If you prefer to install only the runtime libraries manually:

```bash
pip install "useful-moonshine-onnx @ git+https://github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx"
pip install onnxruntime
```

## Usage

```python
from getstream.plugins.moonshine import MoonshineSTT
from getstream.video.rtc.track_util import PcmData

# Initialize with default settings (base model, 16kHz)
stt = MoonshineSTT()

# Or customize the configuration
stt = MoonshineSTT(
    model_name="moonshine/tiny",  # Use the smaller, faster model
    sample_rate=16000,            # Moonshine's native sample rate
    min_audio_length_ms=500,      # Minimum audio length for transcription
    # ONNX runtime will automatically select the best execution provider
)

# Set up event handlers
@stt.on("transcript")
async def on_transcript(text: str, user: any, metadata: dict):
    print(f"Final transcript: {text}")
    print(f"Confidence: {metadata.get('confidence', 'N/A')}")
    print(f"Processing time: {metadata.get('processing_time_ms', 'N/A')}ms")

@stt.on("error")
async def on_error(error: Exception):
    print(f"STT Error: {error}")

# Process audio data
pcm_data = PcmData(samples=audio_bytes, sample_rate=16000, format="s16")
await stt.process_audio(pcm_data)

# Clean up
await stt.close()
```

## Model Selection

Moonshine offers two model variants with different trade-offs:

| Model | Size | Parameters | Speed | Accuracy | Use Case |
|-------|------|------------|-------|----------|----------|
| `moonshine/tiny` | ~190MB | 27M | Faster | Good | Resource-constrained devices, real-time applications |
| `moonshine/base` | ~400MB | 61M | Fast | Better | **Default choice** - balanced performance and accuracy |

**Default Model**: The plugin uses `moonshine/base` by default as it provides the best balance of accuracy and performance for most use cases.

**Choosing a Model**:
- Use `moonshine/tiny` for maximum speed on very resource-constrained devices
- Use `moonshine/base` for better accuracy with still excellent performance (recommended)

**Model Name Validation**:
- Strict validation prevents silent fallbacks to wrong models
- Supports both short names (`"tiny"`, `"base"`) and full names (`"moonshine/tiny"`, `"moonshine/base"`)
- Clear error messages list all valid options when invalid model is specified
- Canonical model names ensure consistent behavior across different input formats

## Sample Rate Handling

The Moonshine plugin automatically handles sample rate conversion for optimal transcription quality:

## Events

The plugin emits the following events:

- **transcript**: Final transcription result
  - `text` (str): The transcribed text
  - `user` (any): User metadata passed to `process_audio()`
  - `metadata` (dict): Additional information including model name, duration, etc.

- **error**: Error during transcription
  - `error` (Exception): The error that occurred

Note: Unlike streaming STT services, Moonshine doesn't emit `partial_transcript` events as it processes complete audio chunks.
