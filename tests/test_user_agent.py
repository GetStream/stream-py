import httpx
import pytest

from getstream import Stream, AsyncStream
from getstream.version import VERSION


def _mock_transport_capture_headers(captured):
    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(dict(request.headers))
        return httpx.Response(200, json={}, request=request)

    return httpx.MockTransport(handler)


def _get_header_case_insensitive(headers_map: dict, name: str):
    for k, v in headers_map.items():
        if k.lower() == name.lower():
            return v
    return None


def _attach_httpx_clients_sync(
    stream_client: Stream, captured_common, video_client, captured_video
):
    stream_client.client = httpx.Client(
        base_url=stream_client.base_url,
        headers=stream_client.headers,
        transport=_mock_transport_capture_headers(captured_common),
    )
    video_client.client = httpx.Client(
        base_url=video_client.base_url,
        headers=video_client.headers,
        transport=_mock_transport_capture_headers(captured_video),
    )


def _attach_httpx_clients_async(
    stream_client: AsyncStream, captured_common, video_client, captured_video
):
    stream_client.client = httpx.AsyncClient(
        base_url=stream_client.base_url,
        headers=stream_client.headers,
        transport=_mock_transport_capture_headers(captured_common),
    )
    video_client.client = httpx.AsyncClient(
        base_url=video_client.base_url,
        headers=video_client.headers,
        transport=_mock_transport_capture_headers(captured_video),
    )


def _exercise_sync(stream_client: Stream, video_client):
    stream_client.get_app()
    video_client.get_active_calls_status()


async def _exercise_async(stream_client: AsyncStream, video_client):
    await stream_client.get_app()
    await video_client.get_active_calls_status()


def test_user_agent_sync_common_and_video_default():
    captured_common = []
    captured_video = []
    ua_expected = f"stream-python-client-{VERSION}"

    client = Stream(api_key="k", api_secret="s", base_url="http://test")

    # Inject mock transports and exercise requests
    video = client.video
    _attach_httpx_clients_sync(client, captured_common, video, captured_video)
    _exercise_sync(client, video)

    assert captured_common, "no common request captured"
    assert captured_video, "no video request captured"
    assert (
        _get_header_case_insensitive(captured_common[-1], "X-Stream-Client")
        == ua_expected
    )
    assert (
        _get_header_case_insensitive(captured_video[-1], "X-Stream-Client")
        == ua_expected
    )


def test_user_agent_sync_common_and_video_custom():
    captured_common = []
    captured_video = []
    ua_custom = "my-app/9.9"

    client = Stream(
        api_key="k", api_secret="s", base_url="http://test", user_agent=ua_custom
    )

    video = client.video
    _attach_httpx_clients_sync(client, captured_common, video, captured_video)
    _exercise_sync(client, video)

    assert (
        _get_header_case_insensitive(captured_common[-1], "X-Stream-Client")
        == ua_custom
    )
    assert (
        _get_header_case_insensitive(captured_video[-1], "X-Stream-Client") == ua_custom
    )


@pytest.mark.asyncio
async def test_user_agent_async_common_and_video_default():
    captured_common = []
    captured_video = []
    ua_expected = f"stream-python-client-{VERSION}"

    client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")

    video = client.video
    _attach_httpx_clients_async(client, captured_common, video, captured_video)
    await _exercise_async(client, video)

    assert captured_common, "no async common request captured"
    assert captured_video, "no async video request captured"
    assert (
        _get_header_case_insensitive(captured_common[-1], "X-Stream-Client")
        == ua_expected
    )
    assert (
        _get_header_case_insensitive(captured_video[-1], "X-Stream-Client")
        == ua_expected
    )


@pytest.mark.asyncio
async def test_user_agent_async_common_and_video_custom():
    captured_common = []
    captured_video = []
    ua_custom = "my-app/9.9"

    client = AsyncStream(
        api_key="k", api_secret="s", base_url="http://test", user_agent=ua_custom
    )

    video = client.video
    _attach_httpx_clients_async(client, captured_common, video, captured_video)
    await _exercise_async(client, video)

    assert (
        _get_header_case_insensitive(captured_common[-1], "X-Stream-Client")
        == ua_custom
    )
    assert (
        _get_header_case_insensitive(captured_video[-1], "X-Stream-Client") == ua_custom
    )
