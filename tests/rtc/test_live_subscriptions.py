"""Live subscription policy: audio-only default, selective video, pause/resume.

Ports the JS Call / Rust rtc_media subscription cases onto ConnectionManager
events and SubscriptionConfig passed to rtc.join.
"""

import asyncio

import pytest

from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import (
    MEDIA_TIMEOUT,
    EventLog,
    apply_subscriptions,
    audio_only_config,
    audio_video_config,
    live_call,
    publishing_audio,
    publishing_video,
    rtc,
    wait_for_non_silent_audio,
)


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _kinds(events: EventLog) -> set[str]:
    return {args[1] for args in events.payloads("track_added") if len(args) >= 2}


class TestLiveSubscriptions:
    @skip_on_rate_limit
    async def test_audio_only_default_does_not_deliver_video(self, live_call):
        call, users = live_call
        publisher_id, subscriber_id = users[0], users[1]

        async with await rtc.join(
            call, subscriber_id, subscription_config=audio_only_config()
        ) as subscriber:
            events = EventLog()
            events.bind(subscriber, "track_added")
            events.bind(subscriber, "audio")

            async with await rtc.join(call, publisher_id) as publisher:
                async with publishing_audio(publisher), publishing_video(publisher):
                    await apply_subscriptions(subscriber, audio=True, video=False)
                    await wait_for_non_silent_audio(events)
                    await asyncio.sleep(8.0)
                    assert "audio" in _kinds(events)
                    assert "video" not in _kinds(events)

    @skip_on_rate_limit
    async def test_selective_video_subscribe_delivers_video_track(self, live_call):
        call, users = live_call
        publisher_id, subscriber_id = users[0], users[1]

        async with await rtc.join(
            call, subscriber_id, subscription_config=audio_video_config()
        ) as subscriber:
            events = EventLog()
            events.bind(subscriber, "track_added")

            async with await rtc.join(call, publisher_id) as publisher:
                async with publishing_video(publisher):
                    await apply_subscriptions(subscriber, audio=True, video=True)
                    await events.wait_for(
                        lambda: "video" in _kinds(events),
                        timeout=MEDIA_TIMEOUT,
                        message="video subscription did not deliver a video track",
                    )

    @skip_on_rate_limit
    async def test_unsubscribe_and_resubscribe_video(self, live_call):
        """Pause/resume via coarse update_subscriptions (JS pause/resume analogue)."""
        call, users = live_call
        publisher_id, subscriber_id = users[0], users[1]

        async with await rtc.join(
            call, subscriber_id, subscription_config=audio_only_config()
        ) as subscriber:
            events = EventLog()
            events.bind(subscriber, "track_added")
            events.bind(subscriber, "audio")

            async with await rtc.join(call, publisher_id) as publisher:
                async with publishing_audio(publisher), publishing_video(publisher):
                    await apply_subscriptions(subscriber, audio=True, video=False)
                    await wait_for_non_silent_audio(events)
                    await asyncio.sleep(5.0)
                    assert "video" not in _kinds(events)

                    await apply_subscriptions(subscriber, audio=True, video=True)
                    await events.wait_for(
                        lambda: "video" in _kinds(events),
                        timeout=MEDIA_TIMEOUT,
                        message="subscribing to video did not deliver a video track",
                    )
                    video_count = sum(
                        1 for args in events.payloads("track_added") if args[1] == "video"
                    )

                    await apply_subscriptions(subscriber, audio=True, video=False)
                    await asyncio.sleep(5.0)
                    assert (
                        sum(
                            1
                            for args in events.payloads("track_added")
                            if args[1] == "video"
                        )
                        == video_count
                    )

                    await apply_subscriptions(subscriber, audio=True, video=True)
                    await asyncio.sleep(8.0)
                    # Resume may reuse the existing transceiver; audio must stay live.
                    await wait_for_non_silent_audio(events)
