import time
import pytest
import os
import uuid
import jwt
from getstream.models.apns_request import Apnsrequest
from getstream.models.audio_settings_request import AudioSettingsRequest
from getstream.models.backstage_settings_request import BackstageSettingsRequest
from getstream.models.call_request import CallRequest
from getstream.models.call_settings_request import CallSettingsRequest
from getstream.models.event_notification_settings_request import (
    EventNotificationSettingsRequest,
)
from getstream.models.geofence_settings_request import GeofenceSettingsRequest

from getstream.models.notification_settings_request import NotificationSettingsRequest
from getstream.models.own_capability import OwnCapability
from getstream.models.record_settings_request import RecordSettingsRequest
from getstream.models.screensharing_settings_request import ScreensharingSettingsRequest
from getstream.sync.stream import Stream
from getstream.version import VERSION


VIDEO_API_KEY = os.environ.get("VIDEO_API_KEY")
BASE_URL = "https://video.stream-io-api.com/video"
VIDEO_API_SECRET = os.environ.get("VIDEO_API_SECRET")
TIMEOUT = 6

CALL_ID = str(uuid.uuid4())
CALL_TYPE = "default"


@pytest.fixture(scope="module")
def client():
    return Stream(
        api_key=VIDEO_API_KEY,
        api_secret=VIDEO_API_SECRET,
        timeout=TIMEOUT,
        video_base_url=BASE_URL,
    )


def test_video_client_initialization(client: Stream):
    assert client.api_key == VIDEO_API_KEY
    assert client.api_secret == VIDEO_API_SECRET
    assert client.video.base_url == BASE_URL
    assert client.video.timeout == TIMEOUT


def test_create_token(client: Stream):
    token = client.create_token()
    assert token is not None

    decoded = jwt.decode(token, VIDEO_API_SECRET, algorithms=["HS256"])
    assert decoded["iss"] == f"stream-video-python@{VERSION}"
    assert decoded["sub"] == "server-side"
    assert decoded["iat"] is not None


def test_create_call_type(client: Stream):
    response = client.video.create_call_type(
        name="example_calltype6",
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
        notification_settings=NotificationSettingsRequest(
            enabled=True,
            call_notification=EventNotificationSettingsRequest(
                apns=Apnsrequest(title="{{ user.display_name }} invites you to a call"),
                enabled=True,
            ),
            session_started=EventNotificationSettingsRequest(enabled=False),
        ),
        grants={
            "admin": [
                OwnCapability.SEND_AUDIO.to_str(),
                OwnCapability.SEND_VIDEO.to_str(),
                OwnCapability.MUTE_USERS.to_str(),
            ],
            "user": [
                OwnCapability.SEND_AUDIO.to_str(),
                OwnCapability.SEND_VIDEO.to_str(),
            ],
        },
    )

    assert response.data().name == "example_calltype6"
    assert response.data().settings.audio.mic_default_on is True
    assert response.data().settings.audio.default_device == "speaker"
    assert response.data().grants["admin"] is not None
    assert response.data().grants["user"] is not None
    assert response.data().settings.screensharing.access_request_enabled is False
    assert response.data().settings.screensharing.enabled is True
    assert response.data().notification_settings.enabled is True
    assert response.data().notification_settings.session_started.enabled is False
    assert response.data().notification_settings.call_notification.enabled is True
    assert response.data().notification_settings.call_notification.apns.title == (
        "{{ user.display_name }} invites you to a call"
    )


def test_read_call_type(client: Stream):
    response = client.video.get_call_type(name="example_calltype6")
    assert response.data().name == "example_calltype6"


def test_update_call_type(client: Stream):
    response = client.video.update_call_type(
        name="example_calltype6",
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
        grants={"host": [OwnCapability.JOIN_BACKSTAGE.to_str()]},
    )
    assert response.data().settings.audio.mic_default_on is False
    assert response.data().settings.audio.default_device == "earpiece"
    assert response.data().settings.recording.mode == "disabled"
    assert response.data().settings.backstage.enabled is True
    assert response.data().grants["host"] == ["join-backstage"]


def test_delete_call_type(client: Stream):
    try:
        response = client.video.delete_call_type(name="example_calltype6")
    except Exception:
        time.sleep(2)
        response = client.video.delete_call_type(name="example_calltype6")
    assert response.status_code() == 200


def test_create_call(client: Stream):
    response = client.video.get_or_create_call(
        type="default",
        id=CALL_ID,
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
    assert response.data().call.created_by.id == "john"
    assert response.data().call.settings.geofencing.names == ["canada"]
    assert response.data().call.settings.screensharing.enabled is False


def test_update_call(client: Stream):
    response = client.video.update_call(
        CALL_TYPE,
        CALL_ID,
        settings_override=CallSettingsRequest(
            audio=AudioSettingsRequest(
                mic_default_on=True,
                default_device="speaker",
            ),
        ),
    )
    assert response.data().call.settings.audio.mic_default_on is True


def test_rtmp_address(client: Stream):
    response = client.video.get_or_create_call(
        type="default",
        id=CALL_ID,
        data=CallRequest(
            created_by_id="john",
        ),
    )
    assert CALL_ID in response.data().call.ingress.rtmp.address


def test_query_calls(client: Stream):
    response = client.video.query_calls()
    assert len(response.data().calls) >= 1


def test_enable_call_recording(client: Stream):
    response = client.video.update_call(
        CALL_TYPE,
        CALL_ID,
        settings_override=CallSettingsRequest(
            recording=RecordSettingsRequest(
                mode="available",
            )
        ),
    )
    assert response.data().call.settings.recording.mode == "available"


# def test_start_recording(client: Stream):
#     response = client.video.start_recording(CALL_ID)
#     assert "recording" in response


# def test_stop_recording(client: Stream):
#     response = client.video.stop_recording(CALL_ID)
#     assert "recording" in response


# def test_query_recordings(client: Stream):
#     response = client.video.query_recordings(CALL_ID)
#     assert "recordings" in response


def test_enable_backstage_mode(client: Stream):
    response = client.video.update_call(
        CALL_TYPE,
        CALL_ID,
        settings_override=CallSettingsRequest(
            backstage=BackstageSettingsRequest(
                enabled=True,
            ),
        ),
    )
    assert response.data().call.settings.backstage.enabled is True


# def test_go_live(client: Stream):
#     response = client.video.go_live(CALL_ID)
#     assert response.data().call.egress.broadcasting is True


# def test_stop_live(client: Stream):
#     response = client.video.stop_live(CALL_ID)
#     assert response.data().call.egress.broadcasting is False
