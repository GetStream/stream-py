"""Tests for gzip request/response support (CHA-2964).

Server-Side SDK Gzip Spec, section 6.2 (stream-py):
- httpx does NOT auto-add ``Accept-Encoding``; the SDK must set it on the
  default client it constructs.
- httpx auto-decodes ``Content-Encoding: gzip`` responses transparently.
- Sync and async parity required.
- The escape hatch (user passing their own ``httpx.Client``/``httpx.AsyncClient``)
  MUST NOT be modified by the SDK — those tests live in ``test_http_client.py``.
"""

from __future__ import annotations

import gzip
import json

import httpx
import pytest

from getstream import AsyncStream, Stream


def _capture_transport():
    """A MockTransport that records every outgoing request and returns 200 {}."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={}, request=request)

    return httpx.MockTransport(handler), captured


def _gzip_response_transport(payload: dict):
    """A MockTransport that returns the given payload gzip-encoded.

    Sets ``Content-Encoding: gzip`` so httpx transparently decompresses on read.
    """
    body = gzip.compress(json.dumps(payload).encode("utf-8"))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=body,
            headers={
                "Content-Encoding": "gzip",
                "Content-Type": "application/json",
            },
            request=request,
        )

    return httpx.MockTransport(handler)


# ── Accept-Encoding request header ───────────────────────────────────


class TestAcceptEncodingHeaderSync:
    def test_sync_default_client_sends_accept_encoding_gzip(self):
        transport, captured = _capture_transport()
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
        )
        client.get_app()

        assert len(captured) == 1
        accept_encoding = captured[0].headers.get("accept-encoding", "")
        assert "gzip" in accept_encoding.lower(), (
            f"expected 'gzip' in Accept-Encoding, got {accept_encoding!r}"
        )


@pytest.mark.asyncio
class TestAcceptEncodingHeaderAsync:
    async def test_async_default_client_sends_accept_encoding_gzip(self):
        transport, captured = _capture_transport()
        client = AsyncStream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
        )
        await client.get_app()

        assert len(captured) == 1
        accept_encoding = captured[0].headers.get("accept-encoding", "")
        assert "gzip" in accept_encoding.lower(), (
            f"expected 'gzip' in Accept-Encoding, got {accept_encoding!r}"
        )


# ── Gzip response decoding (httpx transparently decompresses) ────────


class TestGzipResponseDecodingSync:
    def test_sync_client_decodes_gzip_response_body(self):
        expected = {"hello": "world", "n": 42}
        transport = _gzip_response_transport(expected)
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
        )

        # Use the underlying httpx client directly so the assertion targets
        # response decoding rather than any specific dataclass-json model.
        resp = client.client.get("/api/v2/app")
        assert resp.status_code == 200
        assert resp.json() == expected


@pytest.mark.asyncio
class TestGzipResponseDecodingAsync:
    async def test_async_client_decodes_gzip_response_body(self):
        expected = {"hello": "world", "n": 42}
        transport = _gzip_response_transport(expected)
        client = AsyncStream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            transport=transport,
        )

        resp = await client.client.get("/api/v2/app")
        assert resp.status_code == 200
        assert resp.json() == expected


# ── Escape hatch is NOT modified by the SDK (regression guard) ───────


class TestEscapeHatchUntouched:
    def test_sync_user_provided_clients_accept_encoding_is_not_overwritten(self):
        """When the user passes their own httpx.Client with an explicit
        Accept-Encoding, the SDK must not overwrite it. The user owns that
        client and its transport-level headers."""
        transport, captured = _capture_transport()
        # User explicitly opts out of gzip via identity encoding
        custom = httpx.Client(
            transport=transport,
            headers={"Accept-Encoding": "identity"},
        )
        client = Stream(
            api_key="k",
            api_secret="s",
            base_url="http://test",
            http_client=custom,
        )
        client.get_app()

        assert len(captured) == 1
        accept_encoding = captured[0].headers.get("accept-encoding", "")
        # The SDK must not have replaced the user's choice with 'gzip' only.
        assert accept_encoding.lower() == "identity", (
            f"SDK overwrote a user-provided client's Accept-Encoding; "
            f"got {accept_encoding!r}, expected 'identity'"
        )
