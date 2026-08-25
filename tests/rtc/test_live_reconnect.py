"""Live FAST vs REJOIN recovery, state transitions, and reconnect events.

Mirrors stream-video-js Call reconnect coverage and the live reconnect
benchmark: drive ConnectionManager.reconnector against a real SFU session.
"""

import pytest

from getstream.video.rtc.connection_utils import ConnectionState
from getstream.video.rtc.reconnection import ReconnectionStrategy
from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import EventLog, live_call, rtc, wait_for_state


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _recorded_states(events: EventLog) -> list[ConnectionState]:
    states = []
    for args in events.payloads("connection.state_changed"):
        if not args:
            continue
        payload = args[0]
        new = payload.get("new") if isinstance(payload, dict) else None
        if new is not None:
            states.append(new)
    return states


def _success_strategies(events: EventLog) -> list[str]:
    strategies = []
    for args in events.payloads("reconnection_success"):
        if not args:
            continue
        payload = args[0]
        if isinstance(payload, dict) and payload.get("strategy"):
            strategies.append(payload["strategy"])
    return strategies


class TestLiveReconnect:
    @skip_on_rate_limit
    async def test_fast_reconnect_recovers_and_emits_success(self, live_call):
        call, users = live_call
        async with await rtc.join(call, users[0]) as connection:
            assert connection.connection_state == ConnectionState.JOINED

            events = EventLog()
            events.bind(connection, "connection.state_changed")
            events.bind(connection, "reconnection_success")
            events.bind(connection, "reconnection_failed")

            await connection.reconnector.reconnect(
                ReconnectionStrategy.FAST, "live FAST coverage"
            )

            await events.wait_for(
                lambda: bool(_success_strategies(events)),
                timeout=30.0,
                message="FAST reconnect did not emit reconnection_success",
            )
            assert not events.payloads("reconnection_failed")
            assert ReconnectionStrategy.FAST in _success_strategies(events)
            assert connection.connection_state == ConnectionState.JOINED
            states = _recorded_states(events)
            assert ConnectionState.RECONNECTING in states
            assert states[-1] == ConnectionState.JOINED

    @skip_on_rate_limit
    async def test_rejoin_recovers_and_emits_success(self, live_call):
        call, users = live_call
        async with await rtc.join(call, users[0]) as connection:
            assert connection.connection_state == ConnectionState.JOINED
            previous_tag = connection._sfu_client_tag

            events = EventLog()
            events.bind(connection, "connection.state_changed")
            events.bind(connection, "reconnection_success")
            events.bind(connection, "reconnection_failed")

            await connection.reconnector.reconnect(
                ReconnectionStrategy.REJOIN, "live REJOIN coverage"
            )

            await events.wait_for(
                lambda: ReconnectionStrategy.REJOIN in _success_strategies(events),
                timeout=30.0,
                message="REJOIN reconnect did not emit reconnection_success",
            )
            assert not events.payloads("reconnection_failed")
            assert connection.connection_state == ConnectionState.JOINED
            assert connection._sfu_client_tag == previous_tag + 1
            states = _recorded_states(events)
            assert ConnectionState.RECONNECTING in states
            assert states[-1] == ConnectionState.JOINED
            assert ReconnectionStrategy.REJOIN in _success_strategies(events)

    @skip_on_rate_limit
    async def test_reconnect_with_invalid_sfu_credentials_emits_failed(self, live_call):
        call, users = live_call
        async with await rtc.join(call, users[0]) as connection:
            await wait_for_state(connection, ConnectionState.JOINED)

            events = EventLog()
            events.bind(connection, "reconnection_success")
            events.bind(connection, "reconnection_failed")
            events.bind(connection, "connection.state_changed")

            # Detach the healthy Rust session so FAST cannot early-return as joined,
            # then force the SFU handshake to fail.
            connection._rtc_session = None
            connection.ws_client.running = False
            connection.publisher_pc = None
            connection.join_response.credentials.token = "invalid-sfu-token"

            await connection.reconnector.reconnect(
                ReconnectionStrategy.FAST, "invalid SFU token"
            )

            await events.wait_for(
                lambda: bool(events.payloads("reconnection_failed"))
                or connection.connection_state == ConnectionState.RECONNECTING_FAILED,
                timeout=20.0,
                message="invalid SFU credentials did not fail reconnection",
            )
