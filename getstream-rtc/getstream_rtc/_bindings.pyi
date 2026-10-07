import logging
from enum import Enum
from typing import Any, Awaitable

import numpy as np
import numpy.typing as npt

def configure_logging(
    logger: logging.Logger | None, level: int, third_party_level: int = 30
) -> None:
    """Send SDK records at `level` or above, and records of third-party Rust
    crates at the less verbose of `level` and `third_party_level`, to `logger`
    and the loggers below it. `logger=None` stops forwarding. Process-wide: the
    last call wins. Returns after the records queued before the call have been
    delivered."""

class CallingState(Enum):
    IDLE = ...
    JOINING = ...
    JOINED = ...
    RECONNECTING = ...
    MIGRATING = ...
    RECONNECTING_FAILED = ...
    LEFT = ...

class TrackType(Enum):
    UNSPECIFIED = ...
    AUDIO = ...
    VIDEO = ...
    SCREEN_SHARE = ...
    SCREEN_SHARE_AUDIO = ...

class RemoteParticipant:
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def name(self) -> str: ...
    @property
    def image(self) -> str: ...
    @property
    def roles(self) -> list[str]: ...
    @property
    def published_tracks(self) -> list[TrackType]: ...
    @property
    def connection_quality(self) -> int:
        """The protobuf ``ConnectionQuality`` value."""
    @property
    def is_speaking(self) -> bool: ...
    @property
    def is_dominant_speaker(self) -> bool: ...
    @property
    def audio_level(self) -> float: ...
    @property
    def source(self) -> int:
        """The protobuf ``ParticipantSource`` value."""
    @property
    def joined_at(self) -> float | None:
        """Unix time in seconds, or ``None`` if the SFU did not send it."""
    @property
    def custom(self) -> dict[str, Any]:
        """Empty if the SFU did not send it."""

class TrackSubscriptionConfig:
    """The subscription rule for the participants of one role, or the default
    rule. A ``None`` argument keeps the SDK default (no track types,
    1920x1080)."""

    def __init__(
        self,
        track_types: list[TrackType] | None = None,
        video_dimension: tuple[int, int] | None = None,
        screenshare_dimension: tuple[int, int] | None = None,
    ) -> None: ...
    @property
    def track_types(self) -> list[TrackType]: ...
    @property
    def video_dimension(self) -> tuple[int, int]: ...
    @property
    def screenshare_dimension(self) -> tuple[int, int]: ...

class SubscriptionConfig:
    """The SDK applies the rule of the first role in ``participant.roles`` that
    has an entry in ``role_filters``, or else ``default``, and keeps at most
    ``max_subscriptions`` tracks."""

    def __init__(
        self,
        default: TrackSubscriptionConfig | None = None,
        role_filters: dict[str, TrackSubscriptionConfig] | None = None,
        max_subscriptions: int | None = None,
    ) -> None: ...
    @property
    def default(self) -> TrackSubscriptionConfig: ...
    @property
    def role_filters(self) -> dict[str, TrackSubscriptionConfig]: ...
    @property
    def max_subscriptions(self) -> int | None: ...

class CallStateSnapshot:
    @property
    def participants(self) -> list[RemoteParticipant]: ...
    @property
    def own_capabilities(self) -> list[str]: ...

class CallEvent:
    @property
    def name(self) -> str:
        """The stable SDK event name: the ``SfuEvent`` oneof field name for SFU
        events, the ``type`` for coordinator events."""

class ParticipantJoined(CallEvent):
    @property
    def call_cid(self) -> str: ...
    @property
    def participant(self) -> RemoteParticipant: ...

class ParticipantLeft(CallEvent):
    @property
    def call_cid(self) -> str: ...
    @property
    def participant(self) -> RemoteParticipant: ...

class TrackPublished(CallEvent):
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def track_type(self) -> TrackType: ...
    @property
    def participant(self) -> RemoteParticipant | None: ...

class TrackUnpublished(CallEvent):
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def track_type(self) -> TrackType: ...
    @property
    def cause(self) -> int:
        """The protobuf ``TrackUnpublishReason`` value."""
    @property
    def participant(self) -> RemoteParticipant | None: ...

class CallEnded(CallEvent):
    def __init__(self) -> None:
        """For an end that comes without the SFU ``call_ended``; its ``reason``
        is 0 (``CALL_ENDED_REASON_UNSPECIFIED``)."""
    @property
    def reason(self) -> int:
        """The protobuf ``CallEndedReason`` value."""

class CallingStateChanged(CallEvent):
    @property
    def state(self) -> CallingState: ...

class CoordinatorEvent(CallEvent):
    """A coordinator event of this call; ``name`` is its JSON ``type``."""

    @property
    def data(self) -> dict[str, Any]:
        """The whole JSON message."""

class ParticipantUpdated(CallEvent):
    @property
    def call_cid(self) -> str: ...
    @property
    def participant(self) -> RemoteParticipant: ...

class DominantSpeakerChanged(CallEvent):
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...

class AudioLevel:
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def level(self) -> float:
        """0.0 is silence, 1.0 the loudest."""
    @property
    def is_speaking(self) -> bool: ...

class AudioLevelChanged(CallEvent):
    @property
    def audio_levels(self) -> list[AudioLevel]: ...

class ConnectionQualityInfo:
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def connection_quality(self) -> int:
        """The protobuf ``ConnectionQuality`` value."""

class ConnectionQualityChanged(CallEvent):
    @property
    def connection_quality_updates(self) -> list[ConnectionQualityInfo]: ...

class ParticipantCountChanged(CallEvent):
    """Sent by the SDK when the SFU's participant count changes."""

    @property
    def total(self) -> int: ...
    @property
    def anonymous(self) -> int: ...

class Pin:
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...

class PinsChanged(CallEvent):
    @property
    def pins(self) -> list[Pin]: ...

class InboundVideoState:
    @property
    def user_id(self) -> str: ...
    @property
    def session_id(self) -> str: ...
    @property
    def track_type(self) -> TrackType: ...
    @property
    def paused(self) -> bool: ...

class InboundStateNotification(CallEvent):
    @property
    def inbound_video_states(self) -> list[InboundVideoState]: ...

class CallGrants:
    @property
    def can_publish_audio(self) -> bool: ...
    @property
    def can_publish_video(self) -> bool: ...
    @property
    def can_screenshare(self) -> bool: ...

class CallGrantsUpdated(CallEvent):
    @property
    def current_grants(self) -> CallGrants | None: ...
    @property
    def message(self) -> str: ...

class ICERestart(CallEvent):
    """Sent after the SDK has handled the SFU's ICE restart request."""

    @property
    def peer_type(self) -> int:
        """The protobuf ``PeerType`` value."""

class Codec:
    @property
    def payload_type(self) -> int: ...
    @property
    def name(self) -> str: ...
    @property
    def clock_rate(self) -> int: ...
    @property
    def encoding_parameters(self) -> str: ...
    @property
    def fmtp(self) -> str: ...

class VideoDimension:
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...

class AudioBitrate:
    @property
    def profile(self) -> int:
        """The protobuf ``AudioBitrateProfile`` value."""
    @property
    def bitrate(self) -> int: ...

class PublishOption:
    @property
    def track_type(self) -> TrackType: ...
    @property
    def codec(self) -> Codec | None: ...
    @property
    def bitrate(self) -> int: ...
    @property
    def fps(self) -> int: ...
    @property
    def max_spatial_layers(self) -> int: ...
    @property
    def max_temporal_layers(self) -> int: ...
    @property
    def video_dimension(self) -> VideoDimension | None: ...
    @property
    def id(self) -> int: ...
    @property
    def use_single_layer(self) -> bool: ...
    @property
    def audio_bitrate_profiles(self) -> list[AudioBitrate]: ...
    @property
    def degradation_preference(self) -> int:
        """The protobuf ``DegradationPreference`` value."""

class ChangePublishOptions(CallEvent):
    @property
    def publish_options(self) -> list[PublishOption]: ...
    @property
    def reason(self) -> str: ...

class AudioSender:
    @property
    def codec(self) -> Codec | None: ...
    @property
    def track_type(self) -> TrackType: ...
    @property
    def publish_option_id(self) -> int: ...

class VideoLayerSetting:
    @property
    def name(self) -> str: ...
    @property
    def active(self) -> bool: ...
    @property
    def max_bitrate(self) -> int: ...
    @property
    def scale_resolution_down_by(self) -> float: ...
    @property
    def codec(self) -> Codec | None: ...
    @property
    def max_framerate(self) -> int: ...
    @property
    def scalability_mode(self) -> str: ...

class VideoSender:
    @property
    def codec(self) -> Codec | None: ...
    @property
    def layers(self) -> list[VideoLayerSetting]: ...
    @property
    def track_type(self) -> TrackType: ...
    @property
    def publish_option_id(self) -> int: ...
    @property
    def degradation_preference(self) -> int:
        """The protobuf ``DegradationPreference`` value."""

class ChangePublishQuality(CallEvent):
    @property
    def audio_senders(self) -> list[AudioSender]: ...
    @property
    def video_senders(self) -> list[VideoSender]: ...

class ErrorDetails:
    """The protobuf ``models.Error`` inside the ``Error`` event."""

    @property
    def code(self) -> int:
        """The protobuf ``ErrorCode`` value."""
    @property
    def message(self) -> str: ...
    @property
    def should_retry(self) -> bool: ...

class EventsLagged(CallEvent):
    """Sent by the wrapper when this stream fell behind and lost ``skipped``
    events; the stream continues with the oldest event still buffered."""

    @property
    def skipped(self) -> int: ...

class Error(CallEvent):
    @property
    def error(self) -> ErrorDetails: ...
    @property
    def reconnect_strategy(self) -> int:
        """The protobuf ``WebsocketReconnectStrategy`` value."""

Event = (
    ParticipantJoined
    | ParticipantLeft
    | TrackPublished
    | TrackUnpublished
    | CallEnded
    | ParticipantUpdated
    | DominantSpeakerChanged
    | AudioLevelChanged
    | ConnectionQualityChanged
    | ParticipantCountChanged
    | PinsChanged
    | InboundStateNotification
    | CallGrantsUpdated
    | ICERestart
    | ChangePublishOptions
    | ChangePublishQuality
    | Error
    | EventsLagged
    | CallingStateChanged
    | CoordinatorEvent
)

class EventStream:
    """Ends when the call ends (``CallingStateChanged(LEFT)``), after the events
    that are already buffered, or at once if the call had already ended when
    the stream was created."""

    def __aiter__(self) -> EventStream: ...
    def __anext__(self) -> Awaitable[Event]: ...

class PcmFrame:
    @property
    def samples(self) -> npt.NDArray[np.int16]: ...
    @property
    def sample_rate(self) -> int: ...
    @property
    def channels(self) -> int: ...
    @property
    def pts(self) -> int | None:
        """The RTP timestamp of the first sample, on the 48 kHz Opus clock; it
        wraps at 2**32."""

class VideoFrame:
    @property
    def width(self) -> int: ...
    @property
    def height(self) -> int: ...
    @property
    def data(self) -> npt.NDArray[np.uint8]: ...
    @property
    def rtp_timestamp(self) -> int: ...

class VideoFrameStream:
    """Decoded frames of one video track. Each ``RemoteTrack.video_frames()``
    call gives an independent stream with its own copy of each frame. A stream
    that reads slower than the track gets the latest frame and skips the older
    ones. Ends when the track ends, or at once for a track with no video
    decoder."""

    def __aiter__(self) -> VideoFrameStream: ...
    def __anext__(self) -> Awaitable[VideoFrame]: ...

class RemoteTrack:
    @property
    def participant(self) -> RemoteParticipant: ...
    @property
    def track_type(self) -> TrackType: ...
    def next_pcm(self) -> Awaitable[PcmFrame | None]: ...
    def video_frames(self) -> VideoFrameStream:
        """A new stream of the frames decoded after this call. The track stays
        subscribed while one of its streams exists."""

class TrackStream:
    """All streams of one call share one queue. Ends when the call ends, or at
    once if the call had already ended when the stream was created."""

    def __aiter__(self) -> TrackStream: ...
    def __anext__(self) -> Awaitable[RemoteTrack]: ...

class LocalAudioTrack:
    def __init__(self, pcm_queue_capacity: float | None = None) -> None:
        """``pcm_queue_capacity``: the seconds of PCM that ``write_pcm`` queues
        (``None``: the SDK default, 60 s; below 0.02 raises ``MediaError``). A
        write above it drops the oldest samples and raises
        ``PcmQueueOverflowError``."""
    def write_pcm(
        self, samples: npt.NDArray[np.int16], sample_rate: int, channels: int
    ) -> Awaitable[None]:
        """Await each write before the next; writes that run at the same time
        can reach the SDK out of order."""
    def flush(self) -> None: ...

class LocalVideoTrack:
    @staticmethod
    def vp8() -> LocalVideoTrack: ...
    @staticmethod
    def vp9() -> LocalVideoTrack: ...
    def write_i420(
        self, data: npt.NDArray[np.uint8], width: int, height: int, duration: float
    ) -> Awaitable[None]:
        """Await each write before the next; writes that run at the same time
        can reach the SDK out of order."""

class Call:
    def join(self, user_id: str, create: bool = True) -> Awaitable[None]: ...
    def leave(self) -> Awaitable[None]: ...
    def session_id(self) -> Awaitable[str | None]: ...
    @property
    def calling_state(self) -> CallingState: ...
    def participants(self) -> list[RemoteParticipant]: ...
    def call_state(self) -> CallStateSnapshot: ...
    def sfu_events(self) -> EventStream:
        """SFU events. The SFU ``call_ended`` may not come: the SDK also leaves
        on the coordinator ``call.ended``."""
    def coordinator_events(self) -> EventStream:
        """``CoordinatorEvent`` for each coordinator event of this call."""
    def client_events(self) -> EventStream:
        """``CallingStateChanged``; ``LEFT`` is the reliable end of the call."""
    def tracks(self) -> TrackStream: ...
    def publish_audio(self, track: LocalAudioTrack) -> Awaitable[None]: ...
    def publish_video(self, track: LocalVideoTrack) -> Awaitable[None]: ...
    def publish_screen_share(self, track: LocalVideoTrack) -> Awaitable[None]:
        """The SFU accepts VP8 for screen share (``LocalVideoTrack.vp8()``)."""
    def stop_publish_audio(self, track: LocalAudioTrack) -> Awaitable[None]:
        """Stops the track: later writes raise ``IllegalStateError``. A track
        that is not published is ignored."""
    def stop_publish_video(self, track: LocalVideoTrack) -> Awaitable[None]:
        """Stops the track: later writes raise ``IllegalStateError``. A track
        that is not published is ignored."""
    def stop_publish_screen_share(self, track: LocalVideoTrack) -> Awaitable[None]:
        """Stops the track: later writes raise ``IllegalStateError``. A track
        that is not published is ignored."""
    def mute_track(self, track_type: TrackType) -> Awaitable[None]:
        """Keeps the published track; others get ``TrackUnpublished``."""
    def unmute_track(self, track_type: TrackType) -> Awaitable[None]:
        """Others get ``TrackPublished``; their track delivers frames again."""
    def update_subscriptions(self, config: SubscriptionConfig) -> Awaitable[None]:
        """The SDK applies ``config`` again on each participant and track event.
        Remote audio can arrive without a subscription: the SFU sends it."""

class Client:
    def __init__(
        self,
        api_key: str,
        api_secret: str | None = None,
        *,
        token: str | None = None,
        base_url: str | None = None,
        ws_url: str | None = None,
        log_bodies: bool = False,
        call_event_capacity: int | None = None,
    ) -> None:
        """Pass exactly one of ``api_secret`` or ``token`` (a user token); else
        ``ConfigError``. A token client joins only as the token's user.

        ``call_event_capacity``: the events that each event stream of a call
        buffers for a reader that falls behind (``None``: the SDK default, 256);
        0 raises ``ConfigError``."""
    def call(self, call_type: str, call_id: str) -> Call: ...
