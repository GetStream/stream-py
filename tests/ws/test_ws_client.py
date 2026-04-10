from getstream.ws import StreamWS


def test_stream_ws_instantiation():
    ws = StreamWS(
        api_key="test-key",
        api_secret="test-secret",
        user_id="alice",
    )
    assert ws.api_key == "test-key"
    assert ws.user_id == "alice"
    assert not ws.connected


def test_ws_url_construction():
    ws = StreamWS(
        api_key="my-key",
        api_secret="my-secret",
        user_id="alice",
        base_url="https://chat.stream-io-api.com",
    )
    url = ws.ws_url
    assert url.startswith("wss://chat.stream-io-api.com/connect?")
    assert "api_key=my-key" in url
    assert "stream-auth-type=jwt" in url


def test_ws_url_construction_http():
    ws = StreamWS(
        api_key="k",
        api_secret="s",
        user_id="bob",
        base_url="http://localhost:3030",
    )
    url = ws.ws_url
    assert url.startswith("ws://localhost:3030/connect?")
