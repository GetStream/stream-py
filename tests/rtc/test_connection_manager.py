import asyncio
import contextlib
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from dotenv import load_dotenv

from getstream import AsyncStream
from getstream.models import CallRequest, UserRequest
from getstream.video import rtc
from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.rtc.connection_utils import (
    ConnectionState,
    SfuConnectionError,
    SfuJoinError,
)
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.reconnection import ReconnectionStrategy

load_dotenv()


@contextlib.contextmanager
def patched_dependencies():
    """Patch heavy ConnectionManager dependencies for unit testing."""
    with (
        patch("getstream.video.rtc.connection_manager.PeerConnectionManager"),
        patch("getstream.video.rtc.connection_manager.NetworkMonitor"),
        patch("getstream.video.rtc.connection_manager.ReconnectionManager"),
        patch("getstream.video.rtc.connection_manager.RecordingManager"),
        patch("getstream.video.rtc.connection_manager.SubscriptionManager"),
        patch("getstream.video.rtc.connection_manager.ParticipantsState"),
        patch("getstream.video.rtc.connection_manager.Tracer"),
        patch(
            "getstream.video.rtc.connection_manager.asyncio.sleep",
            new_callable=AsyncMock,
        ),
    ):
        yield


@pytest.fixture
def connection_manager(request):
    """Create a ConnectionManager with mocked heavy dependencies.

    Accepts max_join_retries via indirect parametrize, defaults to 3.
    """
    max_join_retries = getattr(request, "param", 3)
    with patched_dependencies():
        mock_call = MagicMock()
        mock_call.call_type = "default"
        mock_call.id = "test_call"
        cm = ConnectionManager(
            call=mock_call, user_id="user1", max_join_retries=max_join_retries
        )
        cm._connect_coordinator_ws = AsyncMock()
        yield cm


@pytest.fixture
def client():
    return AsyncStream(timeout=10.0)


class TestConnectionManager:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_leave_twice_does_not_hang(self, client: AsyncStream):
        """Integration test: join a real call and leave twice without hanging."""
        call_id = str(uuid.uuid4())
        call = client.video.call("default", call_id)

        async with await rtc.join(call, "test-user") as connection:
            assert connection.connection_state == ConnectionState.JOINED

            await asyncio.sleep(2)

            await asyncio.wait_for(connection.leave(), timeout=10.0)
            assert connection.connection_state == ConnectionState.LEFT

            # Second leave must not hang
            await asyncio.wait_for(connection.leave(), timeout=10.0)
            assert connection.connection_state == ConnectionState.LEFT

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_token_only_client_can_join_call(self, client: AsyncStream):
        """A token-only AsyncStream can join a call created by a secret-holding client."""
        call_id = str(uuid.uuid4())
        user_id = f"test-user-{uuid.uuid4()}"
        call_cid = f"default:{call_id}"

        await client.upsert_users(UserRequest(id=user_id))

        server_call = client.video.call("default", call_id)
        await server_call.get_or_create(data=CallRequest(created_by_id="test-admin"))

        user_token = client.create_call_token(user_id, call_cids=[call_cid])

        async with AsyncStream(
            api_key=client.api_key,
            token=user_token,
            base_url=client.base_url,
            timeout=10.0,
        ) as token_client:
            assert token_client.has_api_secret is False

            token_call = token_client.video.call("default", call_id)

            async with await rtc.join(token_call, user_id) as connection:
                assert connection.connection_state == ConnectionState.JOINED
                await asyncio.sleep(2)
                await asyncio.wait_for(connection.leave(), timeout=10.0)
                assert connection.connection_state == ConnectionState.LEFT

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
        call_count = 0

        async def always_fail(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
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

        assert call_count == 2  # 1 initial + 1 retry

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

        first_ws_client = MagicMock()

        async def mock_connect_internal(migrating_from_list=None, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                cm._ws_client = first_ws_client
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
        first_ws_client.close.assert_called_once()
        assert cm._ws_client is None

    def test_rejects_negative_max_join_retries(self):
        """max_join_retries must be >= 0."""
        with (
            patched_dependencies(),
            pytest.raises(ValueError, match="max_join_retries must be >= 0"),
        ):
            ConnectionManager(call=MagicMock(), user_id="user1", max_join_retries=-1)

    @pytest.mark.asyncio
    async def test_signaling_connection_lost_triggers_fast_reconnect(
        self, connection_manager
    ):
        """A signaling-WS `connection_lost` event drives a FAST reconnect.

        Without this handler the session would sit hanging on a transient
        socket drop until the frontend tears it down.
        """
        cm = connection_manager
        cm.running = True
        cm._reconnector.reconnect = AsyncMock()

        await cm._on_signaling_connection_lost("health check timeout")

        cm._reconnector.reconnect.assert_called_once()
        kwargs = cm._reconnector.reconnect.call_args.kwargs
        assert kwargs["strategy"] == ReconnectionStrategy.FAST
        assert "health check timeout" in kwargs["reason"]
