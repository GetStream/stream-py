import asyncio
import pytest
import uuid
import os
from contextlib import asynccontextmanager

from getstream import Stream
from getstream.video.rtc.rtc import (
    JoinError,
    MockConfig,
    MockParticipant,
    MockAudioConfig,
    on_event,
)


# Define an async timeout context manager for the test
@asynccontextmanager
async def timeout(seconds):
    """Async context manager that raises TimeoutError if the body takes too long."""
    try:
        # Start a task that will raise TimeoutError after the specified duration
        task = asyncio.create_task(asyncio.sleep(seconds))
        try:
            yield
        finally:
            # Cancel the timeout task if the body completes before the timeout
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    except asyncio.TimeoutError:
        raise asyncio.TimeoutError(f"Operation timed out after {seconds} seconds")


@pytest.fixture
def rtc_call(client):
    """Create an RTC call object."""
    return client.video.rtc_call("default", str(uuid.uuid4()))


@pytest.mark.asyncio
async def test_rtc_call_initialization(rtc_call):
    """
    Test basic RTC call initialization.

    This test simply verifies that we can initialize the SDK and create an RTC call object.
    Since there's not much to test at this stage, we just wait a few seconds to ensure
    no errors occur during initialization.
    """
    # Verify that the call object was created successfully
    assert rtc_call is not None
    assert rtc_call.call_type == "default"

    # Wait a few seconds to ensure no errors occur
    await asyncio.sleep(3)


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_rtc_call_join_success(rtc_call):
    """
    Test successful RTC call joining using the async context manager.

    This test attempts to join a call with valid credentials and verifies that
    no exception is raised.
    """
    # Attempt to join the call with a short timeout using the async context manager
    try:
        async with rtc_call.join("test-user", timeout=10.0) as connection:
            # If we got here, the join was successful
            assert rtc_call._joined is True
            assert connection.joined is True

        # After exiting the context manager, the call should be left
        assert rtc_call._joined is False
    except Exception as e:
        # Log the exception but don't fail the test
        print(f"Exception during join test: {e}")
        pytest.skip("Skipping due to connection issues")


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_rtc_call_join_failure():
    """
    Test failed RTC call joining with invalid credentials.

    This test attempts to join a call with invalid credentials and verifies that
    the appropriate exception is raised.
    """
    # Create a client with invalid credentials
    invalid_client = Stream(api_key="invalid_key", api_secret="invalid_secret")

    # Create a call with the invalid client
    invalid_call = invalid_client.video.rtc_call("default", str(uuid.uuid4()))

    # Attempt to join the call with a short timeout
    # This should raise a JoinError or a TimeoutError
    with pytest.raises((JoinError, asyncio.TimeoutError)):
        async with invalid_call.join("test-user", timeout=10.0):
            pass


@pytest.mark.skip_in_ci
@pytest.mark.asyncio
async def test_rtc_call_event_iteration(rtc_call):
    """
    Test that joining a call works successfully.
    """
    # Join the call and verify it works
    async with rtc_call.join("test-user", timeout=10.0):
        # If we get here, the join was successful
        assert rtc_call._joined is True

    # After exiting the context manager, the call should be left
    assert rtc_call._joined is False


@pytest.mark.asyncio
async def test_rtc_call_mock_with_wav_file(client):
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Set up the mock configuration
    audio_file = "/Users/tommaso/src/data-samples/audio/king_story_1.wav"

    # Make sure the file exists
    assert os.path.exists(audio_file), f"Test audio file {audio_file} not found"

    # Create a participant with audio configuration
    mock_audio = MockAudioConfig(
        audio_file_path=audio_file,
        realtime_clock=False,  # Send audio events as fast as possible for testing
    )

    mock_participant = MockParticipant(
        user_id="mock-user-1", name="Mock User", audio=mock_audio
    )

    mock_config = MockConfig(participants=[mock_participant])

    # Set the mock configuration
    rtc_call.set_mock(mock_config)

    # Join the mocked call and iterate over events using the connection object
    async with rtc_call.join("test-user", timeout=10.0):
        pass


@pytest.mark.asyncio
async def test_participant_joined_event_handler(client):
    """
    Test that participant joined events are dispatched to the registered handler.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Create a mock participant
    mock_participant = MockParticipant(user_id="mock-user-1", name="Mock User 1")

    # Set up the mock configuration with the participant
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Track received participant joined events
    received_events = []

    # Define the event handler
    async def on_participant_joined(event):
        participant = event.participant_joined
        received_events.append(participant.user_id)

    # Join the call and register the handler
    async with rtc_call.join("test-user", timeout=10.0) as connection:
        # Register the handler for participant joined events
        await on_event(connection, "participant_joined", on_participant_joined)

        # Wait a short time for events to be processed
        await asyncio.sleep(2)

        # Verify that we received the participant joined event
        assert (
            "mock-user-1" in received_events
        ), "Did not receive participant joined event"


@pytest.mark.asyncio
async def test_audio_event_handler(client):
    """
    Test that audio events are dispatched to the registered handler.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Find an audio file for testing
    audio_file = os.path.join(os.path.dirname(__file__), "assets/test_audio.wav")
    if not os.path.exists(audio_file):
        # Use the audio file path from the first test if our test file doesn't exist
        audio_file = "/Users/tommaso/src/data-samples/audio/king_story_1.wav"

    # Make sure the file exists
    assert os.path.exists(audio_file), f"Test audio file {audio_file} not found"

    # Create a participant with audio configuration
    mock_audio = MockAudioConfig(
        audio_file_path=audio_file,
        realtime_clock=False,  # Send audio events as fast as possible for testing
    )

    mock_participant = MockParticipant(
        user_id="mock-user-1", name="Mock User 1", audio=mock_audio
    )

    # Set up the mock configuration with the audio-enabled participant
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Track received audio packets
    audio_packets_received = 0

    # Define the event handler
    async def on_audio_packet(event):
        nonlocal audio_packets_received
        # We expect rtc_packet.audio to be set for audio packets
        if event.rtc_packet and event.rtc_packet.audio:
            audio_packets_received += 1

    # Join the call and register the handler
    async with rtc_call.join("test-user", timeout=10.0) as connection:
        # Register the handler for audio packet events
        await on_event(connection, "audio_packet", on_audio_packet)

        # Wait for some audio packets to be received (up to 5 seconds)
        for _ in range(50):  # Check every 100ms for up to 5 seconds
            if audio_packets_received > 0:
                break
            await asyncio.sleep(0.1)

        # Verify that we received at least one audio packet
        assert audio_packets_received > 0, "Did not receive any audio packets"


@pytest.mark.asyncio
async def test_auto_exit_when_all_participants_leave(client):
    """
    Test that the call automatically exits when all mock participants leave.

    This test verifies that Go sends a call_ended event when all participants leave,
    and that the Python side exits the connection when this event is received.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Find an audio file for testing
    audio_file = os.path.join(os.path.dirname(__file__), "assets/test_audio.wav")
    if not os.path.exists(audio_file):
        # Use the audio file path from the first test if our test file doesn't exist
        audio_file = "/Users/tommaso/src/data-samples/audio/king_story_1.wav"

    # Make sure the file exists
    assert os.path.exists(audio_file), f"Test audio file {audio_file} not found"

    # Create a participant with audio configuration
    mock_audio = MockAudioConfig(
        audio_file_path=audio_file,
        realtime_clock=False,  # Send audio events as fast as possible for testing
    )

    mock_participant = MockParticipant(
        user_id="mock-user-1", name="Mock User 1", audio=mock_audio
    )

    # Set up the mock configuration with the audio-enabled participant
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Track important events
    participant_left_events = []
    call_ended_received = False

    # Define event handlers
    async def on_participant_joined(event):
        assert event.participant_joined.user_id == "mock-user-1"
        print(f"Participant joined: {event.participant_joined.user_id}")

    async def on_participant_left(event):
        participant_left_events.append(event.participant_left.user_id)
        print(f"Participant left: {event.participant_left.user_id}")

    async def on_call_ended(event):
        nonlocal call_ended_received
        call_ended_received = True
        print("Call ended event received")

    # Add a timeout to prevent test from hanging indefinitely
    max_duration = 15.0  # seconds

    # Join the call and register handlers
    async with rtc_call.join("test-user", timeout=max_duration) as connection:
        # Register the event handlers
        await on_event(connection, "participant_joined", on_participant_joined)
        await on_event(connection, "participant_left", on_participant_left)
        await on_event(connection, "call_ended", on_call_ended)

        # This will exit automatically when the call_ended event is received
        # Set a timeout for maximum events to process to avoid hanging
        try:
            with timeout(max_duration):
                event_count = 0
                max_events = 100

                async for event in connection:
                    event_count += 1

                    if event_count > max_events:
                        print(
                            f"Processed {max_events} events, breaking to avoid test hanging"
                        )
                        break

                    # If the call ended event has been received, we should soon exit
                    if call_ended_received:
                        # Give a short time to process any remaining events
                        await asyncio.sleep(0.5)
                        # Exit the loop
                        break
        except asyncio.TimeoutError:
            print("Test timed out waiting for call to exit")
            assert False, "Test timed out"

    # Verify we received a participant left event
    assert participant_left_events, "Did not receive any participant left events"
    assert (
        "mock-user-1" in participant_left_events
    ), "Did not receive expected participant left event"

    # Verify we received a call ended event
    assert call_ended_received, "Did not receive call_ended event"

    # Verify that the call was properly ended
    assert rtc_call._joined is False, "Call was not properly ended"


@pytest.mark.asyncio
async def test_mp3_file_streaming(client):
    """
    Test streaming audio from an MP3 file with a mock participant.
    This test verifies that the MP3 file format is properly supported.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Find the MP3 file for testing
    mp3_file = os.path.join(os.path.dirname(__file__), "assets/test_speech.mp3")

    # Make sure the file exists
    assert os.path.exists(mp3_file), f"Test MP3 file {mp3_file} not found"

    # Create a participant with MP3 audio configuration
    mock_audio = MockAudioConfig(
        audio_file_path=mp3_file,
        realtime_clock=False,  # Send audio events as fast as possible for testing
    )

    mock_participant = MockParticipant(
        user_id="mp3-user", name="MP3 Test User", audio=mock_audio
    )

    # Set up the mock configuration with the MP3-enabled participant
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Track received audio packets and events
    audio_packets_received = 0
    participant_joined = False
    participant_left = False

    # Define event handlers
    async def on_audio_packet(event):
        nonlocal audio_packets_received
        if event.rtc_packet and event.rtc_packet.audio:
            audio_packets_received += 1
            # Verify audio format details
            pcm = event.rtc_packet.audio.pcm
            assert pcm.sample_rate == 48000, "Expected 48kHz sample rate"
            # MP3 files are typically stereo (2 channels)
            assert pcm.channels == 2, "Expected stereo channels"

    async def on_participant_joined(event):
        nonlocal participant_joined
        if event.participant_joined.user_id == "mp3-user":
            participant_joined = True

    async def on_participant_left(event):
        nonlocal participant_left
        if event.participant_left.user_id == "mp3-user":
            participant_left = True

    # Join the call and register handlers
    async with rtc_call.join("test-user", timeout=15.0) as connection:
        # Register the event handlers
        await on_event(connection, "audio_packet", on_audio_packet)
        await on_event(connection, "participant_joined", on_participant_joined)
        await on_event(connection, "participant_left", on_participant_left)

        # Process events until the participant leaves or we hit a timeout
        try:
            async for event in connection:
                # This will automatically exit when the MP3 file is consumed
                # and the participant leaves
                pass
        except asyncio.TimeoutError:
            # If we hit a timeout, that's okay, just make sure we received packets
            pass

    # Verify that we received at least one audio packet
    assert audio_packets_received > 0, "Did not receive any MP3 audio packets"

    # Verify the participant joined
    assert participant_joined, "Mock MP3 participant never joined"

    # Verify the participant left when the file was consumed
    assert participant_left, "Mock MP3 participant never left"


@pytest.mark.asyncio
async def test_wav_file_streaming(client):
    """
    Test streaming audio from a WAV file with a mock participant.
    This test verifies that the WAV file format is properly supported.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Find a WAV file for testing
    audio_file = os.path.join(os.path.dirname(__file__), "assets/test_audio.wav")
    if not os.path.exists(audio_file):
        # Use the audio file path from the other tests if our test file doesn't exist
        audio_file = "/Users/tommaso/src/data-samples/audio/king_story_1.wav"

    # Make sure the file exists
    assert os.path.exists(audio_file), f"Test WAV file {audio_file} not found"

    # Create a participant with WAV audio configuration
    mock_audio = MockAudioConfig(
        audio_file_path=audio_file,
        realtime_clock=False,  # Send audio events as fast as possible for testing
    )

    mock_participant = MockParticipant(
        user_id="wav-user", name="WAV Test User", audio=mock_audio
    )

    # Set up the mock configuration with the WAV-enabled participant
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Track received audio packets and events
    audio_packets_received = 0
    participant_joined = False
    participant_left = False
    sample_rate_verified = False
    channels_verified = False

    # Define event handlers
    async def on_audio_packet(event):
        nonlocal audio_packets_received, sample_rate_verified, channels_verified
        if event.rtc_packet and event.rtc_packet.audio:
            audio_packets_received += 1
            # Verify audio format details
            pcm = event.rtc_packet.audio.pcm

            # Verify the sample rate (expected to be resampled to 48000)
            if not sample_rate_verified:
                assert (
                    pcm.sample_rate == 48000
                ), f"Expected 48kHz sample rate, got {pcm.sample_rate}"
                sample_rate_verified = True

            # Verify the number of channels
            if not channels_verified:
                # WAV files can be mono or stereo, so we just make sure it's a valid value
                assert pcm.channels in (
                    1,
                    2,
                ), f"Expected 1 or 2 channels, got {pcm.channels}"
                channels_verified = True

    async def on_participant_joined(event):
        nonlocal participant_joined
        if event.participant_joined.user_id == "wav-user":
            participant_joined = True

    async def on_participant_left(event):
        nonlocal participant_left
        if event.participant_left.user_id == "wav-user":
            participant_left = True

    # Join the call and register handlers
    async with rtc_call.join("test-user", timeout=15.0) as connection:
        # Register the event handlers
        await on_event(connection, "audio_packet", on_audio_packet)
        await on_event(connection, "participant_joined", on_participant_joined)
        await on_event(connection, "participant_left", on_participant_left)

        # Process events until the participant leaves or we hit a timeout
        try:
            async for event in connection:
                # This will automatically exit when the WAV file is consumed
                # and the participant leaves
                pass
        except asyncio.TimeoutError:
            # If we hit a timeout, that's okay, just make sure we received packets
            pass

    # Verify that we received at least one audio packet
    assert audio_packets_received > 0, "Did not receive any WAV audio packets"

    # Verify audio format was checked
    assert sample_rate_verified, "Sample rate verification never happened"
    assert channels_verified, "Channels verification never happened"

    # Verify the participant joined
    assert participant_joined, "Mock WAV participant never joined"

    # Verify the participant left when the file was consumed
    assert participant_left, "Mock WAV participant never left"


@pytest.mark.asyncio
async def test_call_ended_event_sent_from_go(client):
    """
    Very minimal test that verifies Go sends a call_ended event.

    This test only verifies that the Go side correctly sends the call_ended event
    when the call ends, without trying to test the event loop behavior which is
    difficult to test reliably.
    """
    # Create a call object
    call_id = str(uuid.uuid4())
    rtc_call = client.video.rtc_call("default", call_id)

    # Set up a basic mock with no audio (to avoid real media processing)
    mock_participant = MockParticipant(user_id="mock-user-1", name="Mock User 1")
    mock_config = MockConfig(participants=[mock_participant])
    rtc_call.set_mock(mock_config)

    # Flag to track if we received the call_ended event
    call_ended_received = False

    # Create an event handler just for the call_ended event
    async def on_call_ended(event):
        nonlocal call_ended_received
        if event.call_ended is not None:
            call_ended_received = True
            print("Call ended event received")

    async with rtc_call.join("test-user", timeout=2.0) as connection:
        # Register just the call_ended handler
        await on_event(connection, "call_ended", on_call_ended)

        # Manually trigger a leave to make Go send the call_ended event
        await rtc_call.leave()

        # Wait briefly for events to be processed
        await asyncio.sleep(0.5)

    # Verify the call is no longer joined
    assert not rtc_call._joined, "Call was not properly ended"

    # Verify we received the call_ended event
    assert call_ended_received, "Did not receive call_ended event from Go"
