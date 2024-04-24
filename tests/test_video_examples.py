from getstream import Stream


def test_setup_client():
    from getstream import Stream

    client = Stream(api_key="your_api_key", api_secret="your_api_secret")
    assert isinstance(client, Stream)
    assert client.api_key == "your_api_key"
    assert client.api_secret == "your_api_secret"
    assert client.timeout == 6.0


def test_create_user(client: Stream):
    from getstream.models import UserRequest

    client.update_users(
        users={
            "tommaso-id": UserRequest(
                id="tommaso-id", name="tommaso", role="admin", custom={"country": "NL"}
            ),
            "thierry-id": UserRequest(
                id="thierry-id", name="thierry", role="admin", custom={"country": "US"}
            ),
        }
    )

    token = client.create_token("tommaso-id")
    assert token




def test_create_call(client: Stream):
    import uuid
    from getstream.models import (
        CallRequest,
        CallSettingsRequest,
        BroadcastSettingsRequest,
        HLSSettingsRequest,
    )

    call = client.video.call("default", uuid.uuid4())
    call.get_or_create(
        data=CallRequest(
            created_by_id="tommaso-id",
            settings_override=CallSettingsRequest(
                broadcasting=BroadcastSettingsRequest(
                    enabled=True,
                    hls=HLSSettingsRequest(
                        enabled=True,
                        quality_tracks=["480p", "720p", "1080p"],
                    ),
                ),
            ),
        ),
    )
