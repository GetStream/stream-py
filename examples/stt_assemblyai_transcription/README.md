# Stream + AssemblyAI STT Example

This example demonstrates how to build a real-time transcription bot that joins a Stream video call and transcribes speech using AssemblyAI's Speech-to-Text API.

## What it does

- 🤖 Creates a transcription bot that joins a Stream video call
- 🌐 Opens a browser interface for users to join the call
- 🎙️ Transcribes speech in real-time using AssemblyAI STT
- 📝 Displays transcriptions with timestamps and confidence scores in the terminal

## Prerequisites

1. **Stream Account**: Get your API credentials from [Stream Dashboard](https://dashboard.getstream.io)
2. **AssemblyAI Account**: Get your API key from [AssemblyAI Console](https://www.assemblyai.com/)
3. **Python 3.10+**: Required for running the example

## Installation

You can use your preferred package manager, but we recommend [`uv`](https://docs.astral.sh/uv/).

1. **Navigate to this directory:**
   ```bash
   cd examples/stt_assemblyai_transcription
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment variables:**
   Rename `env.example` to `.env` and fill in your actual credentials.

## Usage

Run the example:
```bash
uv run main.py
```

## Configuration Options

You can customize the AssemblyAI STT settings in the `main.py` file:

```python
stt = AssemblyAISTT(
    sample_rate=48000,                    # Audio sample rate
    language="en",                        # Language code
    interim_results=True,                 # Enable interim results
    enable_partials=True,                 # Enable partial transcripts
    enable_automatic_punctuation=True,    # Auto-punctuation
    enable_utterance_end_detection=True,  # Utterance detection
)
```

## Features

- **Real-time transcription** with low latency
- **Partial transcripts** for immediate feedback
- **Automatic punctuation** for better readability
- **Utterance end detection** for natural speech segmentation
- **Multi-language support** (change the `language` parameter)
- **Confidence scoring** for transcription quality

## How it works

1. **Call Setup**: Creates a Stream video call with unique IDs
2. **Bot Joins**: A transcription bot joins the call as a participant
3. **Audio Processing**: Captures audio from all participants
4. **Real-time Transcription**: Sends audio to AssemblyAI for processing
5. **Results Display**: Shows transcripts in the terminal with timestamps

## Troubleshooting

- **No audio detected**: Ensure your microphone is working and permissions are granted
- **API errors**: Check your AssemblyAI API key and account status
- **Connection issues**: Verify your internet connection and Stream credentials

## AssemblyAI Features

AssemblyAI provides high-quality transcription with:
- **Nova-2 model** for best accuracy
- **Real-time streaming** for low latency
- **Automatic language detection** support
- **Speaker diarization** capabilities
- **Custom vocabulary** support

For more information, visit [AssemblyAI Documentation](https://www.assemblyai.com/docs).
