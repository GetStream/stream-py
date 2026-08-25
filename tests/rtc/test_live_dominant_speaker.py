"""Live dominant-speaker and audio-level events with two publishers.

Mirrors Rust tests/rtc_media.rs `loud_publisher_is_reported_speaking_and_dominant`
and the JS Call dominantSpeaker / audioLevelChanged observers: the SFU only
emits these signaling events when outbound audio carries RFC 6464 levels.
"""

import pytest

from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import (
    LOUD_TONE_AMP,
    EventLog,
    apply_subscriptions,
    audio_only_config,
    live_call,
    publishing_audio,
    rtc,
)


pytestmark = [pytest.mark.asyncio, pytest.mark.integration, pytest.mark.timeout(180)]


def _speaking(events: EventLog, user_id: str) -> bool:
    for args in events.payloads("audio_level_changed"):
        if not args:
            continue
        payload = args[0]
        for level in payload.audio_levels:
            if level.user_id == user_id and level.is_speaking:
                return True
    return False


def _dominant(events: EventLog, user_id: str) -> bool:
    for args in events.payloads("dominant_speaker_changed"):
        if not args:
            continue
        payload = args[0]
        if payload.user_id == user_id:
            return True
    return False


class TestLiveDominantSpeaker:
    @skip_on_rate_limit
    async def test_loud_publisher_becomes_speaking_and_dominant(self, live_call):
        call, users = live_call
        user_a, user_b = users[0], users[1]

        async with await rtc.join(
            call, user_b, subscription_config=audio_only_config()
        ) as connection_b:
            events = EventLog()
            events.bind(connection_b, "audio_level_changed")
            events.bind(connection_b, "dominant_speaker_changed")
            await apply_subscriptions(connection_b, audio=True, video=False)

            async with publishing_audio(connection_b, amp=LOUD_TONE_AMP) as pub_b:
                await events.wait_for(
                    lambda: _speaking(events, user_b) and _dominant(events, user_b),
                    timeout=45.0,
                    message=f"SFU never established {user_b} as speaking/dominant",
                )
                pub_b.stop_feeding()

                async with await rtc.join(call, user_a) as connection_a:
                    async with publishing_audio(
                        connection_a, amp=LOUD_TONE_AMP, speech=True
                    ):
                        await events.wait_for(
                            lambda: _speaking(events, user_a)
                            and _dominant(events, user_a),
                            timeout=45.0,
                            message=(
                                f"SFU never transitioned dominant speaker "
                                f"from {user_b} to {user_a}"
                            ),
                        )
