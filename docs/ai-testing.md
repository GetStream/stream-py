## Python tests:

When writing a python test, follow these rules:

1. Do not mock things unless you are directly asked to do that
2. Do not create 1 file for each test, better if we use 1 test file per topic (eg. test_rtc.py)
3. Test should run using uv and pytest
4. All tests live under the tests/ folder
5. Try to reuse code when possible, there is a conftest file with fixtures where you can put helpers or re-use existing ones
6. If you need a client, use the fixture and it will get you a client loaded from .env
7. Sometime you need to create the client object (eg. use a client with wrong credentials), in that case you can use Stream(api_key="your_api_key", api_secret="your_api_secret") directly
8. Some tests need to be async, make sure to use the pytest decorator for that
9. When you initialize a call object, you need to pass two params: type and id. Type should always be "default" and an arbitrary string like a uuidv4 string

This is a good example of python test:

```python
@pytest.mark.asyncio
async def test_rtc_call_initialization(client):
    # uses the client from fixture and create an rtc_call object
    call = client.video.call("default", "123")

    # this is supposed to resolve and not throw
    await call.join()
```

uv is used to manage the python project and pytest for tests, make sure to use these two

## Mock testing with RTCCalls

For testing purposes, the SDK provides a mocking mechanism that simulates a real call without connecting to the actual API or WebRTC infrastructure. This is useful for unit testing or integration testing without external dependencies.

### Basic Mock Setup

Here's how to use the mock functionality:

```python
from getstream.video.rtc.rtc import MockConfig, MockParticipant, MockAudioConfig

# Create a call object
rtc_call = client.video.rtc_call("default", uuid.uuid4())

# Set up mock audio configuration with a WAV file
mock_audio = MockAudioConfig(
    audio_file_path="/path/to/audio.wav",
    realtime_clock=True,  # Send events at realistic 20ms intervals
)

# Set up mock audio configuration with an MP3 file
mp3_mock_audio = MockAudioConfig(
    audio_file_path="/path/to/audio.mp3",
    realtime_clock=True,
)

# Create mock participants
mock_participant1 = MockParticipant(
    user_id="mock-user-1",
    name="Mock User 1",
    audio=mock_audio
)

mock_participant2 = MockParticipant(
    user_id="mock-user-2",
    name="Mock User 2",
    audio=mp3_mock_audio
)

# Create the mock configuration with participants
mock_config = MockConfig(participants=[mock_participant1, mock_participant2])

# Set the mock configuration on the call object
rtc_call.set_mock(mock_config)
```

### Participant Lifecycle

Mock participants have the following lifecycle:
1. When you join a call, all configured participants automatically join
2. If a participant has audio configured, audio events start streaming from their file
3. When a participant's audio file is fully consumed, a `participant_left` event is automatically sent
4. When all mock participants have left, the connection will automatically exit

This automatic lifecycle makes testing audio processing straightforward - the test will naturally complete when all audio sources are exhausted.

### Handling Events

There are two recommended ways to handle events from a mocked call:

#### Method 1: Using Event Handlers (recommended for most cases)

```python
# Register specialized event handlers
async with rtc_call.join("test-user") as connection:
    # Define event handlers
    async def handle_audio_packet(event):
        audio = event.rtc_packet.audio
        print(f"Received audio packet: {len(audio.pcm.payload)} bytes")

    async def handle_participant_joined(event):
        participant = event.participant_joined
        print(f"Participant joined: {participant.user_id}")

    async def handle_participant_left(event):
        participant = event.participant_left
        print(f"Participant left: {participant.user_id}")

    # Register the handlers
    await on_event(connection, "audio_packet", handle_audio_packet)
    await on_event(connection, "participant_joined", handle_participant_joined)
    await on_event(connection, "participant_left", handle_participant_left)

    # Process events (handlers will be called automatically)
    async for event in connection:
        # Iteration will exit when all participants have left
        pass
```

#### Method 2: Using Python 3.10+ Match Pattern (for more granular control)

```python
# Use pattern matching to handle different event types
async with rtc_call.join("test-user") as connection:
    async for event in connection:
        match event:
            case events.Event(rtc_packet=rtc_packet) if rtc_packet.audio:
                # Process audio packet
                print(f"Received audio packet: {len(rtc_packet.audio.pcm.payload)} bytes")
            case events.Event(participant_joined=participant):
                print(f"Participant joined: {participant.user_id}")
            case events.Event(participant_left=participant):
                print(f"Participant left: {participant.user_id}")
            case events.Event(error=error):
                print(f"Error received: {error.code} - {error.message}")
            case _:
                print(f"Unhandled event type: {event}")
```

### Supported Features

The mock supports the following features:
- Adding mock participants with custom user IDs and names
- Playing audio from WAV and MP3 files (detected by file extension)
- Controlling whether audio events are sent at realistic timing intervals (20ms) or as fast as possible
- Automatic participant lifecycle management based on audio file consumption
- Both WAV and MP3 files are automatically converted to PCM 48000hz and included in events

Mock joining is implemented in Go inside the binding/main.go. The Go code creates a simulated call environment that sends audio events for participants based on the configuration provided. Audio is streamed from the configured files and converted to the appropriate format for WebRTC.

## Go tests

- Write compact idiomatic tests in Golang
- Use testify libs for assertions
- Structure tests in test suites (testify lib) so tests are better organized and can reuse setup/teardown steps
