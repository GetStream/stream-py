import pytest

from getstream import _rust


class TestClient:
    def test_empty_api_key_raises(self):
        with pytest.raises(_rust.RustError):
            _rust.Client("", "secret")

    def test_non_websocket_ws_url_raises(self):
        with pytest.raises(_rust.RustError, match="must use ws or wss"):
            _rust.Client(
                "key", "secret", ws_url="https://video.stream-io-api.com/api/v2/connect"
            )
