# Migration Guide: aiortc transport → Rust Video SDK

This guide lists the breaking changes in `getstream.video.rtc` when the WebRTC
transport moves from aiortc to the Rust Video SDK
([stream-video-rust](https://github.com/GetStream/stream-video-rust)). It
compares with stream-py 4.1.0. The work is not released yet; this guide is
updated with each change.

## Overview

`ConnectionManager` (from `rtc.join(...)`) no longer connects to the call
itself. The Rust SDK, compiled into the private extension
`getstream._rust.bindings`, does the coordinator join, the SFU signaling, the
peer connections, the retries and the reconnects. `ConnectionManager` is a thin
layer on top of it.

The main changes for consumers:

- Event payloads are stream-py classes, not SFU protobuf messages.
- `ConnectionManager` emits the stable event names that the SDK can supply.
  The SFU transport events and the reconnection events are gone.
- Remote video is read from the track object of `track_added`. There is no
  `add_track_subscriber()`.
- Join errors are the Rust SDK errors, not `SfuJoinError`.
- Local recording is removed; use the server recording.

## Installation

The package now contains a native extension. Building from source (a git
checkout or an sdist) needs the Rust toolchain pinned in `rust-toolchain.toml`,
a C compiler, `cmake`, `pkg-config` and `libvpx`:

- macOS: `brew install libvpx cmake pkg-config`
- Debian/Ubuntu: `apt install libvpx-dev cmake pkg-config build-essential`

## Breaking Changes

### Connection state

| 4.1.0 | Now | Notes |
| --- | --- | --- |
| `connection.connection_state` returns `ConnectionState` | returns `CallingState` | Import it from `getstream.video.rtc`. |
| `ConnectionState.JOINED` | `CallingState.JOINED` | Values: `IDLE`, `JOINING`, `JOINED`, `RECONNECTING`, `MIGRATING`, `RECONNECTING_FAILED`, `LEFT`. |
| `ConnectionState.RINGING`, `ConnectionState.OFFLINE` | removed | stream-py never set these values. |
| `connection.connection_state = ...` | read only | The SDK owns the state. |
| event `connection.state_changed` with `{"old": ConnectionState, "new": ConnectionState}` | the same event and dict, with `CallingState` values | The first event is `{"old": IDLE, "new": JOINING}`. |

### Event payloads

Every SDK event is an instance of `CallEvent` and has `name`, the event name
it is emitted under. Import the classes from `getstream.video.rtc`, together
with `RemoteTrack`, `RemoteParticipant`, `TrackType`, `VideoFrameStream` and
`VideoFrame`.

| Event | 4.1.0 payload | Now |
| --- | --- | --- |
| `participant_joined` | `events_pb2.ParticipantJoined` | `ParticipantJoined`: `call_cid`, `participant` |
| `participant_left` | `events_pb2.ParticipantLeft` | `ParticipantLeft`: `call_cid`, `participant` |
| `track_published` | `events_pb2.TrackPublished` | `TrackPublished`: `user_id`, `session_id`, `track_type`, `participant` |
| `track_unpublished` | `events_pb2.TrackUnpublished` | `TrackUnpublished`: `user_id`, `session_id`, `track_type`, `cause`, `participant` |
| `call_ended` | `events_pb2.CallEnded` | `CallEnded`: `reason` |
| `participant_updated` | `events_pb2.ParticipantUpdated` | `ParticipantUpdated`: `call_cid`, `participant` |
| `dominant_speaker_changed` | `events_pb2.DominantSpeakerChanged` | `DominantSpeakerChanged`: `user_id`, `session_id` |
| `audio_level_changed` | `events_pb2.AudioLevelChanged` | `AudioLevelChanged`: `audio_levels` (`AudioLevel`: `user_id`, `session_id`, `level`, `is_speaking`) |
| `connection_quality_changed` | `events_pb2.ConnectionQualityChanged` | `ConnectionQualityChanged`: `connection_quality_updates` (`ConnectionQualityInfo`: `user_id`, `session_id`, `connection_quality`) |
| `pins_updated` | `events_pb2.PinsChanged` | `PinsChanged`: `pins` (`Pin`: `user_id`, `session_id`) |
| `inbound_state_notification` | `events_pb2.InboundStateNotification` | `InboundStateNotification`: `inbound_video_states` (`InboundVideoState`: `user_id`, `session_id`, `track_type`, `paused`) |
| `call_grants_updated` | `events_pb2.CallGrantsUpdated` | `CallGrantsUpdated`: `current_grants` (`CallGrants`: `can_publish_audio`, `can_publish_video`, `can_screenshare`), `message` |
| `ice_restart` | `events_pb2.ICERestart`, the SFU request | `ICERestart`: `peer_type`, sent after the SDK has handled the request |
| `participant_count_changed` | (not emitted) | new: `ParticipantCountChanged`: `total`, `anonymous`, when the SFU's count changes |
| `change_publish_options` | `events_pb2.ChangePublishOptions` | `ChangePublishOptions`: `publish_options` (`PublishOption`), `reason` |
| `change_publish_quality` | `events_pb2.ChangePublishQuality` | `ChangePublishQuality`: `audio_senders` (`AudioSender`), `video_senders` (`VideoSender` with `layers`: `VideoLayerSetting`) |
| `error` | `events_pb2.Error`: `error` (`models_pb2.Error`), `reconnect_strategy` | `Error`: `error` (`ErrorDetails`: `code`, `message`, `should_retry`), `reconnect_strategy` |
| `custom` | the coordinator JSON `dict` | unchanged |
| `audio` | `PcmData`, 48 kHz mono `s16`; `participant` is `models_pb2.Participant` | `PcmData`, 48 kHz mono `s16`; `participant` is a `RemoteParticipant`; `pts` (the RTP timestamp), `dts` (`None`) and `time_base` (`1/48000`) as in 4.1.0 |

`ConnectionManager` reads every remote audio track (`AUDIO` and
`SCREEN_SHARE_AUDIO`) to emit `audio`. Do not also call `next_pcm()` on these
tracks: each frame goes to one reader only.

Field changes:

- `participant` is a `RemoteParticipant` with the fields of the protobuf
  `Participant`, except `track_lookup_prefix`: use `session_id` to identify a
  participant session.
- `participant.joined_at` is a `float`, the Unix time in seconds (or `None`),
  not a protobuf `Timestamp`. Use
  `datetime.fromtimestamp(joined_at, timezone.utc)` for a `datetime`.
- `participant.custom` is a `dict`, not a protobuf `Struct`; numbers are
  `float`, as with `MessageToDict`.
- The protobuf field `type` of `TrackPublished` and `TrackUnpublished` is now
  `track_type`.
- `track_type` and `published_tracks` use the `TrackType` enum (`AUDIO`,
  `VIDEO`, `SCREEN_SHARE`, `SCREEN_SHARE_AUDIO`, `UNSPECIFIED`), not
  `models_pb2.TrackType` integers.
- The other protobuf enum fields keep their `int` values, as in 4.1.0:
  `participant.connection_quality`, `participant.source`,
  `TrackUnpublished.cause`, `CallEnded.reason`.
- `TrackPublished.participant`, `TrackUnpublished.participant` and
  `CallGrantsUpdated.current_grants` are `None` when the SFU does not send
  them; in 4.1.0 they were always an object.
- `InboundVideoState.track_type`, `PublishOption.track_type`,
  `AudioSender.track_type` and `VideoSender.track_type` use the `TrackType`
  enum.
- `codec` (on `PublishOption`, `AudioSender`, `VideoSender`,
  `VideoLayerSetting`) and `PublishOption.video_dimension` are `None` when the
  SFU does not send them.
- `PublishOption` and `VideoSender` also have `degradation_preference` (`int`),
  from a newer SFU protocol than 4.1.0.
- The nested error of the `Error` event is an `ErrorDetails`; the data path
  (`event.error.code`) is the same as in 4.1.0. `Error` is an event class, not
  an exception.
- `ICERestart` arrives after the SDK has handled the SFU's restart request;
  in 4.1.0 it was the request itself.
- A `call_ended` after a coordinator end carries `reason` 0
  (`CALL_ENDED_REASON_UNSPECIFIED`).

### Events that are no longer emitted

| 4.1.0 event | Now |
| --- | --- |
| `subscriber_offer`, `publisher_answer`, `ice_trickle`, `join_response`, `health_check_response`, `go_away`, `participant_migration_complete` | Not emitted. The SDK handles these SFU transport events itself. For the participant count of `health_check_response`, use `participant_count_changed`. |
| `connection_lost`, `reconnection_success`, `reconnection_failed` | Not emitted. The SDK reconnects by itself; watch `connection.state_changed` (`RECONNECTING`, `MIGRATING`, `RECONNECTING_FAILED`). |
| coordinator events other than `custom` | Not emitted, as in 4.1.0. They are logged at DEBUG. |

### Remote tracks

| 4.1.0 | Now | Notes |
| --- | --- | --- |
| `track_added` with `(track_id, kind, user)` | `track_added` with a `RemoteTrack` | `track.participant`, `track.track_type`. |
| `connection.subscriber_pc.add_track_subscriber(track_id)` | the `RemoteTrack` itself | `await track.next_pcm()` gives a `PcmFrame` (48 kHz mono `int16` numpy samples), or `None` when the track ends. `track.video_frames()` gives a `VideoFrameStream`: `async for frame in track.video_frames()` gives each `VideoFrame` (I420 `uint8` numpy data) until the track ends. |
| each `add_track_subscriber()` call returns a new aiortc relay proxy, and each proxy gets the frames independently | each `video_frames()` call returns a new independent `VideoFrameStream` | Each stream gets its own copy of each frame. A stream that reads slower than the track skips to the latest frame. Two loops on one stream share its frames. The result is not an aiortc track. |
| `connection.republish_tracks()` | not needed; it does nothing | `track_added` also arrives for the tracks of participants who joined before you. |
| `track_published` for tracks that existed before the join (from `republish_tracks()`) | not emitted | Use `track_added`. |

Behavior of a track object:

- `ConnectionManager` keeps no reference to a track. When the last reference to
  the track and to its `VideoFrameStream`s is dropped, the SDK unsubscribes
  from that track.
- After a remote mute and unmute (`track_unpublished`, then
  `track_published`), no new `track_added` arrives. The same track object
  delivers frames again. Keep the track object during a mute: if you drop it,
  the track does not come back until the participant rejoins.
- A track ends (`None`, or the end of its `VideoFrameStream`s) when its
  participant leaves, when this client leaves, or when this client rejoins
  with a new session; after a rejoin a new `track_added` arrives.

### Joining, waiting and leaving

| 4.1.0 | Now | Notes |
| --- | --- | --- |
| `participant_joined` only for participants who join after you | also for the participants already in the call at join | Handlers registered before `__aenter__()` get them. |
| `wait()` returns after `leave()` | also returns when the call ends | |
| `call_ended` only from the SFU | also when the coordinator ends the call | Emitted once. After a coordinator end, the payload is a `CallEnded` that stream-py makes. |
| `connect()` retries with `max_join_retries` and other SFUs | the SDK retries | `max_join_retries` has no effect. |
| `rtc.join(call, user_id, **kwargs)` passes `kwargs` to the join request | `kwargs` are ignored | |
| `user_id=None` raises `ValueError` | raises `TypeError` | |
| `drain_video_frames` | no effect | |

### Publishing audio

- `add_tracks(audio=track)` accepts any aiortc audio track. The SDK paces the
  frames and always sends mono: stereo frames are mixed down.
- `AudioStreamTrack` has a new setting `pace`, `False` by default:
  - `pace=False`: `recv()` returns the next queued frame at once and waits for
    the next `write()` when the queue is empty. This is the right setting for
    `add_tracks`.
  - `pace=True`: the 4.1.0 behavior, one frame per 20 ms and silence when the
    queue is empty. Code that passes an `AudioStreamTrack` to its own aiortc
    connection needs `pace=True`.
- `AudioStreamTrack.wait_for_flush()` is new: it returns at the next
  `flush()`. `add_tracks` uses it, so `flush()` also drops the audio that is
  already queued for sending.
- When more audio is queued than `audio_buffer_size_ms`, the oldest audio is
  dropped, as in 4.1.0, with an "Audio buffer overflow" DEBUG record from
  `getstream.video.rtc.audio_forwarder`. `add_tracks` raises `MediaError` for
  an `audio_buffer_size_ms` below 20 (one frame).
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`. In 4.1.0 the packets only stopped.

### Publishing video

- `add_tracks(video=track)` accepts any aiortc video track; the track paces
  itself, as in 4.1.0.
- The video is sent as VP9, the SFU's default publish option for camera
  video. 4.1.0 sent H264 (aiortc without VP8).
- The whole track has the size of its first frame. Later frames of another
  size are scaled to it, and an odd width or height is raised to the next
  even value. In 4.1.0 each frame kept its own size.
- The frame duration comes from the `pts` difference; frames without `pts`
  count as 1/30 s.
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`.
- A later `add_tracks(video=new_track)` puts the new track on the same sender:
  other participants get its frames on their existing `RemoteTrack`. If it is
  called before the stopped track is unpublished, it raises `MediaError`.

### Handlers, failures and lost events

- A handler that raises is logged at ERROR with its traceback; it does not
  stop the other events, `wait()` or `leave()`. This is true for
  `ConnectionManager` and `participants_state`. `emit(event, *args,
  unsafe=True)` raises the handler's exception instead.
- If `connect()` fails or is cancelled after the SDK join, it leaves the call
  before it raises.
- If the event loop is blocked long enough that `ConnectionManager` falls
  behind an SDK event stream (1024 buffered events per stream), the lost events are
  skipped with a `stream.rtc.events.lagged` WARNING (field `skipped`), and
  `participants_state` is filled again from the SDK's participant list.

### `participants_state`

- `get_participants()` and the `map()` handlers give a list of
  `RemoteParticipant`, not `models_pb2.Participant`. The list includes this
  participant (the agent) and is keyed by `session_id`.
- After the join, the list is filled from the SDK's participants; then
  `participant_joined` and `participant_left` update it. `participant_updated`
  does not change it, as in 4.1.0.
- `get_user_from_track_id()`, `get_stream_id_from_track_id()` and
  `set_track_stream_mapping()` are removed: they mapped aiortc track ids. A
  `RemoteTrack` carries its `participant`.

### Subscriptions

`subscription_config` of `rtc.join` works as in 4.1.0 (`default`,
`role_filters`, `max_subscriptions`, separate video and screen share sizes).
The SDK applies it again on each participant and track event. Differences in
rare cases:

- A participant with two roles that both have a rule in `role_filters` gets
  the rule of the first role in its `roles` list. In 4.1.0 the choice was not
  defined.
- `max_subscriptions=0` subscribes to no tracks. In 4.1.0 it subscribed to one.
- When no track matches, the SDK sends an empty subscription list to the SFU.
  4.1.0 never sent an empty list.
- The SFU sends remote audio without a request, also without a
  `subscription_config`, as in 4.1.0. It is not verified whether a config
  without `TRACK_TYPE_AUDIO` stops it.

### Errors

| 4.1.0 | Now |
| --- | --- |
| `SfuJoinError`, `SfuConnectionError` | Errors from `getstream._rust`, all subclasses of `RustError`: |
| | `ApiError` (coordinator HTTP error: `code`, `status_code`, `message`, `unrecoverable`) |
| | `CoordinatorError` (coordinator connection or authentication failed) |
| | `PermissionDeniedError` (`capability`), `IllegalStateError`, `MediaError`, `PcmQueueOverflowError` |
| | `RtcError` (other RTC failures), `ConfigError` (invalid client configuration) |

### `ConnectionManager` attributes

These attributes are no longer set:

- `join_response` stays `None`.
- `session_id` is a random UUID, not the SFU session id.
- `running` stays `False`.
- `ws_client`, `publisher_pc`, `subscriber_pc`, `twirp_signaling_client` and
  `stats_reporter` are not set.

### Logging

- The transport logs come from the SDK through the `getstream` logger and its
  children (for example `getstream.rtc.join.lifecycle`), not from the `aiortc`
  and `aioice` loggers. Records of other Rust crates (for example
  `getstream.webrtc_ice`) are forwarded at `WARNING` and above.
- `connect()` reads the effective level of the `getstream` logger. A later
  level change takes effect at the next `connect()`.

### Network

- TURN works only over UDP. Networks that allow only TCP or TLS (for example
  port 443 only) cannot connect; aiortc supported TURN over TCP and TLS.
- A user token with an `expiration` cannot be refreshed. If it expires during
  the call, the next rejoin or migration fails and the state becomes
  `RECONNECTING_FAILED`. Tokens from `create_token()` without `expiration` do
  not expire.

### Local recording

Local recording is removed. stream-video-js, the Go SDK and the Rust SDK do
not have local call recording either.

| 4.1.0 | Now |
| --- | --- |
| `connection.start_recording()`, `stop_recording()`, `is_recording`, `get_recording_status()` | removed |
| `connection.recording_manager` and the module `getstream.video.rtc.recording` (`RecordingManager`, `RecordingType`, `RecordingConfig` and the recorder classes) | removed |
| the `recording_manager` events `recording_started`, `recording_stopped`, `user_recording_started`, `user_recording_stopped`, `composite_recording_started`, `composite_recording_stopped`, `recording_error` | removed |

To record a call, use the server recording: `call.start_recording()` and
`call.stop_recording()`. The `call.recording_ready` event tells when a file is
ready. To write files locally, read the `audio` event (`PcmData` with
`participant`, `pts` and `time_base`) and `track.video_frames()`.
