import pytest

from getstream import _rust


class TestClient:
    def test_empty_api_key_raises(self):
        with pytest.raises(_rust.ConfigError):
            _rust.Client("", "secret")

    def test_secret_and_token_raise(self):
        with pytest.raises(_rust.ConfigError):
            _rust.Client("key", "secret", token="token")

    def test_no_secret_and_no_token_raise(self):
        with pytest.raises(_rust.ConfigError):
            _rust.Client("key")

    def test_zero_call_event_capacity_raises(self):
        with pytest.raises(_rust.ConfigError):
            _rust.Client("key", "secret", call_event_capacity=0)

    def test_non_websocket_ws_url_raises(self):
        with pytest.raises(_rust.ConfigError):
            _rust.Client(
                "key", "secret", ws_url="https://video.stream-io-api.com/api/v2/connect"
            )
