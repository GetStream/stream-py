import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional

import aiortc

from getstream import _rust
from getstream.common import telemetry
from getstream.utils import StreamAsyncIOEventEmitter
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

from getstream.video.async_call import Call
from getstream.video.rtc.audio_forwarder import AudioForwarder
from getstream.video.rtc.video_forwarder import VideoForwarder
from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.track_util import (
    AudioFormat,
    PcmData,
)
from getstream.video.rtc.participants import ParticipantsState
from getstream.video.rtc.tracks import (
    SubscriptionConfig,
    TrackSubscriptionConfig,
)

logger = logging.getLogger(__name__)


async def _log_event(event_type: str, data: Any):
    logger.debug(f"Received event {event_type}: {data}")


_AUDIO_TRACK_TYPES = (_rust.TrackType.AUDIO, _rust.TrackType.SCREEN_SHARE_AUDIO)
# Events that each SDK event stream buffers while the event loop is blocked
# (SDK default 256); more makes a lag less likely and costs memory per call.
_CALL_EVENT_CAPACITY = 1024
# The unit of `PcmFrame.pts`: the 48 kHz RTP clock of Opus.
_OPUS_TIME_BASE = 1 / 48000
_TRACK_TYPES: dict[int, _rust.TrackType] = {
    models_pb2.TRACK_TYPE_AUDIO: _rust.TrackType.AUDIO,
    models_pb2.TRACK_TYPE_VIDEO: _rust.TrackType.VIDEO,
    models_pb2.TRACK_TYPE_SCREEN_SHARE: _rust.TrackType.SCREEN_SHARE,
    models_pb2.TRACK_TYPE_SCREEN_SHARE_AUDIO: _rust.TrackType.SCREEN_SHARE_AUDIO,
}


def _rust_subscription_config(config: SubscriptionConfig) -> _rust.SubscriptionConfig:
    return _rust.SubscriptionConfig(
        default=_rust_track_subscription_config(config.default),
        role_filters={
            role: _rust_track_subscription_config(rule)
            for role, rule in config.role_filters.items()
        },
        max_subscriptions=config.max_subscriptions,
    )


def _rust_track_subscription_config(
    rule: TrackSubscriptionConfig,
) -> _rust.TrackSubscriptionConfig:
    return _rust.TrackSubscriptionConfig(
        # An unknown value matches no track, as in the aiortc version.
        track_types=[
            _TRACK_TYPES[track_type]
            for track_type in rule.track_types
            if track_type in _TRACK_TYPES
        ],
        video_dimension=(rule.video_dimension.width, rule.video_dimension.height),
        screenshare_dimension=(
            rule.screenshare_dimension.width,
            rule.screenshare_dimension.height,
        ),
    )


class ConnectionManager(StreamAsyncIOEventEmitter):
    """Main connection manager facade for video streaming."""

    def __init__(
        self,
        call: Call,
        user_id: str,
        create: bool = True,
        subscription_config: Optional[SubscriptionConfig] = None,
    ):
        super().__init__()
        if call.id is None:
            raise TypeError("the call has no id")

        # Public attributes
        self.call: Call = call
        self.user_id: str = user_id
        self.create: bool = create

        # Created before the join, so the tracks and events of the join are kept.
        stream = call.client.stream
        if stream.has_api_secret:
            rust_client = _rust.Client(
                stream.api_key,
                stream.api_secret,
                base_url=stream.base_url,
                call_event_capacity=_CALL_EVENT_CAPACITY,
            )
        else:
            rust_client = _rust.Client(
                stream.api_key,
                token=stream.token,
                base_url=stream.base_url,
                call_event_capacity=_CALL_EVENT_CAPACITY,
            )
        self._rust_call: _rust.Call = rust_client.call(call.call_type, call.id)
        self._subscription_config = subscription_config
        self._event_tasks: list[asyncio.Task] = []
        self._audio_tasks: set[asyncio.Task] = set()
        # The forwarding task of the published track of each kind.
        self._publish_tasks: dict[str, asyncio.Task] = {}
        self._leaving: bool = False
        self._call_ended_sent: bool = False

        # Private attributes
        self._stop_event: asyncio.Event = asyncio.Event()

        # Initialize private managers
        self._participants_state: ParticipantsState = ParticipantsState()

        self.participants_state = self._participants_state

    @property
    def connection_state(self) -> _rust.CallingState:
        """Get the current connection state."""
        return self._rust_call.calling_state

    def emit(self, event: str, *args: Any, unsafe: bool = False, **kwargs: Any) -> bool:
        """Calls the handlers of `event`. Unless `unsafe`, a handler that raises
        is logged, so it cannot stop the task that emits."""
        if unsafe:
            return super().emit(event, *args, **kwargs)
        try:
            return super().emit(event, *args, **kwargs)
        except Exception:
            logger.exception(f"A {event!r} handler failed")
            return True

    @telemetry.with_span("connect")
    async def connect(self):
        """
        Join the call. The SDK retries the join and chooses the SFU.
        """
        logger.info("Joining the call")
        # Process-wide. Rust drops records below this level before it formats
        # them, so a later level change applies at the next connect().
        sdk_logger = logging.getLogger("getstream")
        _rust.configure_logging(sdk_logger, sdk_logger.getEffectiveLevel())
        # The streams are created before the join, so the events and tracks of
        # the join are kept. Both end when the call ends or is left.
        call = self._rust_call
        tasks = [
            asyncio.create_task(self._emit_sfu_events(call.sfu_events())),
            asyncio.create_task(
                self._emit_coordinator_events(call.coordinator_events())
            ),
            asyncio.create_task(self._emit_client_events(call.client_events())),
            asyncio.create_task(self._emit_tracks(call.tracks())),
        ]
        try:
            await call.join(self.user_id, self.create)
            # Includes this participant, which gets no `participant_joined`.
            for participant in call.participants():
                self._participants_state._add_participant(participant)
            # Without a config nothing is requested, as in the aiortc version;
            # the SFU sends remote audio without a request.
            if self._subscription_config is not None:
                await call.update_subscriptions(
                    _rust_subscription_config(self._subscription_config)
                )
        except BaseException:
            for task in tasks:
                task.cancel()
            # A failure after the SDK join must not keep this session in the call.
            await call.leave()
            raise
        self._event_tasks = tasks

    async def _emit_sfu_events(self, events: _rust.EventStream) -> None:
        async for event in events:
            if isinstance(event, _rust.EventsLagged):
                # The lost events can include participant changes.
                self._participants_state._replace_participants(
                    self._rust_call.participants()
                )
                continue
            if isinstance(event, _rust.ParticipantJoined):
                await self._participants_state._on_participant_joined(event)
            elif isinstance(event, _rust.ParticipantLeft):
                await self._participants_state._on_participant_left(event)
            if isinstance(event, _rust.CallEnded):
                self._emit_call_ended(event)
            else:
                self.emit(event.name, event)

    async def _emit_coordinator_events(self, events: _rust.EventStream) -> None:
        async for event in events:
            # The stream gives only `CoordinatorEvent` and `EventsLagged`.
            if not isinstance(event, _rust.CoordinatorEvent):
                continue
            # Of the coordinator events, only `custom` is emitted, as its dict.
            if event.name == "custom":
                self.emit("custom", event.data)
            else:
                await _log_event(event.name, event.data)

    async def _emit_client_events(self, events: _rust.EventStream) -> None:
        old = _rust.CallingState.IDLE
        async for event in events:
            # The stream gives only `CallingStateChanged` and `EventsLagged`.
            if not isinstance(event, _rust.CallingStateChanged):
                continue
            self.emit("connection.state_changed", {"old": old, "new": event.state})
            old = event.state
            # The SDK leaves on the SFU `call_ended` and on the coordinator
            # `call.ended`; after the latter the SFU `call_ended` may not come.
            if event.state == _rust.CallingState.LEFT and not self._leaving:
                self._emit_call_ended(_rust.CallEnded())
        self._stop_event.set()

    def _emit_call_ended(self, event: _rust.CallEnded) -> None:
        if not self._call_ended_sent:
            self._call_ended_sent = True
            self.emit("call_ended", event)

    async def _emit_tracks(self, tracks: _rust.TrackStream) -> None:
        async for track in tracks:
            self.emit("track_added", track)
            if track.track_type in _AUDIO_TRACK_TYPES:
                task = asyncio.create_task(self._emit_audio(track))
                self._audio_tasks.add(task)
                task.add_done_callback(self._audio_tasks.discard)
            # Holds no reference: dropping the last one unsubscribes the track.
            del track

    async def _emit_audio(self, track: _rust.RemoteTrack) -> None:
        # Reads every frame of the track, so no other reader may read it.
        while (frame := await track.next_pcm()) is not None:
            self.emit(
                "audio",
                PcmData(
                    sample_rate=frame.sample_rate,
                    format=AudioFormat.S16,
                    samples=frame.samples,
                    channels=frame.channels,
                    pts=frame.pts,
                    time_base=_OPUS_TIME_BASE,
                    participant=track.participant,
                ),
            )

    async def wait(self):
        """
        Wait until the connection is over.

        This is useful for tests and examples where you want to wait for the
        connection to end rather than just sleeping for a fixed time.

        Returns when the connection is over (either naturally ended or
        explicitly stopped with leave()).
        """
        await self._stop_event.wait()

    @telemetry.with_span("leave")
    async def leave(self):
        """Gracefully leave the call and close connections."""
        logger.info("Leaving the call")
        self._leaving = True
        self._stop_event.set()
        await self._rust_call.leave()
        await asyncio.gather(*self._event_tasks)
        media_tasks = [*self._audio_tasks, *self._publish_tasks.values()]
        for task in media_tasks:
            task.cancel()
        if media_tasks:
            await asyncio.wait(media_tasks)
        logger.info("Call left and connections closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.leave()

    async def add_tracks(
        self,
        audio: Optional[aiortc.MediaStreamTrack] = None,
        video: Optional[aiortc.MediaStreamTrack] = None,
    ) -> None:
        """Publish `audio` and `video`, aiortc tracks.

        The SDK paces the audio and sends it as mono, so the audio track need not
        be paced (`AudioStreamTrack(pace=False)`). The video track paces itself;
        it is sent as VP9 at the size of its first frame. A track that ends is
        unpublished. A new track replaces the published track of its kind.
        """
        with telemetry.start_as_current_span("rtc.add_tracks"):
            if audio is not None:
                await self._publish_audio(audio)
            if video is not None:
                await self._publish_video(video)

    async def _publish_audio(self, track: aiortc.MediaStreamTrack) -> None:
        # The SDK queue holds the backlog, so it gets the track's buffer size.
        capacity = (
            track.audio_buffer_size_ms / 1000
            if isinstance(track, AudioStreamTrack)
            else None
        )
        rust_track = _rust.LocalAudioTrack(pcm_queue_capacity=capacity)
        # The SFU has one publish option for each kind of track.
        await self._stop_forwarding("audio")
        await self._rust_call.publish_audio(rust_track)
        self._start_forwarding(
            "audio",
            AudioForwarder(track, rust_track),
            self._rust_call.stop_publish_audio,
        )

    async def _publish_video(self, track: aiortc.MediaStreamTrack) -> None:
        # VP9 is the SFU's default publish option for camera video; no other
        # codec is requested at join.
        rust_track = _rust.LocalVideoTrack.vp9()
        await self._stop_forwarding("video")
        await self._rust_call.publish_video(rust_track)
        self._start_forwarding(
            "video",
            VideoForwarder(track, rust_track),
            self._rust_call.stop_publish_video,
        )

    def _start_forwarding(
        self,
        kind: str,
        forwarder: AudioForwarder | VideoForwarder,
        stop_publish: Callable[[Any], Awaitable[None]],
    ) -> None:
        self._publish_tasks[kind] = asyncio.create_task(
            self._forward(forwarder, stop_publish)
        )

    async def _stop_forwarding(self, kind: str) -> None:
        """Unpublish the published track of `kind`, if there is one."""
        task = self._publish_tasks.pop(kind, None)
        if task is not None:
            task.cancel()
            await asyncio.wait([task])

    async def _forward(
        self,
        forwarder: AudioForwarder | VideoForwarder,
        stop_publish: Callable[[Any], Awaitable[None]],
    ) -> None:
        try:
            await forwarder.run()
        finally:
            # The source track ended, or the forwarding was cancelled.
            await stop_publish(forwarder.target)
