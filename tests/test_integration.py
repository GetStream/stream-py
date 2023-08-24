import os
import uuid

import jwt
from getstream.models.model_audio_settings_request import AudioSettingsRequest
from getstream.models.model_backstage_settings_request import BackstageSettingsRequest
from getstream.models.model_broadcast_settings_request import BroadcastSettingsRequest
from getstream.models.model_call_request import CallRequest
from getstream.models.model_call_settings_request import CallSettingsRequest
from getstream.models.model_create_call_type_request import CreateCallTypeRequest
from getstream.models.model_member_request import MemberRequest
from getstream.models.model_record_settings_request import RecordSettingsRequest
from getstream.models.model_screensharing_settings_request import (
    ScreensharingSettingsRequest,
)
from getstream.models.model_target_resolution_request import TargetResolutionRequest
from getstream.models.model_transcription_settings_request import (
    TranscriptionSettingsRequest,
)
from getstream.models.model_update_call_type_request import UpdateCallTypeRequest
from getstream.models.model_video_settings_request import VideoSettingsRequest
from getstream.version import VERSION
import pytest
from getstream import Stream

VIDEO_API_KEY = os.environ.get("VIDEO_API_KEY")
BASE_URL = "https://video.stream-io-api.com/video"
VIDEO_API_SECRET = os.environ.get("VIDEO_API_SECRET")
TIMEOUT = 6

CALL_ID = str(uuid.uuid4())


def create_call_type_data() -> CreateCallTypeRequest:
    return CreateCallTypeRequest(
        name="example_calltype3",
        settings=CallSettingsRequest(
            audio=AudioSettingsRequest(
                default_device="speaker",
                access_request_enabled=True,
                opus_dtx_enabled=True,
            ),
            recording=RecordSettingsRequest(
                audio_only=True,
                mode="available",
                quality="audio-only",
            ),
            backstage=BackstageSettingsRequest(
                enabled=True,
            ),
            broadcasting=BroadcastSettingsRequest(
                enabled=True,
                hls=CallSettingsRequest(
                    auto_on=True,
                    enabled=True,
                    quality_tracks=[
                        "audio-only",
                        "360p",
                        "480p",
                        "720p",
                        "1080p",
                        "1440p",
                    ],
                ),
            ),
            screensharing=ScreensharingSettingsRequest(
                access_request_enabled=True,
                enabled=True,
            ),
            transcription=TranscriptionSettingsRequest(
                closed_caption_mode="available",
                mode="available",
            ),
            video=VideoSettingsRequest(
                access_request_enabled=True,
                enabled=True,
                camera_facing="front",
                target_resolution=TargetResolutionRequest(
                    bitrate=240,
                    height=240,
                    width=1000,
                ),
            ),
        ),
    )


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


def test_create_call_type(client: Stream):
    data = create_call_type_data()
    response = client.video.create_call_type(data)
    print(response)
    assert response.data().name == "example_calltype3"
    # assert "settings" in response


def test_update_call_type(client: Stream):
    name = "example_calltype3"
    updated_data = UpdateCallTypeRequest(
        settings=CallSettingsRequest(
            audio=AudioSettingsRequest(
                default_device="speaker",
                access_request_enabled=False,
            ),
            recording=RecordSettingsRequest(
                audio_only=False,
            ),
        ),
    )
    response = client.video.update_call_type(name, updated_data)

    assert response.data().settings.audio.access_request_enabled is False
    assert response.data().settings.recording.audio_only is False


def test_get_call_type(client: Stream):
    name = "example_calltype3"
    response = client.video.get_call_type(name)

    assert response.data().name == "example_calltype3"


def test_list_call_types(client: Stream):
    response = client.video.list_call_types()
    keys = response.data().call_types.keys()
    assert "example_calltype3" in keys


def test_delete_call_type(client: Stream):
    response = client.video.delete_call_type("example_calltype3")
    assert response.status_code == 200


def test_create_token(client: Stream):
    token = client.create_token()
    assert token is not None

    decoded = jwt.decode(token, VIDEO_API_SECRET, algorithms=["HS256"])
    assert decoded["iss"] == f"stream-video-python@{VERSION}"
    assert decoded["sub"] == "server-side"
    assert decoded["iat"] is not None


def test_get_or_create_call(client: Stream):
    calltype_name = "default"

    data = CallRequest(
        created_by_id="sacha@getstream.io",
        settings_override=CallSettingsRequest(
            audio=AudioSettingsRequest(
                default_device="speaker",
                access_request_enabled=False,
            ),
        ),
    )

    members = [MemberRequest(role="speaker", user_id="sacha@getstream.io")]
    response = client.video.get_or_create_call(
        call_type=calltype_name, call_id=CALL_ID, data=data, members=members
    )

    assert response.data().call.settings.audio.access_request_enabled is False
    assert response.data().call.settings.recording.audio_only is False


# def test_start_broadcasting(client):
#     call_type = "default"
#     response = client.video.start_broadcasting(call_id=CALL_ID, call_type=call_type)
#     assert "duration" in response


# def test_stop_broadcasting(client):
#     call_type = "default"
#     response = client.video.stop_broadcasting(call_id=CALL_ID, call_type=call_type)
#     assert "duration" in response
