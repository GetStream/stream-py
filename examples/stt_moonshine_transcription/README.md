# Moonshine STT Transcription Example

This example demonstrates real-time call transcription using the Moonshine Speech-to-Text plugin with GetStream Video SDK.

## Features

- **Real-time Transcription**: Process audio from video calls using Moonshine STT
- **Voice Activity Detection**: Integrated Silero VAD to filter speech from silence
- **Efficient Processing**: Only transcribe actual speech, reducing computational overhead
- **Performance Monitoring**: Track transcription speed, accuracy, and resource usage
- **Model Selection**: Choose between `moonshine/tiny` (fast) and `moonshine/base` (accurate)
- **Configurable Processing**: Adjust VAD sensitivity and STT parameters

## Prerequisites

1. **GetStream Account**: Get your API key from [GetStream Dashboard](https://dashboard.getstream.io/)
2. **Moonshine Library**: Install the Moonshine STT library
3. **Python 3.9+**: Required for the GetStream SDK

## Installation

1. **Install Moonshine STT Library**:
   ```bash
   pip install useful-moonshine@git+https://github.com/usefulsensors/moonshine.git
   ```

2. **Install Example Dependencies**:
   ```bash
   # From the example directory
   uv sync
   ```

3. **Configure Environment**:
   ```bash
   cp env.example .env
   # Edit .env with your GetStream API key
   ```

## Configuration

Edit the `.env` file with your settings:

```env
# Required: Your GetStream API key
STREAM_API_KEY=your_stream_api_key_here

# Optional: Moonshine model selection (default: moonshine/base)
MOONSHINE_MODEL=moonshine/base  # or moonshine/tiny

# Demo Configuration
DEMO_DURATION_SECONDS=60        # Demo runtime (seconds)
```

### Model Comparison

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `moonshine/tiny` | ~190MB | 5-10x real-time | Good | Real-time applications, resource-constrained |
| `moonshine/base` | ~400MB | 3-5x real-time | Better | **Default** - Higher accuracy requirements |

## Usage

### Basic Demo

Run the transcription demo:

```bash
python main.py
```

This will:
1. Initialize Moonshine STT with your chosen model
2. Set up Voice Activity Detection (if enabled)
3. Display configuration and wait for audio input
4. Show periodic statistics during runtime

### Integration with Video Calls

To integrate with actual video calls, modify the `run_transcription_demo` method:

```python
# Example integration (pseudo-code)
async def process_call_audio(call_id: str):
    # Initialize components
    stt = Moonshine()
    vad = Silero(sample_rate=16000, speech_pad_ms=300, min_speech_ms=250)

    # Set up VAD -> STT pipeline
    @vad.on("audio")
    async def on_speech_detected(pcm_data, user):
        await stt.process_audio(pcm_data, user)

    # Join the call
    call = client.video.call("default", call_id)
    async with await rtc.join(call, "bot-user") as connection:
        @connection.on("audio")
        async def on_audio(pcm_data, user):
            # Process all audio through VAD first
            await vad.process_audio(pcm_data, user)
```

## Performance Characteristics

### Expected Performance (on modern hardware)

- **Real-time Factor**: 0.1-0.3x (processes 3-10x faster than real-time)
- **Latency**: 100-300ms for 1-second audio chunks
- **Memory Usage**: 200-400MB depending on model
- **CPU Usage**: 10-30% on modern CPUs

### Optimization Tips

1. **Model Selection**:
   - Use `moonshine/base` for best balance of accuracy and performance (**default**)
   - Use `moonshine/tiny` for maximum speed on resource-constrained devices

2. **Chunk Duration**:
   - Smaller chunks (500-1000ms): Lower latency, more processing overhead
   - Larger chunks (1000-2000ms): Higher latency, better efficiency

3. **VAD Integration**:
   - Silero VAD automatically filters out silence
   - Only processes actual speech, reducing computational overhead
   - Configured with optimal settings: 300ms padding, 250ms minimum speech, 0.3/0.2 activation/deactivation thresholds

## Troubleshooting

### Common Issues

1. **Moonshine Import Error**:
   ```
   ImportError: No module named 'moonshine'
   ```
   **Solution**: Install Moonshine library:
   ```bash
   pip install useful-moonshine@git+https://github.com/usefulsensors/moonshine.git
   ```

2. **CUDA/GPU Issues**:
   ```
   RuntimeError: CUDA out of memory
   ```
   **Solution**: Force CPU usage:
   ```python
   stt = Moonshine(device="cpu")
   ```

3. **No Transcriptions**:
   - Check audio input levels
   - Verify VAD settings (try disabling VAD)
   - Ensure minimum audio length requirements are met

4. **Poor Performance**:
   - Try the `moonshine/tiny` model
   - Increase chunk duration
   - Check system resources (CPU/memory)

### Debug Mode

Enable debug logging for detailed information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Example Output

```
🌙 Stream + Moonshine Real-time Transcription Example
===================================================
📞 Call ID: 12345678-1234-1234-1234-123456789abc
🔑 Created token for browser user: browser-user
🤖 Created token for bot user: transcription-bot
📞 Call created: 12345678-1234-1234-1234-123456789abc
Opening browser to: https://pronto.getstream.io/bare/join/...

🤖 Starting transcription bot...
The bot will join the call and transcribe speech using VAD + Moonshine STT.
VAD will filter out silence and only process actual speech.
Join the call in your browser and speak to see transcriptions appear here!

🌙 Initializing Moonshine STT...
🔊 Initializing Silero VAD...
✅ Audio processing pipeline ready: VAD → Moonshine STT
✅ Bot joined call: 12345678-1234-1234-1234-123456789abc
🎧 Listening for audio... (Press Ctrl+C to stop)

🎤 Speech detected from user: browser-user, duration: 2.34s
[14:30:25] browser-user: Hello, this is a test of the Moonshine transcription system.
    └─ model: moonshine/base, device: cpu, RTF: 0.10x

🧹 Cleanup completed
```

## Next Steps

1. **Integrate with Real Calls**: Modify the example to process actual call audio
2. **Add Persistence**: Store transcriptions in a database
3. **Implement Webhooks**: Send transcriptions to external services
4. **Add Language Support**: Extend for multiple languages (when supported by Moonshine)
5. **Custom Models**: Train custom Moonshine models for specific domains

## Resources

- [Moonshine GitHub Repository](https://github.com/usefulsensors/moonshine)
- [GetStream Video SDK Documentation](https://getstream.io/video/docs/)
- [GetStream Python SDK](https://github.com/GetStream/stream-python)
- [Voice Activity Detection with Silero](https://github.com/snakers4/silero-vad)
