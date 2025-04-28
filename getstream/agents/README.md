# GetStream.io Agents

This directory contains various agent implementations for GetStream.io's Python SDK.

## Voice Activity Detection (VAD)

The `VAD` class provides a voice activity detection system that can be used to detect speech in audio data. It's designed to:

- Process raw PCM audio data
- Detect speech vs. silence
- Accumulate speech segments and discard silence
- Emit detected speech as events

### Usage Example

```python
import asyncio
from getstream.agents.silero.vad import Silero
import numpy as np

async def main():
    # Create a VAD instance
    vad = Silero(
        sample_rate=16000,
        silence_threshold=0.5, 
        speech_pad_ms=300,  # Padding around speech segments
        min_speech_ms=250,  # Minimum speech duration to emit
    )
    
    # Set up audio event handler
    @vad.on("audio")
    async def on_speech(pcm_data, user_metadata):
        # Handle detected speech segments
        print(f"Speech detected: {len(pcm_data)} bytes")
    
    # Process audio data
    # PCM_DATA should be 16-bit PCM audio data as bytes
    await vad.process_audio(PCM_DATA)
    
    # Clean up when done
    await vad.close()

asyncio.run(main())
```

### Integration with RTC

The VAD system is designed to work with GetStream's RTC connection manager:

```python
from getstream.agents.silero.vad import Silero
from getstream.stream import Stream
from getstream.video import rtc

async def main():
    # Initialize Stream client
    client = Stream(api_key="YOUR_API_KEY", api_secret="YOUR_API_SECRET")
    
    # Get a call
    call = client.video.call("default", "your-call-id")
    
    # Create a VAD instance
    vad = Silero()
    
    # Set up a speech event handler
    @vad.on("audio")
    async def on_speech_detected(pcm_data, user):
        # Handle speech from participants
        print(f"Speech detected from user: {user.get('user_id', 'unknown')}")
    
    # Join the call
    async with await rtc.join(call, "your-user-id") as connection:
        # Connect the VAD to the RTC audio events
        @connection.on("audio")
        async def on_audio(pcm_data, user):
            # Forward audio to VAD for speech detection
            await vad.process_audio(pcm_data, user)
        
        # Wait for the call to end
        await connection.wait()
    
    # Clean up
    await vad.close()

asyncio.run(main())
```

### Available VAD Implementations

- `getstream.agents.silero.vad.Silero`: Implementation using the Silero VAD model for high-quality speech detection.

### Creating Custom VAD Implementations

You can create custom VAD implementations by extending the base `VAD` class and implementing the `is_speech` method.

```python
from getstream.agents.vad import VAD
import numpy as np

class CustomVAD(VAD):
    async def is_speech(self, frame: np.ndarray) -> float:
        """
        Determine if the audio frame contains speech.
        
        Args:
            frame: Audio frame as numpy array
            
        Returns:
            Probability (0.0 to 1.0) that the frame contains speech
        """
        # Your custom speech detection logic here
        # For example, using a simple amplitude threshold
        energy = np.mean(np.abs(frame))
        return float(energy > 0.1)
``` 