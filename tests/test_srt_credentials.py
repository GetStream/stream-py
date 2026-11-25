from datetime import datetime, timezone
from types import SimpleNamespace

import jwt
import pytest

from getstream import AsyncStream, Stream
from getstream.video import SRTCredentials

API_KEY = "srt-test-key"
API_SECRET = "srt-test-secret-that-is-at-least-32-bytes"


def srt_template(call_type: str, call_id: str) -> str:
    return (
        "srt://ingress.stream-io-video.com:10080?mode=caller&passphrase={passphrase}"
        f"&streamid={API_KEY}.{call_type}.{call_id}/{{token}}"
    )


def initialized_call(client, call_type="livestream", call_id="my-call"):
    call = client.video.call(call_type, call_id)
    # Only ingress.srt.address is read; a full CallResponse is not needed.
    call._data = SimpleNamespace(
        ingress=SimpleNamespace(
            srt=SimpleNamespace(address=srt_template(call_type, call_id))
        )
    )
    return call


def token_from(address: str) -> str:
    return address.split("streamid=", 1)[1].split("/", 1)[1]


@pytest.fixture
def client():
    return Stream(api_key=API_KEY, api_secret=API_SECRET)


class TestCreateSRTCredentials:
    def test_requires_initialized_call(self, client):
        with pytest.raises(TypeError, match="not initialized"):
            client.video.call("livestream", "my-call").create_srt_credentials("john")

    def test_call_scoped_token_expires_after_24_hours_by_default(self, client):
        credentials = initialized_call(client).create_srt_credentials("john")
        token = token_from(credentials.address)
        claims = jwt.decode(token, API_SECRET, algorithms=["HS256"])

        assert claims["user_id"] == "john"
        assert claims["scoped_call_cid"] == "livestream:my-call"
        assert "call_cids" not in claims
        # iat is backdated 5 seconds for clock skew.
        assert claims["exp"] - claims["iat"] == 24 * 60 * 60 + 5
        assert credentials.expires_at == datetime.fromtimestamp(
            claims["exp"], tz=timezone.utc
        )
        assert f"passphrase={token.split('.')[2]}&" in credentials.address

    def test_custom_expiration(self, client):
        credentials = initialized_call(client).create_srt_credentials(
            "john", expiration=3 * 60 * 60
        )
        claims = jwt.decode(
            token_from(credentials.address), API_SECRET, algorithms=["HS256"]
        )

        assert claims["exp"] - claims["iat"] == 3 * 60 * 60 + 5

    @pytest.mark.parametrize("expiration", [0, -1])
    def test_rejects_non_positive_expiration(self, client, expiration):
        with pytest.raises(ValueError, match="positive"):
            initialized_call(client).create_srt_credentials(
                "john", expiration=expiration
            )

    @pytest.mark.parametrize("expiration", [1.5, "3600", True])
    def test_rejects_non_int_expiration(self, client, expiration):
        with pytest.raises(TypeError, match="int"):
            initialized_call(client).create_srt_credentials(
                "john", expiration=expiration
            )

    def test_rejects_stream_id_over_srt_limit(self, client):
        call = initialized_call(client, call_id="c" * 200)

        with pytest.raises(ValueError, match="512-byte SRT limit"):
            call.create_srt_credentials("u" * 100)

    def test_repr_and_str_hide_the_address(self, client):
        credentials = initialized_call(client).create_srt_credentials("john")
        token = token_from(credentials.address)

        assert token not in repr(credentials)
        assert token not in str(credentials)
        assert "[redacted]" in repr(credentials)
        assert token in credentials.address

    def test_address_only_constructor_still_works(self):
        assert SRTCredentials(address="srt://x").expires_at is None

    def test_async_client(self):
        client = AsyncStream(api_key=API_KEY, api_secret=API_SECRET)
        credentials = initialized_call(client).create_srt_credentials("john")
        claims = jwt.decode(
            token_from(credentials.address), API_SECRET, algorithms=["HS256"]
        )

        assert claims["scoped_call_cid"] == "livestream:my-call"
