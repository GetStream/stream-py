# Stream + VAD + Deepgram STT + OpenAI LLM + ElevenLabs TTS Example

This example demonstrates how to build a real-time AI conversation bot using Stream's Video SDK, Silero VAD (Voice Activity Detection), Deepgram's Speech-to-Text API, OpenAI's GPT models, and ElevenLabs Text-to-Speech API.

## What it does

- 🤖 Creates an AI conversation bot that joins a Stream video call
- 🌐 Opens a browser interface for users to join the call
- 🎤 Uses VAD to detect when users are speaking
- 🎙️ Transcribes speech in real-time using Deepgram STT
- 🧠 Processes transcriptions through OpenAI's GPT model for intelligent responses
- 🔊 Converts AI responses to speech using ElevenLabs TTS
- 📝 Displays conversation flow with timestamps in the terminal

## Prerequisites

1. **Stream Account**: Get your API credentials from [Stream Dashboard](https://dashboard.getstream.io)
2. **Deepgram Account**: Get your API key from [Deepgram Console](https://console.deepgram.com)
3. **ElevenLabs Account**: Get your API key from [ElevenLabs](https://elevenlabs.io)
4. **OpenAI Account**: Get your API key from [OpenAI Platform](https://platform.openai.com)
5. **Python 3.9+**: Required for running the example

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

   Note: This will install the getstream package, deepgram-sdk, elevenlabs, openai, silero-vad, aiortc (for WebRTC), and other required dependencies.

3. **Set up environment variables:**

   The environment file is shared across all examples and located in the parent directory:
   ```bash
   cd ../  # Go to examples directory
   cp env.example .env
   ```

   Edit `examples/.env` with your actual credentials:
   ```env
   STREAM_API_KEY=your_actual_stream_api_key
   STREAM_API_SECRET=your_actual_stream_api_secret
   STREAM_BASE_URL=the_stream_base_url
   DEEPGRAM_API_KEY=your_actual_deepgram_api_key
   ELEVENLABS_API_KEY=your_actual_elevenlabs_api_key
   OPENAI_API_KEY=your_actual_openai_api_key
   ```

   Then return to the example directory:
   ```bash
   cd llm_audio_conversation
   ```

## Usage

1. **Run the example:**
   ```bash
   python main.py
   ```

2. **What happens:**
   - Unique user IDs and call ID are generated
   - A browser automatically opens with the Stream call interface
   - The AI conversation bot joins the call
   - The bot says a welcome message using TTS
   - When you speak in the browser, VAD detects your voice
   - Your speech is transcribed using Deepgram STT
   - The transcript is sent to OpenAI GPT for an intelligent response
   - The AI response is converted to speech using ElevenLabs TTS
   - You hear the AI's response through the call

3. **Example output:**
   ```
   🎙️  Stream + VAD + Deepgram STT + ElevenLabs TTS Example
   ============================================================
   👤 Created user: user-a1b2c3d4
   🔑 Created token for user: user-a1b2c3d4
   🤖 Created bot user: llm-audio-bot-e5f6g7h8
   📞 Call ID: i9j0k1l2-m3n4-o5p6-q7r8-s9t0u1v2w3x4
   📞 Call created: i9j0k1l2-m3n4-o5p6-q7r8-s9t0u1v2w3x4
   Opening browser to: https://pronto.getstream.io/bare/join/...
   Browser opened successfully!

   🤖 Starting LLM audio conversation bot...
   The bot will join the call, detect speech, transcribe it, and respond intelligently.

   Press Ctrl+C to stop the bot.

   ✅ Bot joined call: i9j0k1l2-m3n4-o5p6-q7r8-s9t0u1v2w3x4
   🎧 Listening for audio... (Press Ctrl+C to stop)
   1704123135.123 Speech detected from user: user-a1b2c3d4 duration 2.5
   1704123137.456 got text from user user-a1b2c3d4, will send to LLM: Hello, how are you today?
   1704123139.789 LLM response: Hello! I'm doing great, thank you for asking. How are you doing today? Is there anything I can help you with?
   1704123140.012 Speech detected from user: user-a1b2c3d4 duration 3.2
   1704123142.345 got text from user user-a1b2c3d4, will send to LLM: Can you tell me about artificial intelligence?
   1704123145.678 LLM response: Artificial intelligence is a fascinating field that involves creating computer systems capable of performing tasks that typically require human intelligence...
   ```

## How it works

### AI Conversation Pipeline
1. **Voice Activity Detection (VAD)**: Silero VAD detects when speech starts and ends
2. **Speech-to-Text (STT)**: Detected speech is sent to Deepgram for transcription
3. **LLM Processing**: Transcribed text is sent to OpenAI GPT for intelligent response generation
4. **Text-to-Speech (TTS)**: AI responses are converted to speech using ElevenLabs
5. **Audio Output**: The synthesized speech is played back through the call

### Browser Integration
- Automatically opens a browser window with the Stream call interface
- Users can join the call and have natural conversations with the AI
- Real-time audio communication between browser and AI bot

### Code Structure
```python
# Initialize all components
vad = Silero()
stt = Deepgram()
tts_instance = ElevenLabs(voice_id="zOImbcIGBTxd0yXmwgRi")
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set up the AI conversation pipeline
@connection.on("audio")
async def on_audio(pcm: PcmData, user):
    await vad.process_audio(pcm, user)

@vad.on("audio")
async def on_speech_detected(pcm: PcmData, user):
    await stt.process_audio(pcm, user)

@stt.on("transcript")
async def on_transcript(text: str, user: Any, metadata: dict[str, Any]):
    # Send to OpenAI for intelligent response
    response = openai_client.responses.create(
        model="gpt-4o",
        input=f"You are a helpful assistant. Respond to: {text}"
    )

    # Convert AI response to speech
    await tts_instance.send(response.output_text)
```

## Troubleshooting

### No speech detection
- Check that your microphone is working in the browser
- Verify that audio is being received by the bot
- Ensure you've allowed microphone permissions in the browser

### No transcriptions appearing
- Verify your Deepgram API key is valid and has credits
- Check that speech is being detected by VAD first
- Ensure the bot successfully joined the call

### No AI responses
- Verify your OpenAI API key is valid and has credits
- Check that transcriptions are being generated first
- Monitor the console for any OpenAI API errors

### No TTS output
- Verify your ElevenLabs API key is valid and has credits
- Check that the voice ID exists in your ElevenLabs account
- Ensure AI responses are being generated first

### Browser doesn't open
- Check that the URL is correct in the console output
- Manually copy and paste the URL into your browser
- Ensure your firewall allows the browser to open URLs

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

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up for an account
3. Navigate to API keys section
4. Create a new API key
5. Copy the API key

## Configuration Options

### Voice ID
You can change the ElevenLabs voice by modifying the `voice_id` parameter:
```python
tts_instance = ElevenLabs(voice_id="your_preferred_voice_id")
```

**Default ElevenLabs voices available to all users:**
- **Rachel** (`21m00Tcm4TlvDq8ikWAM`) - Calm, young female voice (currently used)
- **Adam** (`pNInz6obpgDQGcFmaJgB`) - Deep, male voice with American accent
- **Antoni** (`ErXwobaYiN019PkySvjV`) - Well-rounded, young male voice
- **Arnold** (`VR6AewLTigWG4xSOukaG`) - Crisp, middle-aged male voice
- **Domi** (`AZnzlk1XvdvUeBnXmlld`) - Strong, young female voice
- **Josh** (`TxGEqnHWrfWFTfGW9XjX`) - Deep, young male voice
- **Sam** (`yoZ06aMxZJJ28mfd3POQ`) - Raspy, young male voice

These voices are pre-made by ElevenLabs and don't require any special setup beyond your API key.

### OpenAI Model
You can change the OpenAI model by modifying the `model` parameter:
```python
response = openai_client.responses.create(
    model="gpt-4o",  # or "gpt-3.5-turbo", "gpt-4", etc.
    input=prompt
)
```

### Audio Settings
The audio track is configured for 16kHz sample rate:
```python
audio = audio_track.AudioStreamTrack(framerate=16000)
```

### System Prompt
You can customize the AI's personality by modifying the system prompt:
```python
input=f"You are a helpful and friendly assistant. Respond to: {text}"
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
This example provides a foundation for building more complex AI conversation bots. You could extend it by:
- Adding conversation memory and context tracking
- Implementing different AI personalities or roles
- Adding support for multiple languages
- Implementing real-time language translation
- Adding visual elements to the browser interface
- Integrating with external APIs or databases
- Adding conversation analytics and logging

## Use Cases

This example can be adapted for various applications:
- **Customer Support**: AI-powered customer service agents
- **Education**: Interactive tutoring and learning assistants
- **Healthcare**: Patient intake and preliminary consultation bots
- **Entertainment**: Interactive storytelling and gaming companions
- **Accessibility**: Voice-controlled assistants for users with disabilities
- **Language Learning**: Conversational practice partners

## Support

- [Stream Documentation](https://getstream.io/video/docs/)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [ElevenLabs Documentation](https://elevenlabs.io/docs)
- [OpenAI Documentation](https://platform.openai.com/docs)
- [Stream Community](https://github.com/GetStream/stream-video-python)
