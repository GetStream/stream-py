# Audio Recording Example

This example demonstrates two types of audio recording with multiple users:
- **Composite Recording**: Records all users mixed into a single audio file
- **Track Recording**: Records individual audio tracks from specific users

## Setup

### Prerequisites

1. **Stream Account**: Get your API key and secret from [Stream Dashboard](https://dashboard.getstream.io/)
2. **Audio Files**: Prepare 3 audio files (WAV, MP3, MP4, etc.)
3. **Environment Setup**: Create a `.env` file in the `examples/` directory

### Environment Variables

Create `examples/.env`:

```bash
STREAM_API_KEY=your_stream_api_key_here
STREAM_API_SECRET=your_stream_api_secret_here
```

### Audio Files

Update the `AUDIO_FILES` list in `main.py` with paths to your actual audio files:

```python
AUDIO_FILES = [
    "/path/to/your/audio1.wav",  # Bot Alice will play this
    "/path/to/your/audio2.wav",  # Bot Bob will play this  
    "/path/to/your/audio3.wav",  # Bot Charlie will play this
]
```

## Usage

Run the example with one of two recording types:

```bash
# For composite recording (all audio mixed into one file)
python main.py --type composite

# For track recording (individual audio tracks)
python main.py --type track
```

The recordings will be saved in:
- Composite recordings: `recordings/composite/`
- Track recordings: `recordings/tracks/`

## How It Works

1. Creates three bot users (Alice, Bob, and Charlie) with different audio files
2. Creates a recorder bot to handle the recording
3. Joins all bots to the call and adds their audio tracks
4. Records for 20 seconds
5. Saves the recordings to the specified output directory
6. Cleans up by removing all created users

## Code Example

### Recording API

The `start_recording` method accepts the following parameters:
- `recording_types`: List of recording types (COMPOSITE or TRACK)
- `output_dir`: Directory where recordings will be saved
- `user_id_filter` (optional): For track recording, specify which user's audio to record

```python
# Start recording with specified type
await connection.start_recording(
    recording_types=[RecordingType.COMPOSITE],  # or RecordingType.TRACK
    output_dir="recordings/composite"  # or "recordings/tracks"
)

# Record for 20 seconds
await asyncio.sleep(20)

# Stop recording
await connection.stop_recording()
```

### Bot Audio with MediaPlayer

The example uses `aiortc.contrib.media.MediaPlayer` to play audio files for the bots:

```python
# Create a media player from an audio file
player = MediaPlayer(audio_file, loop=True)

# Add the audio track to the call
if player.audio:
    await connection.add_tracks(audio=player.audio)
```

The `MediaPlayer` handles:
- Loading audio files (WAV, MP3, MP4, etc.)
- Continuous playback (with `loop=True`)
- Converting audio to the correct format for WebRTC
- Providing the audio track that can be added to the call

