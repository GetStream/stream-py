import getstream_rtc
import pytest


class TestClient:
    def test_empty_api_key_raises(self):
        with pytest.raises(getstream_rtc.ConfigError):
            getstream_rtc.Client("", "secret")

    def test_secret_and_token_raise(self):
        with pytest.raises(getstream_rtc.ConfigError):
            getstream_rtc.Client("key", "secret", token="token")

    def test_no_secret_and_no_token_raise(self):
        with pytest.raises(getstream_rtc.ConfigError):
            getstream_rtc.Client("key")

    def test_zero_call_event_capacity_raises(self):
        with pytest.raises(getstream_rtc.ConfigError):
            getstream_rtc.Client("key", "secret", call_event_capacity=0)

    def test_non_websocket_ws_url_raises(self):
        with pytest.raises(getstream_rtc.ConfigError):
            getstream_rtc.Client(
                "key", "secret", ws_url="https://video.stream-io-api.com/api/v2/connect"
            )
