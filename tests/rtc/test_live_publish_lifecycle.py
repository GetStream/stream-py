"""Live publish lifecycle: mute/unmute, stop/republish, video round-trip.

Codec round-trips for VP8/H264 are skipped unless ConnectionManager.add_tracks
exposes a codec argument — the frozen public API publishes the SFU video option (VP9).
"""

import asyncio
import inspect

import pytest

from getstream.video.rtc.connection_manager import ConnectionManager
from tests.conftest import skip_on_rate_limit
from tests.rtc.live_support import (
    MEDIA_TIMEOUT,
    EventLog,
    apply_subscriptions,
    audio_only_config,
    audio_video_config,
    feed_tone,
    live_call,
    publishing_audio,
    publishing_video,
    rtc,
    rtc_session,
    wait_for_non_silent_audio,
)


pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _add_tracks_exposes_codec() -> bool:
    params = inspect.signature(ConnectionManager.add_tracks).parameters
    return any(name in params for name in ("codec", "video_codec", "preferred_codec"))


class TestLivePublishLifecycle:
    @skip_on_rate_limit
    async def test_mute_and_unmute_audio(self, live_call):
        call, users = live_call
        publisher_id, subscriber_id = users[0], users[1]

        async with await rtc.join(
            call, subscriber_id, subscription_config=audio_only_config()
        ) as subscriber:
            events = EventLog()
            events.bind(subscriber, "audio")
            events.bind(subscriber, "track_unpublished")
            events.bind(subscriber, "track_published")

            async with await rtc.join(call, publisher_id) as publisher:
                session = rtc_session(publisher)
                try:
                    mute = session.mute_track
                    unmute = session.unmute_track
                except AttributeError:
                    pytest.skip("RtcSession does not expose mute_track/unmute_track")

                async with publishing_audio(publisher):
                    await apply_subscriptions(subscriber, audio=True, video=False)
                    await wait_for_non_silent_audio(events)
                    before = len(events.payloads("audio"))

                    await mute("audio")
                    await asyncio.sleep(3.0)
                    unpublished = any(
                        args[0].user_id == publisher_id
                        for args in events.payloads("track_unpublished")
                        if args
                    )
                    after_mute = len(events.payloads("audio"))
                    # Either the SFU un-announces the track or RTP goes silent.
                    assert unpublished or after_mute - before < 50

                    await unmute("audio")
                    await asyncio.sleep(1.0)
                    events.items = [
                        item for item in events.items if item[0] != "audio"
                    ]
                    await wait_for_non_silent_audio(events)

    @skip_on_rate_limit
    async def test_stop_and_republish_audio(self, live_call):
        """Stop outbound audio (mute, matching JS/Rust stopPublish) then resume.

        A second ConnectionManager.add_tracks call cannot occupy a new Opus
        publish option — the SFU keeps the original publisher envelope.
        """
        call, users = live_call
        publisher_id, subscriber_id = users[0], users[1]

        async with await rtc.join(
            call, subscriber_id, subscription_config=audio_only_config()
        ) as subscriber:
            events = EventLog()
            events.bind(subscriber, "audio")
            events.bind(subscriber, "track_added")

            async with await rtc.join(call, publisher_id) as publisher:
                session = rtc_session(publisher)
                async with publishing_audio(publisher) as publication:
                    await apply_subscriptions(subscriber, audio=True, video=False)
                    await wait_for_non_silent_audio(events)
                    publication.stop_feeding()
                    await session.mute_track("audio")
                    await asyncio.sleep(2.0)

                    events.items = [
                        item for item in events.items if item[0] != "audio"
                    ]
                    await session.unmute_track("audio")
                    resume = asyncio.Event()
                    feeder = asyncio.create_task(
                        feed_tone(publication.track, resume),
                        name="live-republish-feeder",
                    )
                    try:
                        await wait_for_non_silent_audio(events)
                    finally:
                        resume.set()
                        feeder.cancel()
                        try:
                            await feeder
                        except asyncio.CancelledError:
                            pass

    @skip_on_rate_limit
    async def test_video_round_trip(self, live_call):
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
                        lambda: any(
                            args[1] == "video" for args in events.payloads("track_added")
                        ),
                        timeout=MEDIA_TIMEOUT,
                        message="video publish did not deliver a remote video track",
                    )

    async def test_vp9_h264_round_trips_require_codec_api(self):
        if not _add_tracks_exposes_codec():
            pytest.skip(
                "ConnectionManager.add_tracks does not expose video codec selection"
            )
        pytest.fail("codec argument is exposed; add VP9/H264 live round-trips")
