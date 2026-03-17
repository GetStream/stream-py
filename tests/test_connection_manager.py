import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.rtc.connection_utils import SfuJoinError, SfuConnectionError
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


async def _instant_backoff(max_retries, base=1.0, factor=2.0, sleep=False):
    """exp_backoff replacement that never sleeps."""
    for attempt in range(max_retries):
        yield base * (factor**attempt)


@pytest.fixture
def connection_manager(request):
    """Create a ConnectionManager with mocked heavy dependencies.

    Accepts max_join_retries via indirect parametrize, defaults to 3.
    """
    max_join_retries = getattr(request, "param", 3)
    with (
        patch("getstream.video.rtc.connection_manager.PeerConnectionManager"),
        patch("getstream.video.rtc.connection_manager.NetworkMonitor"),
        patch("getstream.video.rtc.connection_manager.ReconnectionManager"),
        patch("getstream.video.rtc.connection_manager.RecordingManager"),
        patch("getstream.video.rtc.connection_manager.SubscriptionManager"),
        patch("getstream.video.rtc.connection_manager.ParticipantsState"),
        patch("getstream.video.rtc.connection_manager.Tracer"),
        patch("getstream.video.rtc.connection_manager.exp_backoff", _instant_backoff),
    ):
        mock_call = MagicMock()
        mock_call.call_type = "default"
        mock_call.id = "test_call"
        cm = ConnectionManager(
            call=mock_call, user_id="user1", max_join_retries=max_join_retries
        )
        cm._connect_coordinator_ws = AsyncMock()
        yield cm


class TestConnectRetry:
    """Tests for connect() retry logic when SFU is full."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("connection_manager", [2], indirect=True)
    async def test_retries_on_sfu_join_error_and_passes_failed_sfus(
        self, connection_manager
    ):
        """When SFU is full, connect() should retry with migrating_from_list."""
        cm = connection_manager
        call_count = 0
        received_migrating_from_list = []

        async def mock_connect_internal(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            received_migrating_from_list.append(
                list(migrating_from_list) if migrating_from_list else None
            )

            if call_count <= 2:
                mock_join_response = MagicMock()
                mock_join_response.credentials.server.edge_name = (
                    f"sfu-node-{call_count}"
                )
                cm.join_response = mock_join_response
                raise SfuJoinError(
                    "server is full",
                    error_code=models_pb2.ERROR_CODE_SFU_FULL,
                    should_retry=True,
                )
            cm.running = True

        cm._connect_internal = mock_connect_internal

        await cm.connect()

        assert call_count == 3
        assert received_migrating_from_list[0] is None
        assert received_migrating_from_list[1] == ["sfu-node-1"]
        assert received_migrating_from_list[2] == ["sfu-node-1", "sfu-node-2"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("connection_manager", [1], indirect=True)
    async def test_raises_after_all_retries_exhausted(self, connection_manager):
        """When all retries are exhausted, connect() should raise SfuJoinError."""
        cm = connection_manager

        async def always_fail(migrating_from_list=None, **kwargs):
            mock_join_response = MagicMock()
            mock_join_response.credentials.server.edge_name = "sfu-node-1"
            cm.join_response = mock_join_response
            raise SfuJoinError(
                "server is full",
                error_code=models_pb2.ERROR_CODE_SFU_FULL,
                should_retry=True,
            )

        cm._connect_internal = always_fail

        with pytest.raises(SfuJoinError):
            await cm.connect()

    @pytest.mark.asyncio
    async def test_non_retryable_error_propagates_immediately(self, connection_manager):
        """Non-retryable errors should not trigger retry."""
        cm = connection_manager
        call_count = 0

        async def fail_with_generic_error(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            raise SfuConnectionError("something went wrong")

        cm._connect_internal = fail_with_generic_error

        with pytest.raises(SfuConnectionError):
            await cm.connect()

        assert call_count == 1

    @pytest.mark.asyncio
    @pytest.mark.parametrize("connection_manager", [1], indirect=True)
    async def test_cleans_up_ws_client_between_retries(self, connection_manager):
        """Partial WS state should be cleaned up before retry."""
        cm = connection_manager
        call_count = 0

        async def mock_connect_internal(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                cm._ws_client = MagicMock()
                mock_join_response = MagicMock()
                mock_join_response.credentials.server.edge_name = "sfu-node-1"
                cm.join_response = mock_join_response
                raise SfuJoinError(
                    "server is full",
                    error_code=models_pb2.ERROR_CODE_SFU_FULL,
                    should_retry=True,
                )
            cm.running = True

        cm._connect_internal = mock_connect_internal

        await cm.connect()

        assert call_count == 2
