import time
import pytest
import uuid
import jwt
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
)

from getstream.stream import Stream
from getstream.video.call import Call

CALL_TYPE_NAME = f"calltype{uuid.uuid4()}"
EXTERNAL_STORAGE_NAME = f"storage{uuid.uuid4()}"


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


class TestExternalStorage:
    def test_creating_storage_with_reserved_name_should_fail(self, client: Stream):
        with pytest.raises(Exception) as exc_info:
            client.video.create_external_storage(
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
        client.video.list_external_storage()


class TestCallTypes:
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

    def test_delete_call_type(self, client: Stream):
        try:
            response = client.video.delete_call_type(name=CALL_TYPE_NAME)
        except Exception:
            time.sleep(2)
            response = client.video.delete_call_type(name=CALL_TYPE_NAME)
            assert response.status_code() == 200


class TestCalls:
    def test_create_call(self, call: Call):
        response = call.get_or_create(
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

    def test_update_call(self, call: Call):
        response = call.update(
            settings_override=CallSettingsRequest(
                audio=AudioSettingsRequest(
                    mic_default_on=True,
                    default_device="speaker",
                ),
            ),
        )
        assert response.data.call.settings.audio.mic_default_on is True

    def test_rtmp_address(self, call: Call):
        response = call.get_or_create(
            data=CallRequest(
                created_by_id="john",
            ),
        )
        assert call.id in response.data.call.ingress.rtmp.address

    def test_query_calls(self, client: Stream):
        response = client.video.query_calls()
        assert len(response.data.calls) >= 1

    def test_enable_call_recording(self, call: Call):
        response = call.update(
            settings_override=CallSettingsRequest(
                recording=RecordSettingsRequest(
                    mode="available",
                )
            ),
        )
        assert response.data.call.settings.recording.mode == "available"

    def test_enable_backstage_mode(self, call: Call):
        response = call.update(
            settings_override=CallSettingsRequest(
                backstage=BackstageSettingsRequest(
                    enabled=True,
                ),
            ),
        )
        assert response.data.call.settings.backstage.enabled is True
