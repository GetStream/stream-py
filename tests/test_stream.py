import pytest

from getstream import Stream


@pytest.fixture
def user_token():
    return Stream(api_key="k", api_secret="s").create_token("alice")


class TestStream:
    def test_subclients_use_token(self, user_token):
        client = Stream(api_key="k", token=user_token)
        assert client.chat.token == user_token
        assert client.video.token == user_token
        assert client.moderation.token == user_token

    def test_sync_accepts_token(self, user_token):
        client = Stream(api_key="k", token=user_token)
        assert client.token == user_token
        assert client.has_api_secret is False

    def test_neither_secret_nor_token_raises(self, monkeypatch):
        monkeypatch.delenv("STREAM_API_KEY", raising=False)
        monkeypatch.delenv("STREAM_API_SECRET", raising=False)
        with pytest.raises(ValueError):
            Stream(api_key="k")

    def test_both_secret_and_token_raises(self, user_token):
        with pytest.raises(ValueError):
            Stream(api_key="k", api_secret="s", token=user_token)

    def test_empty_token_raises(self):
        with pytest.raises(ValueError):
            Stream(api_key="k", token="")

    def test_create_token_raises_without_secret(self, user_token):
        client = Stream(api_key="k", token=user_token)
        with pytest.raises(ValueError):
            client.create_token("bob")

    def test_create_call_token_raises_without_secret(self, user_token):
        client = Stream(api_key="k", token=user_token)
        with pytest.raises(ValueError):
            client.create_call_token("bob", call_cids=["default:c1"])

    def test_verify_signature_raises_without_secret(self, user_token):
        client = Stream(api_key="k", token=user_token)
        with pytest.raises(ValueError):
            client.verify_signature(b"body", "sig")

    def test_clone_for_token_forwards_runtime_config(self, user_token):
        client = Stream(
            api_key="k",
            api_secret="s",
            timeout=12.5,
            user_agent="ua/1.0",
        )
        clone = client.clone_for_token(user_token)
        assert clone.token == user_token
        assert clone.timeout == 12.5
        assert clone.user_agent == "ua/1.0"
        assert clone.api_key == client.api_key
        assert clone.base_url == client.base_url

    def test_clone_for_token_subclients_use_clone_token(self, user_token):
        client = Stream(api_key="k", api_secret="s")
        clone = client.clone_for_token(user_token)
        assert clone.chat.token == user_token
        assert clone.video.token == user_token
        assert clone.moderation.token == user_token
        assert clone.feeds.token == user_token
