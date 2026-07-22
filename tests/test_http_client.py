import logging
import os

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


# ── sub-clients inherit the configured pool (default path) ───────────


class TestSubClientPoolPropagation:
    """Regression for CHA-2956 BLOCKER 1: on the DEFAULT path (no transport /
    no http_client) the sub-clients (video/chat/moderation/feeds) are what
    issue the real API calls, so their httpx pool must reflect the configured
    knobs — not the SDK defaults. They were silently falling back to 5/55
    because the intermediate generated REST clients don't forward the pool
    kwargs and ``stream`` was assigned after ``super().__init__()``.
    """

    KNOBS = dict(
        max_conns_per_host=99,
        idle_timeout=11.0,
        connect_timeout=3.0,
        request_timeout=7.0,
    )

    def _assert_pool(self, sub_client, parent_client):
        # Sub-clients share the parent's single configured client.
        assert sub_client.client is parent_client
        pool = sub_client.client._transport._pool
        assert pool._max_connections == 99
        assert pool._max_keepalive_connections == 99
        assert pool._keepalive_expiry == 11.0
        t = sub_client.client.timeout
        assert t.connect == 3.0
        assert t.read == 7.0

    def test_sync_sub_client_pools_match_configured_knobs(self):
        client = Stream(
            api_key="k", api_secret="s", base_url="http://test", **self.KNOBS
        )
        for name in ("video", "chat", "moderation", "feeds"):
            self._assert_pool(getattr(client, name), client.client)
        client.close()

    @pytest.mark.asyncio
    async def test_async_sub_client_pools_match_configured_knobs(self):
        client = AsyncStream(
            api_key="k", api_secret="s", base_url="http://test", **self.KNOBS
        )
        for name in ("video", "chat", "moderation"):
            self._assert_pool(getattr(client, name), client.client)
        await client.aclose()

    def test_sync_sub_client_pools_match_defaults(self):
        # Even with no explicit knobs, sub-clients must carry the SDK defaults
        # (5/55/10/30), not whatever a freshly-built sub-client would default to.
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        for name in ("video", "chat", "moderation", "feeds"):
            sub = getattr(client, name)
            assert sub.client is client.client
            pool = sub.client._transport._pool
            assert pool._max_connections == 5
            assert pool._keepalive_expiry == 55.0
            assert sub.client.timeout.connect == 10.0
            assert sub.client.timeout.read == 30.0
        client.close()


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

    def test_default_path_owns_and_shares_client(self):
        # On the default path (no transport/http_client) the top-level client
        # owns the single httpx client AND shares it with sub-clients, so the
        # resolved pool config reaches the clients that issue requests.
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        assert client._owns_http_client is True
        assert isinstance(client.client, httpx.Client)
        assert client._shared_client is client.client


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


# ── client.initialized event on construction (CHA-2957) ──────────────
# Formerly a plain-text "getstream connection pool: ..." INFO line
# (_log_pool_config); replaced by the structured client.initialized event.
# See tests/test_logging.py for the full logging-feature test suite.


class TestSyncInfoLog:
    def test_info_log_emitted_with_defaults(self, caplog):
        with caplog.at_level(logging.INFO, logger="getstream"):
            Stream(api_key="k", api_secret="s", base_url="http://test")
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        r = infos[0]
        assert r.getMessage() == "client.initialized"
        assert getattr(r, "stream.client.max_conns_per_host") == 5
        assert getattr(r, "stream.client.idle_timeout_seconds") == 55.0
        assert getattr(r, "stream.client.connect_timeout_seconds") == 10.0
        assert getattr(r, "stream.client.request_timeout_seconds") == 30.0
        assert getattr(r, "stream.client.user_http_client") is False

    def test_info_log_emitted_once_even_with_sub_clients(self, caplog):
        # Regression for CHA-2956 MINOR: the pool-config INFO line must fire
        # exactly once per Stream (at the top level), not once per sub-client.
        with caplog.at_level(logging.INFO, logger="getstream"):
            client = Stream(api_key="k", api_secret="s", base_url="http://test")
            _ = (client.video, client.chat, client.moderation, client.feeds)
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        client.close()

    def test_info_log_reflects_resolved_knobs(self, caplog):
        with caplog.at_level(logging.INFO, logger="getstream"):
            Stream(
                api_key="k",
                api_secret="s",
                base_url="http://test",
                max_conns_per_host=33,
                idle_timeout=12.0,
                connect_timeout=4.0,
                request_timeout=9.0,
            )
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        r = infos[0]
        assert getattr(r, "stream.client.max_conns_per_host") == 33
        assert getattr(r, "stream.client.idle_timeout_seconds") == 12.0
        assert getattr(r, "stream.client.connect_timeout_seconds") == 4.0
        assert getattr(r, "stream.client.request_timeout_seconds") == 9.0

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
        assert getattr(infos[0], "stream.client.user_http_client") is True
        assert getattr(infos[0], "stream.client.gzip_enabled") is False


@pytest.mark.asyncio
class TestAsyncInfoLog:
    async def test_info_log_emitted_with_defaults(self, caplog):
        with caplog.at_level(logging.INFO, logger="getstream"):
            client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")
            await client.aclose()
        infos = [r for r in caplog.records if r.name == "getstream"]
        assert len(infos) == 1
        assert getattr(infos[0], "stream.client.max_conns_per_host") == 5
        assert getattr(infos[0], "stream.client.user_http_client") is False


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

    @pytest.fixture
    def stream_client(self):
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            max_conns_per_host=20,
            idle_timeout=120.0,
            connect_timeout=3.0,
            request_timeout=15.0,
        )
        yield client
        client.close()

    def test_clone_for_token_preserves_pool_config(self, stream_client):
        clone = stream_client.clone_for_token("user-token")
        assert clone.max_conns_per_host == 20
        assert clone.idle_timeout == 120.0
        assert clone.connect_timeout == 3.0
        assert clone.request_timeout == 15.0
        pool = clone.client._transport._pool
        assert pool._max_connections == 20
        assert pool._keepalive_expiry == 120.0

    @pytest.mark.asyncio
    async def test_as_async_preserves_pool_config(self, stream_client):
        aclient = stream_client.as_async()
        assert aclient.max_conns_per_host == 20
        assert aclient.idle_timeout == 120.0
        assert aclient.connect_timeout == 3.0
        assert aclient.request_timeout == 15.0
        assert aclient.client._transport._pool._max_connections == 20
        await aclient.aclose()


class TestConstructsWithoutStreamEnv:
    """Regression for CHA-2956 BLOCKER 2: knob resolution must not require
    STREAM_API_KEY in the environment. Passing api_key/api_secret explicitly
    in a clean environment (no STREAM_* vars) must succeed and fall back to the
    spec defaults, instead of crashing inside ``Settings()`` (api_key is a
    required field).
    """

    @staticmethod
    def _clear_stream_env(monkeypatch):
        for key in list(os.environ):
            if key.startswith("STREAM_"):
                monkeypatch.delenv(key, raising=False)

    def test_sync_constructs_with_spec_defaults(self, monkeypatch):
        self._clear_stream_env(monkeypatch)
        client = Stream(api_key="k", api_secret="s", base_url="http://test")
        assert client.max_conns_per_host == 5
        assert client.idle_timeout == 55.0
        assert client.connect_timeout == 10.0
        assert client.request_timeout == 30.0
        pool = client.client._transport._pool
        assert pool._max_connections == 5
        assert pool._keepalive_expiry == 55.0
        client.close()

    @pytest.mark.asyncio
    async def test_async_constructs_with_spec_defaults(self, monkeypatch):
        self._clear_stream_env(monkeypatch)
        client = AsyncStream(api_key="k", api_secret="s", base_url="http://test")
        assert client.max_conns_per_host == 5
        assert client.idle_timeout == 55.0
        assert client.connect_timeout == 10.0
        assert client.request_timeout == 30.0
        await client.aclose()


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
