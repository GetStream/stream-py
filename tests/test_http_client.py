import logging

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


# ── pool defaults ────────────────────────────────────────────────────


class TestSyncPoolDefaults:
    def test_default_limits_applied(self):
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        pool = client.client._transport._pool
        assert pool._max_connections == 5
        assert pool._max_keepalive_connections == 5
        assert pool._keepalive_expiry == 55.0

    def test_default_timeout_is_30s(self):
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        t = client.client.timeout
        assert t.connect == 10.0
        assert t.read == 30.0
        assert t.write == 30.0
        assert t.pool == 30.0


@pytest.mark.asyncio
class TestAsyncPoolDefaults:
    async def test_default_limits_applied(self):
        client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")
        pool = client.client._transport._pool
        assert pool._max_connections == 5
        assert pool._max_keepalive_connections == 5
        assert pool._keepalive_expiry == 55.0
        await client.aclose()

    async def test_default_timeout_is_30s(self):
        client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")
        t = client.client.timeout
        assert t.connect == 10.0
        assert t.read == 30.0
        assert t.write == 30.0
        assert t.pool == 30.0
        await client.aclose()


class TestSyncPoolOverrides:
    def _make(self, **kw):
        return Stream(api_key="k", api_secret="s", base_url="http://test", **kw)

    def test_max_conns_per_host_override(self):
        pool = self._make(max_conns_per_host=20).client._transport._pool
        assert pool._max_connections == 20
        assert pool._max_keepalive_connections == 20

    def test_idle_timeout_override(self):
        pool = self._make(idle_timeout=120.0).client._transport._pool
        assert pool._keepalive_expiry == 120.0

    def test_connect_timeout_override(self):
        assert self._make(connect_timeout=3.0).client.timeout.connect == 3.0

    def test_request_timeout_override(self):
        t = self._make(request_timeout=15.0).client.timeout
        assert t.read == 15.0 and t.write == 15.0 and t.pool == 15.0

    def test_legacy_timeout_alias_still_works(self):
        c = self._make(timeout=12.0)
        assert c.client.timeout.read == 12.0
        assert c.timeout == 12.0 and c.request_timeout == 12.0


@pytest.mark.asyncio
class TestAsyncPoolOverrides:
    async def _make(self, **kw):
        return AsyncStream(api_key="k", api_secret="s", base_url="http://test", **kw)

    async def test_max_conns_per_host_override(self):
        c = await self._make(max_conns_per_host=20)
        pool = c.client._transport._pool
        assert pool._max_connections == 20
        assert pool._max_keepalive_connections == 20
        await c.aclose()

    async def test_idle_timeout_override(self):
        c = await self._make(idle_timeout=120.0)
        assert c.client._transport._pool._keepalive_expiry == 120.0
        await c.aclose()

    async def test_connect_timeout_override(self):
        c = await self._make(connect_timeout=3.0)
        assert c.client.timeout.connect == 3.0
        await c.aclose()

    async def test_request_timeout_override(self):
        c = await self._make(request_timeout=15.0)
        t = c.client.timeout
        assert t.read == 15.0 and t.write == 15.0 and t.pool == 15.0
        await c.aclose()

    async def test_legacy_timeout_alias_still_works(self):
        c = await self._make(timeout=12.0)
        assert c.client.timeout.read == 12.0
        assert c.timeout == 12.0 and c.request_timeout == 12.0
        await c.aclose()


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


class TestSyncHttpClientEscapeHatchKnobs:
    def test_pool_knobs_ignored_when_http_client_provided(self):
        custom_limits = httpx.Limits(
            max_connections=99,
            max_keepalive_connections=99,
            keepalive_expiry=99.0,
        )
        custom = httpx.Client(transport=httpx.HTTPTransport(limits=custom_limits))
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            http_client=custom,
            max_conns_per_host=1,
            idle_timeout=1.0,
            connect_timeout=1.0,
            request_timeout=1.0,
        )
        assert client.client is custom
        pool = client.client._transport._pool
        assert pool._max_connections == 99
        assert pool._max_keepalive_connections == 99
        assert pool._keepalive_expiry == 99.0


@pytest.mark.asyncio
class TestAsyncHttpClientEscapeHatchKnobs:
    async def test_pool_knobs_ignored_when_http_client_provided(self):
        custom_limits = httpx.Limits(
            max_connections=99,
            max_keepalive_connections=99,
            keepalive_expiry=99.0,
        )
        custom = httpx.AsyncClient(
            transport=httpx.AsyncHTTPTransport(limits=custom_limits),
        )
        client = AsyncStream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            http_client=custom,
            max_conns_per_host=1,
            idle_timeout=1.0,
            connect_timeout=1.0,
            request_timeout=1.0,
        )
        assert client.client is custom
        pool = client.client._transport._pool
        assert pool._max_connections == 99
        assert pool._max_keepalive_connections == 99
        assert pool._keepalive_expiry == 99.0
        await client.aclose()


# ── INFO log on construction ─────────────────────────────────────────


class TestSyncInfoLog:
    def test_info_log_emitted_with_defaults(self, caplog):
        with caplog.at_level(logging.INFO, logger="getstream"):
            Stream(api_key="k", api_secret="s", base_url="http://test")
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        msg = infos[0].getMessage()
        assert "max_conns_per_host=5" in msg
        assert "idle_timeout=55.0s" in msg
        assert "connect_timeout=10.0s" in msg
        assert "request_timeout=30.0s" in msg
        assert "user_http_client=False" in msg

    def test_info_log_when_user_http_client_provided(self, caplog):
        custom = httpx.Client(transport=_mock_transport())
        with caplog.at_level(logging.INFO, logger="getstream"):
            Stream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                http_client=custom,
            )
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        assert "user_http_client=True" in infos[0].getMessage()


@pytest.mark.asyncio
class TestAsyncInfoLog:
    async def test_info_log_emitted_with_defaults(self, caplog):
        with caplog.at_level(logging.INFO, logger="getstream"):
            client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")
            await client.aclose()
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        assert "max_conns_per_host=5" in infos[0].getMessage()
        assert "user_http_client=False" in infos[0].getMessage()


# ── sync/async parity ────────────────────────────────────────────────


@pytest.mark.asyncio
class TestSyncAsyncParity:
    async def test_same_kwargs_produce_same_pool_config(self):
        kwargs = dict(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            max_conns_per_host=7,
            idle_timeout=42.0,
            connect_timeout=3.0,
            request_timeout=11.0,
        )
        sync_c = Stream(**kwargs)
        async_c = AsyncStream(**kwargs)

        sp = sync_c.client._transport._pool
        ap = async_c.client._transport._pool
        assert sp._max_connections == ap._max_connections == 7
        assert sp._max_keepalive_connections == ap._max_keepalive_connections == 7
        assert sp._keepalive_expiry == ap._keepalive_expiry == 42.0

        st = sync_c.client.timeout
        at = async_c.client.timeout
        assert st.connect == at.connect == 3.0
        assert st.read == at.read == 11.0
        assert st.write == at.write == 11.0
        assert st.pool == at.pool == 11.0

        sync_c.close()
        await async_c.aclose()


# ── per-call timeout override ────────────────────────────────────────


def _timeout_capture_transport():
    observed = {}

    def handler(request: httpx.Request) -> httpx.Response:
        observed["timeout"] = request.extensions.get("timeout")
        return httpx.Response(200, json={}, request=request)

    return httpx.MockTransport(handler), observed


class TestSyncPerCallTimeoutOverride:
    def test_per_call_timeout_reaches_httpx(self):
        transport, observed = _timeout_capture_transport()
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
            request_timeout=30.0,
        )
        client.get("/app", timeout=httpx.Timeout(2.5))
        assert observed["timeout"]["read"] == 2.5
        assert observed["timeout"]["connect"] == 2.5


@pytest.mark.asyncio
class TestAsyncPerCallTimeoutOverride:
    async def test_per_call_timeout_reaches_httpx(self):
        transport, observed = _timeout_capture_transport()
        client = AsyncStream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
            request_timeout=30.0,
        )
        await client.get("/app", timeout=httpx.Timeout(2.5))
        assert observed["timeout"]["read"] == 2.5
        assert observed["timeout"]["connect"] == 2.5
        await client.aclose()


# ── validation ───────────────────────────────────────────────────────


class TestResolvePoolKnobsExplicitZero:
    """`_resolve_pool_knobs` must use `is None`, not truthiness, so callers
    who deliberately pass `0` / `0.0` get their value back unchanged.
    Regression test for the falsy-fallback bug flagged in CHA-2956 review.
    """

    def test_explicit_zero_preserved(self):
        from getstream.base import _resolve_pool_knobs

        class Obj:
            max_conns_per_host = 0
            idle_timeout = 0.0
            connect_timeout = 0.0

        assert _resolve_pool_knobs(Obj()) == (0, 0.0, 0.0)

    def test_missing_attrs_fall_back_to_defaults(self):
        from getstream.base import (
            _resolve_pool_knobs,
            DEFAULT_MAX_CONNS_PER_HOST,
            DEFAULT_IDLE_TIMEOUT,
            DEFAULT_CONNECT_TIMEOUT,
        )

        class Obj:
            pass

        assert _resolve_pool_knobs(Obj()) == (
            DEFAULT_MAX_CONNS_PER_HOST,
            DEFAULT_IDLE_TIMEOUT,
            DEFAULT_CONNECT_TIMEOUT,
        )

    def test_none_attrs_fall_back_to_defaults(self):
        from getstream.base import (
            _resolve_pool_knobs,
            DEFAULT_MAX_CONNS_PER_HOST,
            DEFAULT_IDLE_TIMEOUT,
            DEFAULT_CONNECT_TIMEOUT,
        )

        class Obj:
            max_conns_per_host = None
            idle_timeout = None
            connect_timeout = None

        assert _resolve_pool_knobs(Obj()) == (
            DEFAULT_MAX_CONNS_PER_HOST,
            DEFAULT_IDLE_TIMEOUT,
            DEFAULT_CONNECT_TIMEOUT,
        )


class TestPoolConfigForwardedOnClone:
    """clone_for_token and as_async build fresh top-level clients; they must
    carry the source client's pool config, not silently revert to defaults.
    """

    def _make(self):
        return Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            max_conns_per_host=20,
            idle_timeout=120.0,
            connect_timeout=3.0,
            request_timeout=15.0,
        )

    def test_clone_for_token_preserves_pool_config(self):
        clone = self._make().clone_for_token("user-token")
        assert clone.max_conns_per_host == 20
        assert clone.idle_timeout == 120.0
        assert clone.connect_timeout == 3.0
        assert clone.request_timeout == 15.0
        pool = clone.client._transport._pool
        assert pool._max_connections == 20
        assert pool._keepalive_expiry == 120.0

    @pytest.mark.asyncio
    async def test_as_async_preserves_pool_config(self):
        sync_client = self._make()
        aclient = sync_client.as_async()
        assert aclient.max_conns_per_host == 20
        assert aclient.idle_timeout == 120.0
        assert aclient.connect_timeout == 3.0
        assert aclient.request_timeout == 15.0
        assert aclient.client._transport._pool._max_connections == 20
        await aclient.aclose()
        sync_client.close()


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
