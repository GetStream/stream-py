import pytest

from getstream import AsyncStream


@pytest.mark.asyncio
class TestAsyncStreamClose:
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
