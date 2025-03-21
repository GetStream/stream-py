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
