import uuid
import pytest
import os
import logging
import betterproto
from getstream.video.rtc.rtc import MockConfig, MockParticipant, MockAudioConfig

# Set up logging
logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
def test_audio_path():
    """Returns the path to the test audio file."""
    return os.path.join(os.path.dirname(__file__), "assets/test_speech.mp3")


@pytest.mark.asyncio
async def test_connection_manager_stays_active(client, test_audio_path):
    """Test that the connection manager properly processes events."""
    # Create a unique call ID
    call_id = str(uuid.uuid4())
    print(f"Using call ID: {call_id}")

    # Create an RTC call
    rtc_call = client.video.rtc_call("default", call_id)

    # Set up mock with an audio file
    mock_audio = MockAudioConfig(
        audio_file_path=test_audio_path,
        realtime_clock=False,  # Set to False to receive events faster in tests
    )

    # Create a mock participant
    mock_participant = MockParticipant(
        user_id="mock-user-1", name="Mock User 1", audio=mock_audio
    )

    # Create the mock configuration
    mock_config = MockConfig(participants=[mock_participant])

    # Set the mock configuration on the call
    rtc_call.set_mock(mock_config)

    # Track events received by type
    participant_joined_events = []
    rtc_packet_events = []
    other_events = []

    # Join the call and process events
    print("Joining call...")
    async with rtc_call.join("test-user", timeout=15.0) as connection:
        # Process events, categorize them and break after a few
        count = 0
        async for event in connection:
            # Use betterproto to correctly check the oneof field
            event_type, _ = betterproto.which_one_of(event, "event")
            print(f"Event received: {event_type}")

            # Categorize the event
            if event_type == "participant_joined":
                participant_joined_events.append(event)
                print(f"Participant joined: {event.participant_joined.user_id}")
            elif event_type == "rtc_packet":
                rtc_packet_events.append(event)
                print("RTC packet received")
            else:
                other_events.append(event)
                print(f"Other event type received: {event_type}")

            count += 1
            if count >= 5:  # Process more events to make sure we get some
                break

        # Assert we received at least some events
        all_events = participant_joined_events + rtc_packet_events + other_events
        assert len(all_events) > 0, "Should have received at least one event"

        # We expect at least one participant_joined event for the mock participant
        assert (
            len(participant_joined_events) > 0
        ), "Should have received a participant joined event"

        print(f"Received {len(all_events)} total events")
        print(f"- {len(participant_joined_events)} participant joined events")
        print(f"- {len(rtc_packet_events)} RTC packet events")
        print(f"- {len(other_events)} other events")
        print("Test completed successfully!")

    # Make sure we reached this point - context manager should properly exit
    print("Connection successfully closed")
