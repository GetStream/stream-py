import pytest
from unittest.mock import AsyncMock, patch

from getstream.video.rtc.connection_utils import (
    connect_websocket,
    ConnectionOptions,
    SfuConnectionError,
    SfuJoinError,
    join_call_coordinator_request,
)
from getstream.video.rtc.signaling import SignalingError
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


@pytest.fixture
def mock_ws_client():
    """Patch WebSocketClient and yield the mock instance."""
    with patch("getstream.video.rtc.connection_utils.WebSocketClient") as mock_ws_cls:
        mock_ws = AsyncMock()
        mock_ws_cls.return_value = mock_ws
        yield mock_ws


@pytest.fixture
def coordinator_request():
    """Set up a mock coordinator client that captures the request body."""
    mock_call = AsyncMock()
    mock_call.call_type = "default"
    mock_call.id = "test_call"
    mock_call.client.stream.api_key = "key"
    mock_call.client.stream.api_secret = "secret"
    mock_call.client.stream.base_url = "https://test.url"

    captured_body = {}

    with patch("getstream.video.rtc.connection_utils.user_client") as mock_user_client:
        mock_client = AsyncMock()

        async def capture_post(*args, **kwargs):
            captured_body.update(kwargs.get("json", {}))
            return AsyncMock()

        mock_client.post = capture_post
        mock_user_client.return_value = mock_client
        yield mock_call, captured_body


class TestConnectWebsocket:
    @pytest.mark.asyncio
    async def test_raises_sfu_join_error_on_sfu_full(self, mock_ws_client):
        """connect_websocket should raise SfuJoinError when SFU is full."""
        sfu_error = models_pb2.Error(
            code=models_pb2.ERROR_CODE_SFU_FULL,
            message="server is full",
            should_retry=True,
        )
        mock_ws_client.connect = AsyncMock(
            side_effect=SignalingError(
                "Connection failed: server is full", error=sfu_error
            )
        )

        with pytest.raises(SfuJoinError) as exc_info:
            await connect_websocket(
                token="test_token",
                ws_url="wss://test.url",
                session_id="test_session",
                options=ConnectionOptions(),
            )

        assert exc_info.value.error_code == models_pb2.ERROR_CODE_SFU_FULL
        assert exc_info.value.should_retry is True
        assert isinstance(exc_info.value, SfuConnectionError)

    @pytest.mark.asyncio
    async def test_non_retryable_error_propagates_as_signaling_error(
        self, mock_ws_client
    ):
        """Non-retryable SignalingError should not become SfuJoinError."""
        sfu_error = models_pb2.Error(
            code=models_pb2.ERROR_CODE_PERMISSION_DENIED,
            message="permission denied",
            should_retry=False,
        )
        mock_ws_client.connect = AsyncMock(
            side_effect=SignalingError(
                "Connection failed: permission denied", error=sfu_error
            )
        )

        with pytest.raises(SignalingError) as exc_info:
            await connect_websocket(
                token="test_token",
                ws_url="wss://test.url",
                session_id="test_session",
                options=ConnectionOptions(),
            )

        assert not isinstance(exc_info.value, SfuJoinError)


class TestJoinCallCoordinatorRequest:
    @pytest.mark.asyncio
    async def test_includes_migrating_from_in_body(self, coordinator_request):
        """migrating_from and migrating_from_list should be included in the request body."""
        mock_call, captured_body = coordinator_request

        await join_call_coordinator_request(
            call=mock_call,
            user_id="user1",
            location="auto",
            migrating_from="sfu-london-1",
            migrating_from_list=["sfu-london-1", "sfu-paris-2"],
        )

        assert captured_body["migrating_from"] == "sfu-london-1"
        assert captured_body["migrating_from_list"] == ["sfu-london-1", "sfu-paris-2"]

    @pytest.mark.asyncio
    async def test_omits_migrating_from_when_not_provided(self, coordinator_request):
        """migrating_from should not appear in body when not provided."""
        mock_call, captured_body = coordinator_request

        await join_call_coordinator_request(
            call=mock_call,
            user_id="user1",
            location="auto",
        )

        assert "migrating_from" not in captured_body
        assert "migrating_from_list" not in captured_body
