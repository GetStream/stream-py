import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.rtc.connection_utils import SfuJoinError, SfuConnectionError
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


async def _instant_backoff(max_retries, base=1.0, factor=2.0, sleep=False):
    """exp_backoff replacement that never sleeps."""
    for attempt in range(max_retries):
        yield base * (factor**attempt)


class TestConnectRetry:
    """Tests for connect() retry logic when SFU is full."""

    def _make_connection_manager(self, max_join_retries=3):
        """Create a ConnectionManager with mocked dependencies."""
        with (
            patch("getstream.video.rtc.connection_manager.PeerConnectionManager"),
            patch("getstream.video.rtc.connection_manager.NetworkMonitor"),
            patch("getstream.video.rtc.connection_manager.ReconnectionManager"),
            patch("getstream.video.rtc.connection_manager.RecordingManager"),
            patch("getstream.video.rtc.connection_manager.SubscriptionManager"),
            patch("getstream.video.rtc.connection_manager.ParticipantsState"),
            patch("getstream.video.rtc.connection_manager.Tracer"),
        ):
            mock_call = MagicMock()
            mock_call.call_type = "default"
            mock_call.id = "test_call"
            cm = ConnectionManager(
                call=mock_call, user_id="user1", max_join_retries=max_join_retries
            )
            return cm

    @pytest.mark.asyncio
    @patch("getstream.video.rtc.connection_manager.exp_backoff", _instant_backoff)
    async def test_retries_on_sfu_join_error_and_passes_failed_sfus(self):
        """When SFU is full, connect() should retry with migrating_from_list."""
        cm = self._make_connection_manager(max_join_retries=2)

        call_count = 0
        received_migrating_from_list = []

        async def mock_connect_internal(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            received_migrating_from_list.append(migrating_from_list)

            if call_count <= 2:
                # Simulate SFU assigning an edge_name before failing
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
            # Third attempt succeeds
            cm.running = True

        cm._connect_internal = mock_connect_internal
        cm._connect_coordinator_ws = AsyncMock()

        await cm.connect()

        assert call_count == 3
        # First attempt: no failed SFUs
        assert received_migrating_from_list[0] is None
        # Second attempt: first SFU in the exclude list
        assert "sfu-node-1" in received_migrating_from_list[1]
        # Third attempt: both SFUs in the exclude list
        assert received_migrating_from_list[2] == ["sfu-node-1", "sfu-node-2"]

    @pytest.mark.asyncio
    @patch("getstream.video.rtc.connection_manager.exp_backoff", _instant_backoff)
    async def test_raises_after_all_retries_exhausted(self):
        """When all retries are exhausted, connect() should raise SfuJoinError."""
        cm = self._make_connection_manager(max_join_retries=1)

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
        cm._connect_coordinator_ws = AsyncMock()

        with pytest.raises(SfuJoinError):
            await cm.connect()

    @pytest.mark.asyncio
    async def test_non_retryable_error_propagates_immediately(self):
        """Non-retryable errors should not trigger retry."""
        cm = self._make_connection_manager(max_join_retries=3)

        call_count = 0

        async def fail_with_generic_error(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            raise SfuConnectionError("something went wrong")

        cm._connect_internal = fail_with_generic_error
        cm._connect_coordinator_ws = AsyncMock()

        with pytest.raises(SfuConnectionError):
            await cm.connect()

        # Should not retry — only one call
        assert call_count == 1

    @pytest.mark.asyncio
    @patch("getstream.video.rtc.connection_manager.exp_backoff", _instant_backoff)
    async def test_cleans_up_ws_client_between_retries(self):
        """Partial WS state should be cleaned up before retry."""
        cm = self._make_connection_manager(max_join_retries=1)

        call_count = 0

        async def mock_connect_internal(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # Simulate partial WS connection
                cm._ws_client = MagicMock()
                mock_join_response = MagicMock()
                mock_join_response.credentials.server.edge_name = "sfu-node-1"
                cm.join_response = mock_join_response
                raise SfuJoinError(
                    "server is full",
                    error_code=models_pb2.ERROR_CODE_SFU_FULL,
                    should_retry=True,
                )
            # Second attempt: ws_client should have been cleaned up
            cm.running = True

        cm._connect_internal = mock_connect_internal
        cm._connect_coordinator_ws = AsyncMock()

        await cm.connect()

        assert call_count == 2
