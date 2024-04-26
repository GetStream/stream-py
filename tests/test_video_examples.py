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
