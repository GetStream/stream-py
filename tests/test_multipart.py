"""The generated upload methods send multipart/form-data: the file path becomes
the file part, other fields become JSON form values."""

from __future__ import annotations

import httpx
import pytest

from getstream import AsyncStream, Stream
from getstream.models import ImageSize, OnlyUserID


def _capture_transport():
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(
            201, json={"file": "https://cdn/x.png", "duration": "1ms"}, request=request
        )

    return httpx.MockTransport(handler), captured


def _assert_image_form(request: httpx.Request, file_name: str):
    assert request.headers["content-type"].startswith("multipart/form-data")
    body = request.read()
    assert f'name="file"; filename="{file_name}"'.encode() in body
    assert b"image-bytes" in body
    assert b'name="user"\r\n\r\n{"id": "jane"}\r\n' in body
    assert b'name="upload_sizes"\r\n\r\n[{"height": 20, "width": 10}]\r\n' in body


@pytest.fixture
def image(tmp_path):
    path = tmp_path / "f.png"
    path.write_bytes(b"image-bytes")
    return path


def test_upload_channel_image_sends_multipart(image):
    transport, captured = _capture_transport()
    client = Stream(
        api_key="k", api_secret="s", base_url="http://test", transport=transport
    )

    client.chat.upload_channel_image(
        channel_type="messaging",
        id="general",
        file=str(image),
        upload_sizes=[ImageSize(width=10, height=20)],
        user=OnlyUserID(id="jane"),
    )

    assert len(captured) == 1
    assert captured[0].url.path == "/api/v2/chat/channels/messaging/general/image"
    _assert_image_form(captured[0], image.name)


def test_upload_channel_file_sends_multipart(image):
    transport, captured = _capture_transport()
    client = Stream(
        api_key="k", api_secret="s", base_url="http://test", transport=transport
    )

    client.chat.upload_channel_file(
        "messaging", "general", file=str(image), user=OnlyUserID(id="jane")
    )

    body = captured[0].read()
    assert captured[0].headers["content-type"].startswith("multipart/form-data")
    assert b'name="user"\r\n\r\n{"id": "jane"}\r\n' in body
    assert b"image-bytes" in body


@pytest.mark.asyncio
async def test_async_upload_image_sends_multipart(image):
    transport, captured = _capture_transport()
    client = AsyncStream(
        api_key="k", api_secret="s", base_url="http://test", transport=transport
    )

    await client.upload_image(
        file=str(image),
        upload_sizes=[ImageSize(width=10, height=20)],
        user=OnlyUserID(id="jane"),
    )

    assert captured[0].url.path == "/api/v2/uploads/image"
    _assert_image_form(captured[0], image.name)
