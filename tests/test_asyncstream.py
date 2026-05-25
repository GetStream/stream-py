import pytest

from getstream import AsyncStream


@pytest.fixture
async def user_token():
    stream = AsyncStream(api_key="k", api_secret="s")
    yield stream.create_token("alice")
    await stream.aclose()


@pytest.mark.asyncio
class TestAsyncStream:
    async def test_aclose_closes_main_client(self):
        client = AsyncStream(api_key="fake", api_secret="fake")

        assert client.client.is_closed is False
        await client.aclose()
        assert client.client.is_closed is True

    async def test_aclose_closes_video_client(self):
        client = AsyncStream(api_key="fake", api_secret="fake")
        _ = client.video  # trigger cached_property

        assert client.video.client.is_closed is False
        await client.aclose()
        assert client.video.client.is_closed is True

    async def test_aclose_closes_chat_client(self):
        client = AsyncStream(api_key="fake", api_secret="fake")
        _ = client.chat

        assert client.chat.client.is_closed is False
        await client.aclose()
        assert client.chat.client.is_closed is True

    async def test_aclose_closes_moderation_client(self):
        client = AsyncStream(api_key="fake", api_secret="fake")
        _ = client.moderation

        assert client.moderation.client.is_closed is False
        await client.aclose()
        assert client.moderation.client.is_closed is True

    async def test_aclose_without_child_clients(self):
        """aclose() should work even if video/chat were never accessed."""
        client = AsyncStream(api_key="fake", api_secret="fake")
        await client.aclose()
        assert client.client.is_closed is True

    async def test_subclients_use_token(self, user_token):
        async with AsyncStream(api_key="k", token=user_token) as client:
            assert client.chat.token == user_token
            assert client.video.token == user_token
            assert client.moderation.token == user_token

    async def test_async_accepts_token(self, user_token):
        async with AsyncStream(api_key="k", token=user_token) as client:
            assert client.token == user_token
            assert client.has_api_secret is False

    async def test_neither_secret_nor_token_raises(self, monkeypatch):
        monkeypatch.delenv("STREAM_API_KEY", raising=False)
        monkeypatch.delenv("STREAM_API_SECRET", raising=False)
        with pytest.raises(ValueError):
            AsyncStream(api_key="k")

    async def test_both_secret_and_token_raises(self, user_token):
        with pytest.raises(ValueError):
            AsyncStream(api_key="k", api_secret="s", token=user_token)

    async def test_empty_token_raises(self):
        with pytest.raises(ValueError):
            AsyncStream(api_key="k", token="")

    async def test_create_token_raises_without_secret(self, user_token):
        async with AsyncStream(api_key="k", token=user_token) as client:
            with pytest.raises(ValueError):
                client.create_token("bob")

    async def test_create_call_token_raises_without_secret(self, user_token):
        async with AsyncStream(api_key="k", token=user_token) as client:
            with pytest.raises(ValueError):
                client.create_call_token("bob", call_cids=["default:c1"])

    async def test_verify_signature_raises_without_secret(self, user_token):
        async with AsyncStream(api_key="k", token=user_token) as client:
            with pytest.raises(ValueError):
                client.verify_signature(b"body", "sig")

    async def test_custom_token_is_passed_to_http(self, user_token):
        # Safety net after refactoring of token handling in AsyncStream
        async with AsyncStream(api_key="k", token="123") as client:
            assert client.client.headers["Authorization"] == "123"
