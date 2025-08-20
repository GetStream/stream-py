# AssemblyAI STT Example Summary

## Overview

This example demonstrates real-time speech-to-text transcription in Stream video calls using the AssemblyAI plugin. It's designed to be a drop-in replacement for the Deepgram example, showing how easy it is to switch between different STT providers in the GetStream ecosystem.

## What This Example Provides

### 🎯 **Core Functionality**
- **Real-time transcription bot** that joins Stream video calls
- **Live audio processing** with AssemblyAI's streaming API
- **Browser interface** for users to join calls
- **Terminal output** showing transcripts with timestamps

### 🔧 **Technical Features**
- **AssemblyAI integration** using the custom plugin
- **WebRTC audio capture** from Stream calls
- **Event-driven architecture** for real-time processing
- **Error handling** and graceful cleanup
- **User management** with automatic cleanup

### 📊 **Transcription Features**
- **Partial transcripts** for immediate feedback
- **Final transcripts** with confidence scores
- **Automatic punctuation** for readability
- **Utterance detection** for natural speech segmentation
- **Multi-language support** (configurable)

## Comparison with Deepgram Example

| Feature | Deepgram Example | AssemblyAI Example |
|---------|------------------|-------------------|
| **STT Provider** | Deepgram | AssemblyAI |
| **API Integration** | Deepgram SDK | AssemblyAI SDK |
| **Audio Format** | PCM 16-bit | PCM 16-bit |
| **Sample Rate** | Configurable | Configurable (default: 48kHz) |
| **Language Support** | Multi-language | Multi-language |
| **Real-time** | ✅ Yes | ✅ Yes |
| **Partial Results** | ✅ Yes | ✅ Yes |
| **Confidence Scores** | ✅ Yes | ✅ Yes |
| **Error Handling** | ✅ Yes | ✅ Yes |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Stream Call   │───▶│  AssemblyAI STT  │───▶│  Terminal       │
│                 │    │  Plugin          │    │  Output         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│  Browser UI     │    │  Audio Stream    │
│  (User Join)    │    │  Processing      │
└─────────────────┘    └──────────────────┘
```

## Key Components

### 1. **Main Application (`main.py`)**
- Call creation and management
- User authentication and tokens
- Browser interface setup
- Event handler registration

### 2. **AssemblyAI STT Plugin**
- Real-time audio processing
- Streaming API integration
- Event emission for transcripts
- Error handling and recovery

### 3. **Stream Integration**
- WebRTC connection management
- Audio track capture
- Participant management
- Call lifecycle handling

## Usage Scenarios

### 🎙️ **Live Meeting Transcription**
- Real-time captions during video calls
- Meeting minutes generation
- Accessibility support for hearing-impaired users

### 📝 **Content Creation**
- Podcast transcription
- Interview recording
- Educational content processing

### 🔍 **Quality Assurance**
- Call center monitoring
- Training session review
- Compliance documentation

## Configuration Options

The example is highly configurable through the `AssemblyAISTT` constructor:

```python
stt = AssemblyAISTT(
    sample_rate=48000,                    # Audio quality
    language="en",                        # Language selection
    interim_results=True,                 # Real-time feedback
    enable_partials=True,                 # Partial transcripts
    enable_automatic_punctuation=True,    # Auto-punctuation
    enable_utterance_end_detection=True,  # Speech segmentation
)
```

## Performance Characteristics

- **Latency**: Low-latency real-time processing
- **Accuracy**: High-quality transcription with confidence scoring
- **Scalability**: Handles multiple participants simultaneously
- **Reliability**: Automatic error recovery and connection management

## Extensibility

This example serves as a foundation for building more complex applications:

- **Multi-language support** for international teams
- **Custom vocabulary** for domain-specific terms
- **Speaker identification** for multi-participant calls
- **Analytics integration** for usage metrics
- **Webhook integration** for external systems

## Getting Started

1. **Install dependencies**: `uv sync`
2. **Configure environment**: Copy `env.example` to `.env`
3. **Add API keys**: Stream and AssemblyAI credentials
4. **Run the example**: `uv run main.py`
5. **Join the call**: Browser will open automatically
6. **Start speaking**: Watch real-time transcription

## Troubleshooting

### Common Issues
- **API key errors**: Verify AssemblyAI credentials
- **Audio not detected**: Check microphone permissions
- **Connection failures**: Verify internet and Stream credentials
- **Import errors**: Ensure all dependencies are installed

### Debug Mode
Enable verbose logging by modifying the logging level in `main.py`:
```python
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")
```

## Next Steps

After running this example successfully:

1. **Customize the configuration** for your use case
2. **Integrate with your application** using the plugin directly
3. **Explore advanced features** like custom models and vocabulary
4. **Build production applications** with proper error handling and monitoring

## Support Resources

- **AssemblyAI Documentation**: https://www.assemblyai.com/docs
- **GetStream Documentation**: https://getstream.io/docs
- **Plugin Source**: `getstream/plugins/assemblyai/`
- **Example Source**: `examples/stt_assemblyai_transcription/`
