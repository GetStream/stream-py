# Stream + VAD + Deepgram STT + ElevenLabs TTS Example

This example demonstrates how to build a real-time audio conversation bot using Stream's Video SDK, Silero VAD (Voice Activity Detection), Deepgram's Speech-to-Text API, and ElevenLabs Text-to-Speech API.

## What it does

- 🤖 Creates an audio conversation bot that joins a Stream video call
- 🎤 Uses VAD to detect when users are speaking
- 🎙️ Transcribes speech in real-time using Deepgram STT
- 🔊 Echoes back the transcribed text using ElevenLabs TTS
- 📝 Displays transcriptions with timestamps in the terminal

## Prerequisites

1. **Stream Account**: Get your API credentials from [Stream Dashboard](https://dashboard.getstream.io)
2. **Deepgram Account**: Get your API key from [Deepgram Console](https://console.deepgram.com)
3. **ElevenLabs Account**: Get your API key from [ElevenLabs](https://elevenlabs.io)
4. **Python 3.9+**: Required for running the example

## Installation

1. **Navigate to the example directory:**
   ```bash
   cd examples/llm_audio_conversation
   ```

2. **Install dependencies:**

   Using pip:
   ```bash
   pip install -e .
   ```

   Or using uv (recommended):
   ```bash
   uv pip install -e .
   ```

   Note: This will install the getstream package, deepgram-sdk, elevenlabs, silero-vad, aiortc (for WebRTC), and other required dependencies.

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   ```

   Edit `.env` with your actual credentials:
   ```env
   STREAM_API_KEY=your_actual_stream_api_key
   STREAM_API_SECRET=your_actual_stream_api_secret
   STREAM_BASE_URL=https://chat.stream-io-api.com/
   DEEPGRAM_API_KEY=your_actual_deepgram_api_key
   ELEVENLABS_API_KEY=your_actual_elevenlabs_api_key
   ```

## Usage

1. **Run the example:**
   ```bash
   python main.py
   ```

2. **What happens:**
   - A unique call ID is generated
   - The audio conversation bot joins the call
   - The bot says a welcome message using TTS
   - When you speak, VAD detects your voice
   - Your speech is transcribed using Deepgram STT
   - The bot echoes back your words using ElevenLabs TTS

3. **Example output:**
   ```
   🎙️  Stream + VAD + Deepgram STT + ElevenLabs TTS Example
   ============================================================
   📞 Call ID: llm-audio-demo-a1b2c3d4
   🤖 Created token for bot user: llm-audio-bot
   📞 Call created: llm-audio-demo-a1b2c3d4

   🤖 Starting LLM audio conversation bot...
   The bot will join the call, detect speech, transcribe it, and echo it back.

   Press Ctrl+C to stop the bot.

   ✅ Bot joined call: llm-audio-demo-a1b2c3d4
   🎧 Listening for audio... (Press Ctrl+C to stop)
   1704123135.123 Speech detected from user: user-123 duration 2.5
   1704123137.456 got text from audio, will echo back the transcript: Hello, how are you today?
   1704123140.789 Speech detected from user: user-123 duration 1.8
   1704123142.012 got text from audio, will echo back the transcript: This is working great!
   ```

## How it works

### Audio Processing Pipeline
1. **Voice Activity Detection (VAD)**: Silero VAD detects when speech starts and ends
2. **Speech-to-Text (STT)**: Detected speech is sent to Deepgram for transcription
3. **Text-to-Speech (TTS)**: Transcribed text is converted back to speech using ElevenLabs
4. **Audio Output**: The synthesized speech is played back through the call

### Code Structure
```python
# Initialize components
vad = Silero()
stt = Deepgram()
tts_instance = ElevenLabs(voice_id="zOImbcIGBTxd0yXmwgRi")

# Set up the processing pipeline
@connection.on("audio")
async def on_audio(pcm: PcmData, user):
    await vad.process_audio(pcm, user)

@vad.on("audio")
async def on_speech_detected(pcm: PcmData, user):
    await stt.process_audio(pcm, user)

@stt.on("transcript")
async def on_transcript(text: str, user, metadata):
    await tts_instance.send(text)
```

## Troubleshooting

### No speech detection
- Check that your microphone is working
- Verify that audio is being received by the bot
- Adjust VAD sensitivity if needed

### No transcriptions appearing
- Verify your Deepgram API key is valid and has credits
- Check that speech is being detected by VAD first
- Ensure the bot successfully joined the call

### No TTS output
- Verify your ElevenLabs API key is valid and has credits
- Check that the voice ID exists in your ElevenLabs account
- Ensure transcriptions are being generated first

### Connection errors
- Verify your Stream API credentials are correct
- Check your internet connection
- Ensure the Stream base URL is correct

## API Keys Setup

### Stream API Keys
1. Go to [Stream Dashboard](https://dashboard.getstream.io)
2. Create a new app or use an existing one
3. Copy the API Key and Secret from the app settings

### Deepgram API Key
1. Go to [Deepgram Console](https://console.deepgram.com)
2. Create a new project or use an existing one
3. Generate an API key in the project settings
4. Copy the API key

### ElevenLabs API Key
1. Go to [ElevenLabs](https://elevenlabs.io)
2. Sign up for an account
3. Go to your profile settings
4. Generate an API key
5. Note: You can also customize the voice ID in the code

## Configuration Options

### Voice ID
You can change the ElevenLabs voice by modifying the `voice_id` parameter:
```python
tts_instance = ElevenLabs(voice_id="your_preferred_voice_id")
```

### Audio Settings
The audio track is configured for 16kHz sample rate:
```python
audio = audio_track.AudioStreamTrack(framerate=16000)
```

## Related Examples

- **STT Examples**: See `../stt_*` directories for speech-to-text examples
- **TTS Examples**: See `../tts_*` directories for text-to-speech examples
- **VAD Examples**: See VAD-specific examples for voice activity detection

## Development

### Running Tests
```bash
python -m pytest test_example.py -v
```

### Extending the Example
This example provides a foundation for building more complex audio conversation bots. You could extend it by:
- Adding an LLM to process and respond to transcriptions intelligently
- Implementing conversation memory and context
- Adding multiple voice options
- Implementing real-time language translation

## Support

- [Stream Documentation](https://getstream.io/video/docs/)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [Stream Community](https://github.com/GetStream/stream-video-python)
