# Stream + Deepgram Real-time Transcription Example

This example demonstrates how to build a real-time call transcription bot using Stream's Video SDK and Deepgram's Speech-to-Text API.

## What it does

- 🤖 Creates a transcription bot that joins a Stream video call
- 🎙️ Transcribes all audio in real-time using Deepgram STT
- 🌐 Opens a browser link for users to join the call
- 📝 Displays transcriptions with timestamps in the terminal

## Prerequisites

1. **Stream Account**: Get your API credentials from [Stream Dashboard](https://dashboard.getstream.io)
2. **Deepgram Account**: Get your API key from [Deepgram Console](https://console.deepgram.com)
3. **Python 3.9+**: Required for running the example

## Installation

1. **Navigate to the example directory:**
   ```bash
   cd examples/stt_deepgram_transcription
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

   Note: This will install the getstream package, deepgram-sdk, aiortc (for WebRTC), and other required dependencies.

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
   ```

## Usage

1. **Run the example:**
   ```bash
   python main.py
   ```

2. **What happens:**
   - A unique call ID is generated
   - A browser opens with the Stream call interface
   - The transcription bot joins the call
   - Speak into your microphone in the browser
   - See real-time transcriptions in the terminal

3. **Example output:**
   ```
   🎙️  Stream + Deepgram Real-time Transcription Example
   =======================================================
   ✅ Credentials loaded successfully
   📞 Call ID: transcription-demo-a1b2c3d4
   🔑 Created token for user: transcription-bot
   Opening browser to: https://pronto.getstream.io/bare/join/?api_key=...
   Browser opened successfully!

   🤖 Starting transcription bot...
   The bot will join the call and transcribe all audio it receives.
   Speak in the browser call and see the transcriptions appear here!

   Press Ctrl+C to stop the transcription bot.

   ✅ Bot joined call: transcription-demo-a1b2c3d4
   🎧 Listening for audio... (Press Ctrl+C to stop)
   [14:32:15] user-123: Hello, can you hear me?
   [14:32:18] user-123: This is a test of the transcription service.
   [14:32:22] user-456: Yes, I can hear you clearly!
   ```

## How it works

### Browser Opening
The `open_browser()` helper function creates a URL with the required parameters:
- `api_key`: Your Stream API key
- `token`: JWT token for authentication
- `call_id`: The unique call identifier

### Real-time Transcription
1. The bot joins the Stream call using the RTC SDK
2. Audio events are captured via `@connection.on("audio")`
3. Audio data is processed through Deepgram STT
4. Transcriptions are displayed with timestamps

### Code Structure
```python
# Load credentials from .env
api_key, api_secret, deepgram_key = load_credentials()

# Create Stream client and call
client = Stream(api_key=api_key, api_secret=api_secret)
call = client.video.call("default", call_id)

# Initialize Deepgram STT
stt = Deepgram(api_key=deepgram_key)

# Join call and set up handlers
async with await rtc.join(call, bot_user_id) as connection:
    @connection.on("audio")
    async def on_audio(pcm, user):
        await stt.process_audio(pcm, user)

    @stt.on("transcript")
    async def on_transcript(text, user):
        print(f"[{timestamp}] {user}: {text}")
```

## Troubleshooting

### Browser doesn't open
- Check that the URL is correct in the console output
- Manually copy and paste the URL into your browser
- Ensure your firewall allows the browser to open URLs

### No transcriptions appearing
- Check that your microphone is working in the browser
- Verify your Deepgram API key is valid
- Ensure the bot successfully joined the call (look for "✅ Bot joined call")

### Connection errors
- Verify your Stream API credentials are correct
- Check your internet connection
- Ensure the Stream base URL is correct

### Installation Issues

#### WebRTC Dependencies
If you encounter issues with aiortc or WebRTC dependencies:

- **macOS**: Install system dependencies first:
  ```bash
  brew install opus libvpx pkg-config
  ```

- **Linux (Ubuntu/Debian)**:
  ```bash
  sudo apt-get update
  sudo apt-get install libopus-dev libvpx-dev pkg-config
  ```

- **Windows**: Install Microsoft C++ Build Tools and ensure you have the latest Visual Studio build tools

#### Module not found errors
If you see `ModuleNotFoundError` for specific packages:
```bash
# Reinstall with all dependencies
pip uninstall getstream aiortc -y
pip install -e . --force-reinstall
```

#### Permission errors
If you encounter permission errors during installation:
```bash
# Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

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

## Related Examples

- **TTS Examples**: See `../tts_*` directories for text-to-speech examples
- **VAD Examples**: See `../vad_*` directories for voice activity detection
- **Combined Examples**: Check the main test files for full echo/conversation bots

## Development

### Running Tests
The example includes a basic test suite to validate functionality. **Note**: Install dependencies first before running tests.

```bash
# Install dependencies
pip install -e .

# Run tests
python test_example.py
```

This test validates:
- Credential loading from environment variables
- URL construction for browser opening
- Basic import functionality

**Note**: If tests fail due to missing dependencies (like `aioice`), make sure you've installed all dependencies using `pip install -e .` first.

### Code Structure
- `main.py`: Main example implementation
- `test_example.py`: Basic test suite
- `pyproject.toml`: Package dependencies and metadata
- `env.example`: Template for environment variables

## Support

- [Stream Documentation](https://getstream.io/video/docs/)
- [Deepgram Documentation](https://developers.deepgram.com/)
- [Stream Community](https://github.com/GetStream/stream-video-python)
