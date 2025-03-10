import pytest
import uuid
import asyncio

from getstream import Stream
from getstream.base import StreamAPIException
from getstream.models import (
    CallRequest,
    CallSettingsRequest,
    ScreensharingSettingsRequest,
    OwnCapability,
    LimitsSettingsRequest,
    BackstageSettingsRequest,
    SessionSettingsRequest,
    FrameRecordingSettingsRequest,
)
from getstream.video.call import Call
from datetime import datetime, timezone, timedelta
from tests.test_video_integration import get_openai_api_key_or_skip


def test_setup_client():
    from getstream import Stream

    client = Stream(api_key="your_api_key", api_secret="your_api_secret")
    assert isinstance(client, Stream)
    assert client.api_key == "your_api_key"
    assert client.api_secret == "your_api_secret"
    assert client.timeout == 6.0


def test_create_user(client: Stream):
    from getstream.models import UserRequest

    client.upsert_users(
        UserRequest(
            id="tommaso-id", name="tommaso", role="admin", custom={"country": "NL"}
        ),
        UserRequest(
            id="thierry-id", name="thierry", role="admin", custom={"country": "US"}
        ),
    )

    token = client.create_token("tommaso-id")
    assert token


def test_create_call_with_members(client: Stream):
    import uuid
    from getstream.models import (
        CallRequest,
        MemberRequest,
    )

    call = client.video.call("default", uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id="tommaso-id",
            members=[
                MemberRequest(user_id="thierry-id"),
                MemberRequest(user_id="tommaso-id"),
            ],
        ),
    )


def test_block_unblock_user_from_calls(client: Stream, call: Call, get_user):
    bad_user = get_user()
    call.get_or_create(
        data=CallRequest(
            created_by_id="tommaso-id",
        )
    )
    call.block_user(bad_user.id)
    response = call.get()
    assert len(response.data.call.blocked_user_ids) == 1

    call.unblock_user(bad_user.id)
    response = call.get()
    assert len(response.data.call.blocked_user_ids) == 0


def test_send_custom_event(client: Stream, call: Call, get_user):
    user = get_user()
    call.get_or_create(
        data=CallRequest(
            created_by_id="tommaso-id",
        )
    )
    call.send_call_event(user_id=user.id, custom={"bananas": "good"})


def test_update_settings(call: Call):
    user_id = str(uuid.uuid4())

    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.update(
        settings_override=CallSettingsRequest(
            screensharing=ScreensharingSettingsRequest(
                enabled=True, access_request_enabled=True
            ),
        ),
    )


def test_mute_all(call: Call):
    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.mute_users(
        muted_by_id=user_id,
        mute_all_users=True,
        audio=True,
    )


def test_mute_some_users(call: Call, get_user):
    alice = get_user()
    bob = get_user()

    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    call.mute_users(
        muted_by_id=user_id,
        user_ids=[alice.id, bob.id],
        audio=True,
        video=True,
        screenshare=True,
        screenshare_audio=True,
    )


def test_update_user_permissions(call: Call, get_user):
    user_id = str(uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
        )
    )

    alice = get_user()
    call.update_user_permissions(
        user_id=alice.id,
        revoke_permissions=[OwnCapability.SEND_AUDIO],
    )

    call.update_user_permissions(
        user_id=alice.id,
        grant_permissions=[OwnCapability.SEND_AUDIO],
    )


def test_deactivate_user(client: Stream, get_user):
    alice = get_user()
    bob = get_user()

    # deactivate one user
    client.deactivate_user(user_id=alice.id)

    # reactivates the user
    client.reactivate_user(user_id=alice.id)

    # deactivates users in bulk, this is an async operation
    response = client.deactivate_users(user_ids=[alice.id, bob.id])
    task_id = response.data.task_id

    # this is just an example, in reality it can take a few seconds for a task to be processed
    task_status = client.get_task(task_id)

    if task_status.data.status == "completed":
        print(task_status.data.result)


def test_create_call_with_session_timer(call: Call):
    user_id = str(uuid.uuid4())
    # create a call and set its max duration to 1 hour
    response = call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
            settings_override=CallSettingsRequest(
                limits=LimitsSettingsRequest(
                    max_duration_seconds=3600,
                ),
            ),
        )
    )

    assert response.data.call.settings.limits.max_duration_seconds == 3600

    # raise the max duration to 2 hours
    response = call.update(
        settings_override=CallSettingsRequest(
            limits=LimitsSettingsRequest(
                max_duration_seconds=7200,
            ),
        )
    )
    assert response.data.call.settings.limits.max_duration_seconds == 7200

    # remove the max duration
    response = call.update(
        settings_override=CallSettingsRequest(
            limits=LimitsSettingsRequest(
                max_duration_seconds=0,
            ),
        )
    )
    assert response.data.call.settings.limits.max_duration_seconds == 0


def test_user_blocking(client: Stream, get_user):
    alice = get_user()
    bob = get_user()

    client.block_users(blocked_user_id=bob.id, user_id=alice.id)
    response = client.get_blocked_users(user_id=alice.id)
    assert len(response.data.blocks) == 1
    assert response.data.blocks[0].user_id == alice.id
    assert response.data.blocks[0].blocked_user_id == bob.id

    client.unblock_users(blocked_user_id=bob.id, user_id=alice.id)
    response = client.get_blocked_users(user_id=alice.id)
    assert len(response.data.blocks) == 0


def test_create_call_with_backstage_and_join_ahead_set(client: Stream, call: Call):
    user_id = str(uuid.uuid4())
    starts_at = datetime.now(timezone.utc) + timedelta(minutes=30)

    # create a call and set backstage and join ahead time to 5 minutes
    call = client.video.call("livestream", uuid.uuid4())
    response = call.get_or_create(
        data=CallRequest(
            starts_at=starts_at,
            created_by_id=user_id,
            settings_override=CallSettingsRequest(
                backstage=BackstageSettingsRequest(
                    enabled=True,
                    join_ahead_time_seconds=300,
                ),
            ),
        )
    )

    assert response.data.call.join_ahead_time_seconds == 300

    # raise the max duration to 10 minutes
    response = call.update(
        settings_override=CallSettingsRequest(
            backstage=BackstageSettingsRequest(
                join_ahead_time_seconds=600,
            ),
        )
    )
    assert response.data.call.join_ahead_time_seconds == 600

    # remove the max duration
    response = call.update(
        settings_override=CallSettingsRequest(
            backstage=BackstageSettingsRequest(
                join_ahead_time_seconds=0,
            ),
        )
    )
    assert response.data.call.join_ahead_time_seconds == 0


def test_create_call_with_custom_session_inactivity_timeout(call: Call):
    user_id = str(uuid.uuid4())

    # create a call and set its session inactivity timeout to 5 seconds
    response = call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
            settings_override=CallSettingsRequest(
                session=SessionSettingsRequest(
                    inactivity_timeout_seconds=5,
                ),
            ),
        )
    )

    assert response.data.call.settings.session.inactivity_timeout_seconds == 5


@pytest.mark.skip_in_ci
def test_create_call_type_with_custom_session_inactivity_timeout(client: Stream):
    # create a call type with a session inactivity timeout of 5 minutes
    response = client.video.create_call_type(
        name="long_inactivity_timeout_" + str(uuid.uuid4()),
        settings=CallSettingsRequest(
            session=SessionSettingsRequest(
                inactivity_timeout_seconds=300,
            ),
        ),
    )

    assert response.data.settings.session.inactivity_timeout_seconds == 300


def test_start_stop_frame_recording(client: Stream):
    user_id = str(uuid.uuid4())

    # create a call and set its frame recording settings
    call = client.video.call("default", uuid.uuid4())
    call.get_or_create(data=CallRequest(created_by_id=user_id))

    with pytest.raises(StreamAPIException) as e_info:
        call.start_recording()

    assert e_info.value.status_code == 400
    assert (
        e_info.value.api_error.message
        == 'StartRecording failed with error: "there is no active session"'
    )

    with pytest.raises(StreamAPIException) as e_info:
        call.stop_recording()

    assert e_info.value.status_code == 400
    assert (
        e_info.value.api_error.message
        == 'StopRecording failed with error: "call egress is not running"'
    )


def test_create_call_with_custom_frame_recording_settings(client: Stream):
    user_id = str(uuid.uuid4())

    # create a call and set its frame recording settings
    call = client.video.call("default", uuid.uuid4())
    response = call.get_or_create(
        data=CallRequest(
            created_by_id=user_id,
            settings_override=CallSettingsRequest(
                frame_recording=FrameRecordingSettingsRequest(
                    capture_interval_in_seconds=3, mode="auto-on", quality="1080p"
                ),
            ),
        )
    )

    assert response.data.call.settings.frame_recording.capture_interval_in_seconds == 3
    assert response.data.call.settings.frame_recording.mode == "auto-on"
    assert response.data.call.settings.frame_recording.quality == "1080p"


@pytest.mark.skip_in_ci
def test_create_call_type_with_custom_frame_recording_settings(client: Stream):
    # create a call type with frame recording settings
    response = client.video.create_call_type(
        name="frame_recording_" + str(uuid.uuid4()),
        settings=CallSettingsRequest(
            frame_recording=FrameRecordingSettingsRequest(
                capture_interval_in_seconds=5, mode="auto-on", quality="720p"
            ),
        ),
    )

    assert response.data.settings.frame_recording.capture_interval_in_seconds == 5
    assert response.data.settings.frame_recording.mode == "auto-on"
    assert response.data.settings.frame_recording.quality == "720p"


@pytest.mark.asyncio
async def test_connect_openai(client: Stream, capsys):
    # Get the OpenAI API key or skip the test
    openai_api_key = get_openai_api_key_or_skip()

    call = client.video.call("default", "example-ai-recorder")

    # Skip the actual connection part which requires a real server, we leave this here just for manual testing
    with capsys.disabled():
        try:
            async with (
                asyncio.timeout(5),
                call.connect_openai(openai_api_key, "lucy") as connection,
            ):
                await connection.session.update(
                    session={"instructions": "help the user with history questions"}
                )
                await connection.session.update(session={"voice": "ballad"})
                async for event in connection:
                    print(f"received event: {event}")
                    if event.type == "call.session_participant_left":
                        print("other user left, leaving the call now")
                        return
                    if event.type == "call.session_participant_joined":
                        await connection.conversation.item.create(
                            item={
                                "type": "message",
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_text",
                                        "text": "Say hello to Kazuki in Japanese",
                                    }
                                ],
                            }
                        )
                        await connection.response.create()
        except asyncio.TimeoutError:
            print("Test timed out after 5 seconds")


@pytest.mark.asyncio
async def test_event_representation():
    """Test that events have a nice string representation."""
    from getstream.video.openai import dict_to_class

    # Create a sample event dictionary
    event_dict = {
        "type": "response.audio_transcript.delta",
        "event_id": "event_B8X1q0WppJQ8J6PN7a555",
        "response_id": "resp_B8X1q71qHQbQlGd8eZ5RZ",
        "item_id": "item_B8X1qkjSfB5sn8lnhgJ5d",
        "content_index": 0,
        "output_index": 0,
        "delta": "。",
    }

    # Convert to a StreamEvent
    event = dict_to_class(event_dict)

    # Get the string representation
    event_str = str(event)
    print(f"\nEvent representation: {event_str}")

    # Verify that the representation includes the type in camel case
    assert "ResponseAudioTranscriptDeltaEvent" in event_str

    # Verify that the representation includes all the attributes
    for key, value in event_dict.items():
        assert f"{key}=" in event_str
        assert str(repr(value)) in event_str
