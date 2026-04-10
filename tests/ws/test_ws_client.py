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
