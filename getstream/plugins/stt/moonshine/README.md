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

## Installation

The plugin requires the Moonshine ONNX library:

```bash
pip install useful-moonshine-onnx@git+https://github.com/usefulsensors/moonshine.git#subdirectory=moonshine-onnx
pip install onnxruntime
```

## Usage

```python
from getstream.plugins.stt.moonshine import Moonshine
from getstream.video.rtc.track_util import PcmData

# Initialize with default settings (base model, 16kHz)
stt = Moonshine()

# Or customize the configuration
stt = Moonshine(
    model_name="moonshine/tiny",  # Use the smaller, faster model
    sample_rate=16000,            # Moonshine's native sample rate
    chunk_duration_ms=1000,       # Process 1-second chunks
    min_audio_length_ms=500,      # Minimum audio length for transcription
    # ONNX runtime will automatically select the best execution provider
    target_dbfs=-26.0             # RMS normalization target (optimal for Moonshine)
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

- **Native Rate**: Moonshine models are optimized for 16kHz audio
- **WebRTC Compatibility**: Automatically detects and converts 48kHz WebRTC audio to 16kHz
- **High-Quality Resampling**: Uses scipy's resample_poly for superior audio quality
- **Automatic Detection**: Logs sample rate conversions for debugging and monitoring
- **Metadata Tracking**: Includes resampling information in transcription metadata

**Common Scenarios**:
- WebRTC calls (48kHz) → Automatically resampled to 16kHz
- Native 16kHz audio → No resampling needed (optimal performance)
- Other sample rates → Automatically resampled with quality preservation

**Audio Format Optimization**:
- Saves audio as 16-bit PCM WAV format (Moonshine's training format)
- Avoids float32 WAV files which reduce dynamic range and accuracy
- Maintains optimal signal-to-noise ratio for transcription quality

**RMS Normalization**:
- Automatically normalizes audio to optimal -26 dBFS level (Moonshine's training standard)
- Boosts quiet WebRTC audio (typically -35 dBFS) for better recognition accuracy
- Provides 1.5-3 dB SNR improvement without introducing clipping
- Configurable target level via `target_dbfs` parameter

## Configuration Options

- **model_name**: Choose between `"moonshine/tiny"` (faster, smaller) or `"moonshine/base"` (more accurate, larger, **default**)
- **sample_rate**: Audio sample rate in Hz (default: 16000, Moonshine's native rate)
- **chunk_duration_ms**: Duration of audio chunks to process (default: 1000ms)
- **min_audio_length_ms**: Minimum audio length required for transcription (default: 500ms)

- **language**: Language code (currently only "en-US" supported by Moonshine)
- **target_dbfs**: Target RMS level in dBFS for audio normalization (default: -26.0, Moonshine's optimal level)

## Performance Characteristics

- **Real-time Factor**: Typically 0.1-0.3x (processes audio 3-10x faster than real-time)
- **Latency**: ~100-300ms processing time for 1-second audio chunks
- **Memory Usage**: ~200MB for tiny model, ~400MB for base model
- **Accuracy**: Comparable to or better than Whisper tiny/base models

## Limitations

- Currently supports English only
- No streaming/partial transcripts (processes complete audio chunks)
- Requires temporary file creation for Moonshine API compatibility
- No confidence scores (Moonshine doesn't provide them)

## Events

The plugin emits the following events:

- **transcript**: Final transcription result
  - `text` (str): The transcribed text
  - `user` (any): User metadata passed to `process_audio()`
  - `metadata` (dict): Additional information including model name, duration, etc.

- **error**: Error during transcription
  - `error` (Exception): The error that occurred

Note: Unlike streaming STT services, Moonshine doesn't emit `partial_transcript` events as it processes complete audio chunks.
