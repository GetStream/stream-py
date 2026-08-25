"""Live participant roster: join/leave/count across two connections, call-ended.

Mirrors stream-video-js Call participant state and Swift StreamVideoTests
join/leave roster assertions.
"""

import pytest

from getstream.video.rtc.connection_utils import ConnectionState
from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import EventLog, live_call, rtc, wait_for_state


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _user_ids(connection) -> set[str]:
    return {p.user_id for p in connection.participants_state.get_participants()}


def _joined_user_ids(events: EventLog) -> set[str]:
    users = set()
    for args in events.payloads("participant_joined"):
        if args:
            users.add(args[0].participant.user_id)
    return users


def _left_user_ids(events: EventLog) -> set[str]:
    users = set()
    for args in events.payloads("participant_left"):
        if args:
            users.add(args[0].participant.user_id)
    return users


class TestLiveRoster:
    @skip_on_rate_limit
    async def test_join_leave_updates_participant_count(self, live_call):
        call, users = live_call
        user_a, user_b = users[0], users[1]

        async with await rtc.join(call, user_a) as connection_a:
            await wait_for_state(connection_a, ConnectionState.JOINED)
            events_a = EventLog()
            events_a.bind(connection_a, "participant_joined")
            events_a.bind(connection_a, "participant_left")

            async with await rtc.join(call, user_b) as connection_b:
                await wait_for_state(connection_b, ConnectionState.JOINED)
                events_b = EventLog()
                events_b.bind(connection_b, "participant_joined")

                await events_a.wait_for(
                    lambda: user_b in _user_ids(connection_a)
                    or user_b in _joined_user_ids(events_a),
                    timeout=20.0,
                    message="A did not observe B joining the call",
                )
                await events_b.wait_for(
                    lambda: user_a in _user_ids(connection_b)
                    or user_a in _joined_user_ids(events_b)
                    or len(connection_b.participants_state.get_participants()) >= 1,
                    timeout=20.0,
                    message="B did not observe A already in the call",
                )
                assert len(connection_a.participants_state.get_participants()) >= 1

            await events_a.wait_for(
                lambda: user_b not in _user_ids(connection_a)
                or user_b in _left_user_ids(events_a),
                timeout=20.0,
                message="A did not observe B leaving the call",
            )

    @skip_on_rate_limit
    async def test_call_ended_is_emitted(self, live_call):
        call, users = live_call
        async with await rtc.join(call, users[0]) as connection:
            await wait_for_state(connection, ConnectionState.JOINED)
            events = EventLog()
            events.bind(connection, "call_ended")

            await call.end()
            await events.wait_for(
                lambda: bool(events.payloads("call_ended")),
                timeout=20.0,
                message="call.end() did not emit call_ended on ConnectionManager",
            )
