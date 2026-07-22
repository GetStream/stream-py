import logging

import httpx
import pytest

from getstream import AsyncStream, Stream
from getstream.logging_utils import redact_json_body, redact_query


def make_client(handler, caplog, **kwargs):
    logger = logging.getLogger("test.stream.logging")
    caplog.set_level(logging.DEBUG, logger="test.stream.logging")
    return Stream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(handler),
        logger=logger,
        **kwargs,
    )


def make_async_client(handler, caplog, **kwargs):
    logger = logging.getLogger("test.stream.logging.async")
    caplog.set_level(logging.DEBUG, logger="test.stream.logging.async")
    return AsyncStream(
        api_key="key",
        api_secret="secret",
        transport=httpx.MockTransport(handler),
        logger=logger,
        **kwargs,
    )


def ok(_request):
    return httpx.Response(200, json={"ok": True})


def records_named(caplog, name):
    return [r for r in caplog.records if r.getMessage() == name]


def test_client_initialized_once_with_schema(caplog):
    make_client(ok, caplog)
    inits = records_named(caplog, "client.initialized")
    assert len(inits) == 1
    r = inits[0]
    assert getattr(r, "stream.sdk.name", None) == "stream-py"
    assert hasattr(r, "stream.client.max_conns_per_host")
    assert getattr(r, "stream.client.log_bodies") is False


def test_sent_and_received_on_success(caplog):
    client = make_client(ok, caplog)
    client.get("/api/v2/app")
    assert len(records_named(caplog, "http.request.sent")) == 1
    received = records_named(caplog, "http.response.received")
    assert len(received) == 1
    assert getattr(received[0], "http.response.status_code") == 200
    assert hasattr(received[0], "duration_ms")


def test_error_status_is_received_not_failed(caplog):
    client = make_client(
        lambda _r: httpx.Response(500, json={"code": 1, "message": "boom"}), caplog
    )
    with pytest.raises(Exception):
        client.get("/api/v2/app")
    assert len(records_named(caplog, "http.response.received")) == 1
    assert not records_named(caplog, "http.request.failed")


def test_transport_failure_emits_failed(caplog):
    def boom(_request):
        raise httpx.ConnectError("reset")

    client = make_client(boom, caplog)
    with pytest.raises(Exception):
        client.get("/api/v2/app")
    failed = records_named(caplog, "http.request.failed")
    assert len(failed) == 1
    assert failed[0].levelno == logging.ERROR
    assert getattr(failed[0], "error.type") in {
        "connection_reset",
        "timeout",
        "dns_failure",
        "tls_handshake_failed",
        "unknown",
    }


def test_no_logger_no_output(caplog):
    caplog.set_level(logging.DEBUG)
    client = Stream(
        api_key="key", api_secret="secret", transport=httpx.MockTransport(ok)
    )
    client.get("/api/v2/app")
    assert not [r for r in caplog.records if r.name.startswith("test.")]


def test_query_redaction(caplog):
    client = make_client(ok, caplog)
    client.get("/api/v2/app", query_params={"api_key": "sekret", "user_id": "123"})
    sent = records_named(caplog, "http.request.sent")[0]
    q = str(getattr(sent, "url.query", ""))
    # Secret value redacted, non-secret param retained.
    assert "sekret" not in q
    assert "<redacted>" in q
    assert "123" in q


def test_log_bodies_opt_in_and_warn(caplog):
    client = make_client(ok, caplog, log_bodies=True)
    warns = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING and "bodies will be logged" in r.getMessage()
    ]
    assert len(warns) == 1
    # Secret value deliberately does not share a substring with its own key
    # name ("token"), otherwise "tok" (the value) would trivially still be
    # found in "token" (the key) even after correct redaction.
    client.post("/api/v2/x", json={"token": "shh12345", "keep": "v"})
    sent = records_named(caplog, "http.request.sent")[0]
    body = getattr(sent, "http.request.body", "")
    assert "shh12345" not in str(body)
    assert "keep" in str(body)


def test_redaction_helpers():
    assert redact_query({"api_key": "k", "q": "x"}) == {
        "api_key": "<redacted>",
        "q": "x",
    }
    out = redact_json_body(
        {"token": "t", "password": "p", "api_secret": "s", "keep": "v"}
    )
    assert out == {
        "token": "<redacted>",
        "password": "<redacted>",
        "api_secret": "<redacted>",
        "keep": "v",
    }
    assert redact_json_body("not json") == "not json"


@pytest.mark.asyncio
async def test_async_sent_and_received_on_success(caplog):
    client = make_async_client(ok, caplog)
    await client.get("/api/v2/app")
    assert len(records_named(caplog, "http.request.sent")) == 1
    received = records_named(caplog, "http.response.received")
    assert len(received) == 1
    assert getattr(received[0], "http.response.status_code") == 200
    assert hasattr(received[0], "duration_ms")
    await client.aclose()
