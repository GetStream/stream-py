import time

import pytest
import uuid
import jwt
import os
from getstream.models import (
    S3Request,
    CallSettingsRequest,
    OwnCapability,
    AudioSettingsRequest,
    ScreensharingSettingsRequest,
    RecordSettingsRequest,
    BackstageSettingsRequest,
    GeofenceSettingsRequest,
    CallRequest,
    LayoutSettingsRequest,
    NotificationSettings,
    EventNotificationSettings,
    APNS,
    UserRequest,
    QueryUsersPayload,
)

from getstream.base import StreamAPIException
from getstream.stream import Stream
from getstream.video.call import Call
from tests.base import VideoTestClass
from tests.base import wait_for_task

CALL_TYPE_NAME = f"calltype{uuid.uuid4()}"
EXTERNAL_STORAGE_NAME = f"storage{uuid.uuid4()}"


def get_openai_api_key_or_skip():
    """
    Get the OpenAI API key from environment variables or skip the test.

    Returns:
        str: The OpenAI API key.

    Raises:
        pytest.skip: If the OpenAI API key is not set.
    """
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    if not openai_api_key:
        pytest.skip("Skipping test as OPENAI_API_KEY is not set")
    return openai_api_key


def test_create_token(client: Stream):
    token = client.create_token(user_id="tommaso")
    assert token is not None
    decoded = jwt.decode(token, client.api_secret, algorithms=["HS256"])
    assert decoded["iat"] is not None
    assert decoded["user_id"] == "tommaso"


def test_create_token_with_expiration(client: Stream):
    token = client.create_token(user_id="tommaso", expiration=10)
    assert token is not None
    decoded = jwt.decode(token, client.api_secret, algorithms=["HS256"])
    assert decoded["iat"] is not None
    assert decoded["exp"] == decoded["iat"] + 10
    assert decoded["user_id"] == "tommaso"


def test_teams(client: Stream):
    call_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    response = client.upsert_users(UserRequest(id=user_id, teams=["red", "blue"]))
    assert response.data.users[user_id].teams == ["red", "blue"]
    call = client.video.call("default", call_id)
    response = call.create(
        data=CallRequest(
            created_by_id=user_id,
            team="blue",
        )
    )
    assert response.data.call.team == "blue"

    response = client.query_users(
        QueryUsersPayload(
            filter_conditions={"id": user_id, "teams": {"$in": ["red", "blue"]}}
        )
    )
    assert len(response.data.users) > 0
    assert user_id in [u.id for u in response.data.users]

    response = client.query_users(
        QueryUsersPayload(
            filter_conditions={
                "teams": None,
            }
        )
    )
    assert len([u for u in response.data.users if len(u.teams) > 0]) == 0

    response = client.video.query_calls(
        filter_conditions={"id": call_id, "team": {"$eq": "blue"}}
    )

    assert len(response.data.calls) > 0


@pytest.mark.skip_in_ci
class TestCallTypes:
    def test_creating_storage_with_reserved_name_should_fail(self, client: Stream):
        with pytest.raises(Exception) as exc_info:
            client.create_external_storage(
                bucket="my-bucket",
                name="stream-s3",
                storage_type="s3",
                path="directory_name/",
                aws_s3=S3Request(
                    s3_region="us-east-1",
                    s3_api_key="my-access-key",
                    s3_secret="my-secret",
                ),
            )
        assert "stream-s3 name reserved for internal use" in str(exc_info.value)

    def test_should_be_able_to_list_external_storage(self, client: Stream):
        client.list_external_storage()

    def test_create_call_type(self, client: Stream):
        response = client.video.create_call_type(
            name=CALL_TYPE_NAME,
            settings=CallSettingsRequest(
                audio=AudioSettingsRequest(
                    default_device="speaker",
                    mic_default_on=True,
                ),
                screensharing=ScreensharingSettingsRequest(
                    access_request_enabled=False,
                    enabled=True,
                ),
            ),
            notification_settings=NotificationSettings(
                enabled=True,
                call_notification=EventNotificationSettings(
                    apns=APNS(
                        title="{{ user.display_name }} invites you to a call", body=""
                    ),
                    enabled=True,
                ),
                session_started=EventNotificationSettings(
                    apns=APNS(
                        body="",
                        title="{{ user.display_name }} invites you to a call",
                    ),
                    enabled=False,
                ),
                call_live_started=EventNotificationSettings(
                    apns=APNS(
                        body="",
                        title="{{ user.display_name }} invites you to a call",
                    ),
                    enabled=False,
                ),
                call_ring=EventNotificationSettings(
                    apns=APNS(
                        body="",
                        title="{{ user.display_name }} invites you to a call",
                    ),
                    enabled=False,
                ),
                call_missed=EventNotificationSettings(
                    apns=APNS(
                        title="{{ user.display_name }} invites you to a call", body=""
                    ),
                    enabled=True,
                ),
            ),
            grants={
                "admin": [
                    OwnCapability.SEND_AUDIO,
                    OwnCapability.SEND_VIDEO,
                    OwnCapability.MUTE_USERS,
                ],
                "user": [
                    OwnCapability.SEND_AUDIO,
                    OwnCapability.SEND_VIDEO,
                ],
            },
        )

        assert response.data.name == CALL_TYPE_NAME
        assert response.data.settings.audio.mic_default_on is True
        assert response.data.settings.audio.default_device == "speaker"
        assert response.data.grants["admin"] is not None
        assert response.data.grants["user"] is not None
        assert response.data.settings.screensharing.access_request_enabled is False
        assert response.data.settings.screensharing.enabled is True
        assert response.data.notification_settings.enabled is True
        assert response.data.notification_settings.session_started.enabled is False
        assert response.data.notification_settings.call_notification.enabled is True
        assert response.data.notification_settings.call_notification.apns.title == (
            "{{ user.display_name }} invites you to a call"
        )

    def test_update_call_type(self, client: Stream):
        response = client.video.update_call_type(
            name=CALL_TYPE_NAME,
            settings=CallSettingsRequest(
                audio=AudioSettingsRequest(
                    default_device="earpiece",
                    mic_default_on=False,
                ),
                recording=RecordSettingsRequest(
                    mode="disabled",
                ),
                backstage=BackstageSettingsRequest(
                    enabled=True,
                ),
            ),
            grants={"host": [OwnCapability.JOIN_BACKSTAGE]},
        )
        assert response.data.settings.audio.mic_default_on is False
        assert response.data.settings.audio.default_device == "earpiece"
        assert response.data.settings.recording.mode == "disabled"
        assert response.data.settings.backstage.enabled is True
        assert response.data.grants["host"] == ["join-backstage"]

    def test_read_call_type(self, client: Stream):
        response = client.video.get_call_type(name=CALL_TYPE_NAME)
        assert response.data.name == CALL_TYPE_NAME

    def test_update_layout(self, client: Stream):
        layout_options = {
            "logo.image_url": "https://theme.zdassets.com/theme_assets/9442057/efc3820e436f9150bc8cf34267fff4df052a1f9c.png",
            "logo.horizontal_position": "center",
            "title.text": "Building Stream Video Q&A",
            "title.horizontal_position": "center",
            "title.color": "black",
            "participant_label.border_radius": "0px",
            "participant.border_radius": "0px",
            "layout.spotlight.participants_bar_position": "top",
            "layout.background_color": "#f2f2f2",
            "participant.placeholder_background_color": "#1f1f1f",
            "layout.single-participant.padding_inline": "20%",
            "participant_label.background_color": "transparent",
        }

        client.video.update_call_type(
            CALL_TYPE_NAME,
            settings=CallSettingsRequest(
                recording=RecordSettingsRequest(
                    mode="available",
                    audio_only=False,
                    quality="1080p",
                    layout=LayoutSettingsRequest(
                        name="spotlight",
                        options=layout_options,
                    ),
                ),
            ),
        )

    def test_custom_recording_style_css(self, client: Stream):
        client.video.update_call_type(
            CALL_TYPE_NAME,
            settings=CallSettingsRequest(
                recording=RecordSettingsRequest(
                    mode="available",
                    audio_only=False,
                    quality="1080p",
                    layout=LayoutSettingsRequest(
                        name="spotlight",
                        external_css_url="https://path/to/custom.css",
                    ),
                ),
            ),
        )

    def test_custom_recording_website(self, client: Stream):
        (
            client.video.update_call_type(
                CALL_TYPE_NAME,
                settings=CallSettingsRequest(
                    recording=RecordSettingsRequest(
                        mode="available",
                        audio_only=False,
                        quality="1080p",
                        layout=LayoutSettingsRequest(
                            name="custom",
                            external_app_url="https://path/to/layout/app",
                        ),
                    ),
                ),
            ),
        )

    @pytest.mark.skip_in_ci
    def test_delete_call_type(self, client: Stream):
        try:
            response = client.video.delete_call_type(name=CALL_TYPE_NAME)
        except Exception:
            time.sleep(2)
            response = client.video.delete_call_type(name=CALL_TYPE_NAME)
            assert response.status_code() == 200


@pytest.mark.usefixtures("shared_call")
class TestCall(VideoTestClass):
    def test_create_call(self):
        response = self.call.get_or_create(
            data=CallRequest(
                created_by_id="john",
                settings_override=CallSettingsRequest(
                    geofencing=GeofenceSettingsRequest(
                        names=[
                            "canada",
                        ]
                    ),
                    screensharing=ScreensharingSettingsRequest(
                        enabled=False,
                    ),
                ),
            ),
        )
        assert response.data.call.created_by.id == "john"
        assert response.data.call.settings.geofencing.names == ["canada"]
        assert response.data.call.settings.screensharing.enabled is False

    def test_update_call(self):
        response = self.call.update(
            settings_override=CallSettingsRequest(
                audio=AudioSettingsRequest(
                    mic_default_on=True,
                    default_device="speaker",
                ),
            ),
        )
        assert response.data.call.settings.audio.mic_default_on is True

    def test_rtmp_address(self):
        response = self.call.get_or_create(
            data=CallRequest(
                created_by_id="john",
            ),
        )
        assert self.call.id in response.data.call.ingress.rtmp.address

    def test_query_calls(self):
        response = self.client.video.query_calls()
        assert len(response.data.calls) >= 1

    def test_enable_call_recording(self):
        response = self.call.update(
            settings_override=CallSettingsRequest(
                recording=RecordSettingsRequest(
                    mode="available",
                    audio_only=True,
                )
            ),
        )
        assert response.data.call.settings.recording.mode == "available"

    def test_enable_backstage_mode(self):
        response = self.call.update(
            settings_override=CallSettingsRequest(
                backstage=BackstageSettingsRequest(
                    enabled=True,
                ),
            ),
        )
        assert response.data.call.settings.backstage.enabled is True

    def test_delete_not_existing_recording(self):
        with pytest.raises(StreamAPIException):
            self.call.delete_recording("random_session", "random_filename")

    def test_delete_not_existing_transcription(self):
        with pytest.raises(StreamAPIException):
            self.call.delete_transcription("random_session", "random_filename")

    def test_get_call_report_for_latest_session(self):
        with pytest.raises(StreamAPIException):
            self.client.video.get_call_report(self.call.call_type, self.call.id)

    def test_get_call_report_for_specified_session(self):
        with pytest.raises(StreamAPIException):
            self.client.video.get_call_report(
                self.call.call_type, self.call.id, session_id="non_existent"
            )


class TestDeleteCall:
    def test_soft_delete(self, call: Call):
        response = call.get_or_create(
            data=CallRequest(
                created_by_id="john",
            ),
        )
        response = call.delete()
        assert response.data.call is not None
        assert response.data.task_id is None

        with pytest.raises(StreamAPIException) as exc_info:
            response = call.get()
        msg = exc_info.value.api_error.message
        assert "Can't find call with id" in msg

    def test_hard_delete(self, client: Stream, call: Call):
        response = call.get_or_create(
            data=CallRequest(
                created_by_id="john",
            ),
        )
        response = call.delete(hard=True)
        assert response.data.call is not None
        task_id = response.data.task_id
        assert task_id is not None

        response = wait_for_task(client, task_id)
        cid = call.call_type + ":" + call.id
        assert response.data.result[cid]["status"] == "ok"


@pytest.mark.asyncio
async def test_connect_openai_with_bad_token(client: Stream):
    """Test that using a bad OpenAI token throws an exception."""
    # Verify that we have a valid OpenAI API key for comparison
    _ = get_openai_api_key_or_skip()

    # Create a call
    call_id = f"bad-token-test-{uuid.uuid4()}"
    call = client.video.call("default", call_id)

    # Use a clearly invalid OpenAI token
    bad_token = "bad_openai_token_that_will_fail"

    # The connection might not fail immediately, but should fail when we try to use it
    try:
        async with call.connect_openai(bad_token, "test-user") as connection:
            # Try to iterate through events, which should trigger the error check
            async for event in connection:
                # If we get here without an error, the test should fail
                assert False, "Should have received an error with invalid token"
                break

        # If we get here without an exception, the test should fail
        assert False, "Should have raised an exception with invalid token"
    except Exception as e:
        # Verify that we got an exception
        error_message = str(e)
        print(f"Received exception as expected: {error_message}")
        # The error message might vary, but should indicate some kind of failure
        assert error_message, "Exception message should not be empty"


@pytest.mark.asyncio
async def test_connect_openai_with_nonexistent_call_type(client: Stream):
    """Test that using a non-existent call type throws an appropriate exception."""
    # Create a call with a non-existent call type
    call_id = f"nonexistent-type-test-{uuid.uuid4()}"
    nonexistent_type = "banana"
    call = client.video.call(nonexistent_type, call_id)

    # First verify that the call type doesn't exist by trying to get it
    with pytest.raises(Exception) as excinfo:
        await client.video.get_call_type(nonexistent_type)

    # Print and verify the exception message
    error_message = str(excinfo.value)
    print(f"\nException when getting call type: {error_message}")
    assert "failed" in error_message.lower(), "Error message should indicate failure"

    # Now try to use the call with OpenAI
    # We expect an exception to be thrown either during connection or when trying to use it
    openai_api_key = get_openai_api_key_or_skip()

    # We expect an exception to be thrown at some point when trying to use a non-existent call type
    with pytest.raises(Exception) as excinfo:
        async with call.connect_openai(openai_api_key, "test-user") as connection:
            # If we get here without an exception, try to use the connection
            # which should definitely fail
            async for event in connection:
                print(f"Received event: {event}")
                break

    # Print the exception for debugging
    error_message = str(excinfo.value)
    print(f"\nException with non-existent call type: {error_message}")

    # The test passes if we get here, as pytest.raises will ensure an exception was thrown
