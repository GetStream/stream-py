import httpx
import pytest

from getstream import Stream, AsyncStream


def _mock_transport(status=200, body=None):
    body = body or {}

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=body, request=request)

    return httpx.MockTransport(handler)


def _capture_transport():
    captured = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={}, request=request)

    return httpx.MockTransport(handler), captured


# ── transport (primary API) ──────────────────────────────────────────


class TestSyncTransport:
    def test_transport_used_for_requests(self):
        transport, captured = _capture_transport()
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        client.get_app()
        assert len(captured) == 1

    def test_stream_headers_applied(self):
        transport, captured = _capture_transport()
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        client.get_app()

        req = captured[0]
        assert "authorization" in req.headers
        assert req.headers["stream-auth-type"] == "jwt"
        assert "x-stream-client" in req.headers
        assert req.url.params["api_key"] == "k"

    def test_sub_clients_share_client(self):
        transport = _mock_transport()
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        shared = client.client
        assert client.video.client is shared
        assert client.chat.client is shared
        assert client.moderation.client is shared
        assert client.feeds.client is shared

    def test_close_closes_sdk_built_client(self):
        transport = _mock_transport()
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        inner = client.client
        client.close()
        assert inner.is_closed

    def test_sub_client_close_is_noop(self):
        transport = _mock_transport()
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        client.video.close()
        assert not client.client.is_closed

    def test_custom_limits_propagated(self):
        limits = httpx.Limits(max_connections=42, max_keepalive_connections=10)
        transport = httpx.HTTPTransport(limits=limits)
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        pool = client.client._transport._pool
        assert pool._max_connections == 42
        assert pool._max_keepalive_connections == 10

    def test_default_path_unchanged(self):
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        assert client._owns_http_client is True
        assert isinstance(client.client, httpx.Client)
        assert client._shared_client is None


@pytest.mark.asyncio
class TestAsyncTransport:
    async def test_transport_used_for_requests(self):
        transport, captured = _capture_transport()
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        await client.get_app()
        assert len(captured) == 1

    async def test_sub_clients_share_client(self):
        transport = _mock_transport()
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        shared = client.client
        assert client.video.client is shared
        assert client.chat.client is shared
        assert client.moderation.client is shared

    async def test_aclose_closes_sdk_built_client(self):
        transport = _mock_transport()
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", transport=transport
        )
        inner = client.client
        await client.aclose()
        assert inner.is_closed


# ── http_client (escape hatch) ───────────────────────────────────────


class TestSyncHttpClientEscapeHatch:
    def test_custom_http_client_is_used(self):
        transport, captured = _capture_transport()
        custom = httpx.Client(transport=transport)

        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        assert client.client is custom
        client.get_app()
        assert len(captured) == 1

    def test_sub_clients_share_custom_http_client(self):
        custom = httpx.Client(transport=_mock_transport())
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        assert client.video.client is custom
        assert client.chat.client is custom

    def test_close_does_not_close_user_provided_client(self):
        custom = httpx.Client(transport=_mock_transport())
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        client.close()
        assert not custom.is_closed

    def test_user_headers_preserved(self):
        transport, captured = _capture_transport()
        custom = httpx.Client(transport=transport, headers={"X-Custom": "val"})
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        client.get_app()

        req = captured[0]
        assert req.headers["x-custom"] == "val"
        assert "authorization" in req.headers


@pytest.mark.asyncio
class TestAsyncHttpClientEscapeHatch:
    async def test_custom_async_client_is_used(self):
        transport = _mock_transport()
        custom = httpx.AsyncClient(transport=transport)
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        assert client.client is custom

    async def test_aclose_does_not_close_user_provided_client(self):
        custom = httpx.AsyncClient(transport=_mock_transport())
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", http_client=custom
        )
        await client.aclose()
        assert not custom.is_closed


# ── validation ───────────────────────────────────────────────────────


class TestValidation:
    def test_transport_and_http_client_mutually_exclusive(self):
        with pytest.raises(ValueError, match="Cannot specify both"):
            Stream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                transport=_mock_transport(),
                http_client=httpx.Client(),
            )

    def test_wrong_type_raises_type_error(self):
        with pytest.raises(TypeError, match="httpx.Client"):
            Stream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                http_client="not-a-client",
            )

    def test_async_client_on_sync_raises_type_error(self):
        with pytest.raises(TypeError, match="httpx.Client"):
            Stream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                http_client=httpx.AsyncClient(),
            )

    def test_sync_client_on_async_raises_type_error(self):
        with pytest.raises(TypeError, match="httpx.AsyncClient"):
            AsyncStream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                http_client=httpx.Client(),
            )
