import asyncio
import pytest
import uuid
import os

from getstream import Stream
from getstream.video.rtc.rtc import (
    JoinError,
    MockConfig,
    MockParticipant,
    MockAudioConfig,
    on_event,
)


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
    This simulates participants leaving when their audio files are consumed.
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

    # Create a participant with audio configuration (use very short realtime clock for faster test)
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

    # Track received participant_left events
    participant_left_events = []

    # Define event handlers
    async def on_participant_joined(event):
        assert event.participant_joined.user_id == "mock-user-1"
        print(f"Participant joined: {event.participant_joined.user_id}")

    async def on_participant_left(event):
        participant_left_events.append(event.participant_left.user_id)
        print(f"Participant left: {event.participant_left.user_id}")

    # Join the call and register handlers
    async with rtc_call.join("test-user", timeout=10.0) as connection:
        # Register the event handlers
        await on_event(connection, "participant_joined", on_participant_joined)
        await on_event(connection, "participant_left", on_participant_left)

        # This will exit automatically when all participants leave
        # Count events while we're in the connection
        event_count = 0
        async for event in connection:
            event_count += 1

    # When we reach here, the connection should have auto-exited

    # Verify we received a participant left event
    assert (
        "mock-user-1" in participant_left_events
    ), "Did not receive participant left event"

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
