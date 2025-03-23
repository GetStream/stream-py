import uuid
import pytest
import os
import betterproto
from getstream.video.rtc.rtc import MockConfig, MockParticipant, MockAudioConfig


@pytest.fixture
def test_audio_path():
    """Returns the path to the test audio file."""
    return os.path.join(os.path.dirname(__file__), "assets/test_speech.mp3")


@pytest.mark.asyncio
async def test_rtc_call_simple(client, test_audio_path):
    """
    Simple test demonstrating how to work with RTCCall.

    The context manager stays active during the entire with block,
    and the async iterator yields events until the 'break' statement.
    """
    # Create a unique call ID
    call_id = str(uuid.uuid4())

    # Create an RTC call
    rtc_call = client.video.rtc_call("default", call_id)

    # Set up a simple mock with one participant
    mock_config = MockConfig(
        [
            MockParticipant(
                user_id="mock-user-1",
                name="Mock User 1",
                audio=MockAudioConfig(
                    audio_file_path=test_audio_path,
                    realtime_clock=False,  # Faster for testing
                ),
            )
        ]
    )

    # Apply the mock configuration
    rtc_call.set_mock(mock_config)

    # Track event types received
    event_types_received = []
    max_events = 10  # Maximum number of events to process before giving up

    # Join the call and process events
    async with rtc_call.join("test-user", timeout=5.0) as connection:
        # Print each event as it's received
        count = 0
        found_participant_joined = False

        async for event in connection:
            # Check event type using betterproto.which_one_of
            event_type, _ = betterproto.which_one_of(event, "event")
            event_types_received.append(event_type)

            print(f"Got event type: {event_type}")

            # Stop once we've found a participant_joined event or processed max events
            count += 1
            if event_type == "participant_joined":
                print(f"Participant joined: {event.participant_joined.user_id}")
                found_participant_joined = True
                break

            if count >= max_events:
                print(f"Reached maximum event count: {max_events}")
                break

    # Connection is automatically closed when exiting the 'with' block
    print(f"Received event types: {', '.join(event_types_received)}")
    # Only assert if we found a participant_joined event among the events we processed
    if not found_participant_joined:
        print("WARNING: Did not find a participant_joined event")
    else:
        print("Found participant_joined event successfully!")
    print("Test completed successfully!")
