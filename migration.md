# Migration Guide: aiortc transport → Rust Video SDK

This guide lists the breaking changes in `getstream.video.rtc` when the WebRTC
transport moves from aiortc to the Rust Video SDK
([stream-video-rust](https://github.com/GetStream/stream-video-rust)). It
compares with stream-py 4.1.0; the `getstream.video.rtc` code of 6.1.1 is the
same. The work is not released yet; this guide is updated with each change.

## Overview

`ConnectionManager` (from `rtc.join(...)`) no longer connects to the call
itself. The Rust SDK, compiled into the separate package `getstream-rtc`
(import name `getstream_rtc`), does the coordinator join, the SFU signaling,
the peer connections, the retries and the reconnects. `ConnectionManager` is a thin
layer on top of it.

The main changes for consumers:

- Event payloads are `getstream_rtc` classes (re-exported by
  `getstream.video.rtc`), not SFU protobuf messages.
- `ConnectionManager` emits the stable event names that the SDK can supply.
  The SFU transport events and the reconnection events are gone.
- Remote video is read from the track object of `track_added`. There is no
  `add_track_subscriber()`.
- Join errors are the Rust SDK errors, not `SfuJoinError`.
- Local recording is removed; use the server recording.

## Installation

The `webrtc` extra now also installs `getstream-rtc` (import name
`getstream_rtc`), a separate package that contains the native extension.
`getstream` itself stays pure Python. Building `getstream-rtc` from source (a
git checkout, or its sdist on a platform without a wheel) needs the Rust
toolchain pinned in `getstream-rtc/rust-toolchain.toml`, a C compiler, `cmake`,
`pkg-config`, `libvpx` and libclang:

- macOS: `brew install libvpx cmake pkg-config` (libclang comes with Xcode)
- Debian/Ubuntu: `apt install libvpx-dev libclang-dev cmake pkg-config build-essential`

The `webrtc` extra no longer installs `scipy`, `soundfile`, `websockets`,
`websocket-client`, `structlog`, `tenacity` and `ping3`; no stream-py code uses
them. Code that imports one of them must declare it itself.

## Breaking Changes

### Connection state

| 4.1.0 | Now | Notes |
| --- | --- | --- |
| `connection.connection_state` returns `ConnectionState` | returns `CallingState` | Import it from `getstream.video.rtc`. |
| `ConnectionState.JOINED` | `CallingState.JOINED` | Values: `IDLE`, `JOINING`, `JOINED`, `RECONNECTING`, `MIGRATING`, `RECONNECTING_FAILED`, `LEFT`. |
| `ConnectionState.RINGING`, `ConnectionState.OFFLINE` | removed | stream-py never set these values. |
| `ConnectionState` is an `Enum` with string values (`"joined"`) | `CallingState` is not an `Enum` | The members have no `name` or `value`, cannot be hashed (as `dict` keys or in a `set`) and cannot be iterated. They compare equal to their `int` values. Compare with the members: `state == CallingState.JOINED`. |
| `connection.connection_state = ...` | read only | The SDK owns the state. |
| event `connection.state_changed` with `{"old": ConnectionState, "new": ConnectionState}` | the same event and dict, with `CallingState` values | The first event is `{"old": IDLE, "new": JOINING}`. |
| after a failed join, `connection.state_changed` with `{"old": JOINING, "new": IDLE}` | no `connection.state_changed` after `connect()` fails | `connect()` stops its event tasks and leaves the call before it raises. |

### Event payloads

Every SDK event is an instance of `CallEvent` and has `name`, the event name
it is emitted under. Import the event classes from `getstream.video.rtc`,
together with `RemoteTrack`, `RemoteParticipant`, `TrackType`,
`VideoFrameStream` and `VideoFrame`. The nested classes in the table below (for
example `AudioLevel`, `PublishOption` and `ErrorDetails`) are not exported; you
get them from the event attributes. Import `PcmFrame` and the errors from
`getstream_rtc`.

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
  `models_pb2.TrackType` integers. As with `CallingState`, the members are not
  `Enum` members and cannot be hashed: `set(participant.published_tracks)`
  raises `TypeError`. They compare equal to the `models_pb2.TrackType`
  integers.
- `RemoteParticipant` compares by identity, and each read of a `participant`
  attribute gives a new object, so `track.participant == track.participant` is
  `False`. Compare `session_id`. In 4.1.0 the protobuf `Participant` compared
  by value.
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
  (`CALL_ENDED_REASON_UNSPECIFIED`). `call_ended` is emitted once, by the first
  event stream that reports the end. If `ConnectionManager` reads the `LEFT`
  state before the SFU's `call_ended` (for example while SFU events wait to be
  read), `reason` is 0 also after an SFU end.

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
| `connection.republish_tracks()` | removed; not needed | `track_added` also arrives for the tracks of participants who joined before you. |
| `track_published` for tracks that existed before the join (from `republish_tracks()`) | not emitted | Use `track_added`. |

Behavior of a track object:

- `ConnectionManager` keeps a reference only to remote audio tracks (`AUDIO`
  and `SCREEN_SHARE_AUDIO`): it reads them for the `audio` event until they
  end. When the last reference to a video track and to its
  `VideoFrameStream`s is dropped, the SDK unsubscribes from that track.
- After a remote mute and unmute (`track_unpublished`, then
  `track_published`), no new `track_added` arrives. The same track object
  delivers frames again. If you drop a video track object during the mute, a
  new `track_added` with a new track object arrives when the media flows again
  after the `track_published`. A video track that you drop while it is
  published does not come back until it is published again.
- Remote H.264 video is not supported: the SDK decodes only VP8 and VP9. A
  participant that publishes only H.264 (for example RTMP or SRT ingress, or an
  app that chooses H.264 as its codec) gives no video track. 4.1.0 decoded
  H.264 with aiortc.
- A track ends (`None`, or the end of its `VideoFrameStream`s) when its
  participant leaves, when this client leaves, or when this client rejoins
  with a new session; after a rejoin a new `track_added` arrives.

### Joining, waiting and leaving

| 4.1.0 | Now | Notes |
| --- | --- | --- |
| `participant_joined` only for participants who join after you | also for the participants already in the call at join | Handlers registered before `__aenter__()` get them. |
| `wait()` returns after `leave()` | also returns when the call ends | It does not return at `RECONNECTING_FAILED`; call `leave()`. |
| `call_ended` only from the SFU | also when the coordinator ends the call | Emitted once. After a coordinator end, the payload is a `CallEnded` that stream-py makes. |
| `connect()` retries with `max_join_retries` and other SFUs | the SDK retries | The `max_join_retries` argument is removed. |
| `rtc.join(call, user_id, **kwargs)` passes `kwargs` to the join request | `rtc.join(call, user_id, create, subscription_config)` | Other keyword arguments raise `TypeError`. |
| `user_id=None` raises `ValueError` | raises `TypeError` | `user_id` of `rtc.join` and `ConnectionManager` has no default now. A call without an id raises `TypeError`. |
| `drain_video_frames` | removed | The SDK decodes a remote track only while it is read. |
| `connect()` again on the same `ConnectionManager` | not supported | After `leave()`, or after a `connect()` that failed or was cancelled, a new `connect()` joins the call, but no events and no tracks arrive, and `wait()` returns at once. Use a new `rtc.join()` for each join. |
| `add_tracks()` before `connect()` logs an error and returns | raises `IllegalStateError` | Call `add_tracks()` after the join. |

### Publishing audio

- `add_tracks(audio=track)` accepts aiortc audio tracks that give packed `s16`
  frames, as `AudioStreamTrack` does. The SDK paces the frames and always
  sends mono: stereo frames are mixed down.
- Frames in other formats are not converted. Float frames (`fltp`) stop the
  forwarding and unpublish the track; planar stereo frames (`s16p`) are sent
  garbled. In 4.1.0 the aiortc Opus encoder converted every format to `s16`.
- The SDK takes the sample rate of the first frame of a published track. A
  later frame at another rate raises `PcmRateMismatchError` (`expected`,
  `actual`), which stops the forwarding and unpublishes the track.
  `AudioStreamTrack` always gives frames at its own `sample_rate`.
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
  an `audio_buffer_size_ms` below 20 (one frame) and `ValueError` for a
  negative value.
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`. In 4.1.0 the packets only stopped.
- A new `add_tracks(audio=new_track)` replaces the published audio track: the
  earlier track is unpublished first, also while it is still live. In 4.1.0
  each call added one more audio track.

### Resampling

`FrameResampler`, and so `AudioStreamTrack.write()`, resamples with the SDK's
windowed-sinc filter (`getstream_rtc.StreamResampler`), not with PyAV
(libswresample). The filter removes much more of the images and aliases: from
16 kHz to 48 kHz, the image of a 7 kHz tone is at −103 dB, with PyAV at
−38 dB. The differences from 6.1.1:

- Audio at another rate than the output rate is delayed by 128 input frames:
  8 ms at 16 kHz, 5.3 ms at 24 kHz, 2.9 ms at 44.1 kHz. The delay is silence
  at the start of the audio and again after each `flush()`. PyAV added no
  silence.
- `flush()` and `write(pcm, final=True)` give the audio that the filter holds
  and about 132 input frames of near-silence after it: 16 ms in all at
  16 kHz. PyAV gave 1 ms at 16 kHz. A change of the input rate also adds the
  held audio and this near-silence.
- Mono input to a stereo `FrameResampler` is copied to each channel at full
  level. PyAV lowered it by 3 dB. Stereo input to mono is averaged, as in
  6.1.1.
- The channel count changes only from mono or to mono; another change raises
  `ValueError`. PyAV converted between all layouts.
- `FrameResampler` accepts only the output format `s16`; another `format`
  raises `ValueError`.
- `PyAVResampler` is removed. For a stream of `PcmData`, use
  `FrameResampler`.

### Publishing video

- `add_tracks(video=track)` accepts any aiortc video track; the track paces
  itself, as in 4.1.0.
- The video is sent as VP9, the SFU's default publish option for camera
  video. 4.1.0 sent H264 (aiortc without VP8).
- The environment variables `STREAM_PATCH_AIORTC_BITRATES` and
  `STREAM_PATCH_AIORTC_H264_PRESET` have no effect: the aiortc encoder patches
  are removed. The SDK encoder starts at its default bitrate and follows the
  SFU's publish quality settings (`change_publish_quality`).
- The whole track has the size of its first frame. Later frames of another
  size are scaled to it, and an odd width or height is raised to the next
  even value. In 4.1.0 each frame kept its own size.
- The frame duration comes from the `pts` difference; frames without `pts`
  count as 1/30 s.
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`.
- A new `add_tracks(video=new_track)` replaces the published video track: the
  earlier track is unpublished first, also while it is still live. Other
  participants get the new frames on their existing `RemoteTrack`. In 4.1.0
  each call added one more video track.

### Handlers, failures and lost events

- A handler that raises does not stop the other events, `wait()` or
  `leave()`. pyee passes its exception to the `error` event. Without an `error`
  handler, the exception is logged at ERROR with its traceback, with the
  message "A 'error' handler failed". With an `error` handler (for example for
  the SFU `Error` event), that handler gets the exception, and nothing is
  logged. This is true for `ConnectionManager` and `participants_state`.
  `emit(event, *args, unsafe=True)` does not raise the handler's exception
  either.
- If `connect()` fails or is cancelled after the SDK join, it leaves the call
  before it raises.
- If the event loop is blocked long enough that `ConnectionManager` falls
  behind an SDK event stream (1024 buffered events per stream), the lost events are
  skipped with a `stream.rtc.events.lagged` WARNING (field `skipped`), and
  `participants_state` is filled again from the SDK's participant list.
- If the event loop is blocked long enough that more than 64 new remote tracks
  wait to be read, the SDK unsubscribes from the tracks that do not fit. Then
  `ConnectionManager` emits no `track_added` and no `audio` for new tracks
  until the end of the call, and `leave()` raises `RtcError`.

### `participants_state`

- `get_participants()` and the `map()` handlers give a list of
  `RemoteParticipant`, not `models_pb2.Participant`. The list includes this
  participant (the agent) and is keyed by `session_id`. The
  `participant_joined` and `participant_left` events of `participants_state`
  also give a `RemoteParticipant`.
- After the join, the list is filled from the SDK's participants; then
  `participant_joined` and `participant_left` update it. `participant_updated`
  does not change it, as in 4.1.0.
- `track_published` does not change the list. In 4.1.0 it replaced the
  participant (with its new `published_tracks`) and called the `map()`
  handlers. Now `published_tracks` in the list keeps the value from the join
  or from `participant_joined`.
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
- When no track matches, the SDK sends an empty subscription list to the SFU.
  4.1.0 never sent an empty list.
- The SFU sends remote audio without a request, also without a
  `subscription_config`, as in 4.1.0. It is not verified whether a config
  without `TRACK_TYPE_AUDIO` stops it.

### Errors

| 4.1.0 | Now |
| --- | --- |
| `SfuJoinError`, `SfuConnectionError` | Errors from `getstream_rtc`, all subclasses of `RustError`: |
| | `ApiError` (coordinator HTTP error: `code`, `status_code`, `message`, `unrecoverable`) |
| | `CoordinatorError` (coordinator connection or authentication failed) |
| | `PermissionDeniedError` (`capability`), `IllegalStateError`, `MediaError`, `PcmQueueOverflowError`, `PcmRateMismatchError` (`expected`, `actual`) |
| | `RtcError` (other RTC failures), `ConfigError` (invalid client configuration) |

`rtc.join()` and `ConnectionManager()` create the SDK client. For an invalid
client configuration they raise `ConfigError`, and for other client errors
`RustError` itself, before `connect()`.

### `ConnectionManager` attributes

These attributes and methods of the aiortc transport are removed:

- `join_response`, `session_id`, `running`, `local_sfu`, `kwargs`.
- `ws_client`, `publisher_pc`, `subscriber_pc`, `publisher_negotiation_lock`,
  `subscriber_negotiation_lock`, `twirp_signaling_client`, `twirp_context`,
  `stats_reporter`, `tracer`, `reconnector`.
- `pc_id()`, `sfu_id()`, `republish_tracks()`.

`call`, `user_id`, `create`, `participants_state` and `connection_state` stay.

### Removed modules and names

The SDK does the coordinator join, chooses the SFU and owns the peer
connections, so the aiortc transport code is removed:

- From `getstream.video.rtc`: `join_call_coordinator_request`,
  `JoinCallRequest`, `JoinCallResponse`, `ServerCredentials`, `Credentials`,
  `discover_location`, `HTTPHintLocationDiscovery`, `HEADER_CLOUDFRONT_POP`,
  `FALLBACK_LOCATION_NAME`, `STREAM_PROD_URL`.
- The modules `peer_connection`, `pc`, `encoders_patches`, `signaling`,
  `twirp_client_wrapper`, `connection_utils` (with `SfuJoinError`,
  `SfuConnectionError` and its `ConnectionState`), `models`, `reconnection`,
  `network_monitor`, `stats_reporter`, `stats_tracer`, `tracer`,
  `coordinator` and `location_discovery` of `getstream.video.rtc`.
- `getstream.video.rtc.tracks.SubscriptionManager`, and the name `TrackType`
  that `tracks` imported from `models_pb2`. `SubscriptionConfig` and
  `TrackSubscriptionConfig` stay. For `TrackSubscriptionConfig.track_types`,
  use the `models_pb2` constants (for example `models_pb2.TRACK_TYPE_VIDEO`).
- From `getstream.video.rtc.track_util`: `patch_sdp_offer`,
  `fix_sdp_msid_semantic`, `fix_sdp_rtcp_fb`, `parse_track_stream_mapping`,
  `BufferedMediaTrack`, `VideoFrameTracker`, `detect_video_properties`,
  `AudioTrackHandler`, `PyAVResampler` (see "Resampling"). `PcmData`,
  `AudioFormat`, `Resampler` and `FrameResampler` stay.

### Logging

- The transport logs come from the SDK through the `getstream` logger and its
  children (for example `getstream.rtc.join.lifecycle`), not from the `aiortc`
  and `aioice` loggers. Records of other Rust crates (for example
  `getstream.webrtc_ice`) are forwarded at `WARNING` and above.
- `connect()` reads the effective level of the `getstream` logger. A later
  level change takes effect at the next `connect()`.

### Telemetry

- Only the OpenTelemetry spans `connect`, `leave` and `rtc.add_tracks` stay.
  The spans of the aiortc transport steps are removed, for example
  `coordinator-setup`, `coordinator-join-call`, `sfu-signaling-ws-connect`,
  `rtc.on_subscriber_offer`, `rtc.publisher_pc.create_offer` and
  `signaling.twirp.<method>`.

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

## Other bugs

The code review of this branch found these issues in addition to the changes
that the sections above describe. They are not addressed yet. Each item gives
its location, its severity, and whether the review confirmed it in the code or
in a test run ("confirmed") or found only its cause ("not confirmed").

### Rust bindings

- `getstream-rtc/rustsrc/tracks.rs:87-91` (medium, confirmed): when the call
  ends, the `TrackStream` stops, but the unread tracks stay in the
  `TrackQueue`, which lives as long as the `Call`. After a new join on the same
  `Call`, a new `TrackStream` first returns the dead tracks of the old session.
  Until they are read, these tracks keep their decoders.
- `getstream-rtc/rustsrc/logging.rs:244-256` (medium, not confirmed):
  `SINK.set` and the thread spawn come before `set_global_default` and
  `LogTracer::init`. If another extension has already set a global `tracing`
  subscriber or `log` logger, `import getstream_rtc` raises. A second import
  then succeeds with no subscriber, and the Rust logs are lost.
- `getstream-rtc/rustsrc/tracks.rs:93` (low, not confirmed): if Python cancels
  the awaitable after the Rust future is complete (for example
  `asyncio.wait_for(anext(tracks), timeout)`), the `RemoteTrack` is dropped and
  the SDK unsubscribes from it. The track is lost until it is published again.
  `EventStream` and `next_pcm()` can lose one item in the same way.
- `getstream-rtc/rustsrc/logging.rs:291-309` (low, not confirmed):
  `configure_logging` waits for the forwarding thread. If a handler or filter
  of the `getstream` logger calls it, the forwarding thread waits for itself.
  If the caller holds `logging._lock` or a handler lock, the forwarding thread
  waits for that lock. No caller in the repository does this.
- `getstream-rtc/rustsrc/logging.rs:278` (low, confirmed):
  `SINK.get().expect(...)` in a `#[pyfunction]` breaks the AGENTS.md rule
  against `expect` in library code. It cannot fail at this time.
- `getstream-rtc/rustsrc/call_end.rs:38` (low, confirmed): the watcher ignores
  `RecvError::Lagged`, so a skipped `LEFT` or `JOINING` state is never applied,
  and the streams can end at the wrong time.
- Python calls from Rust that AGENTS.md does not document (low, confirmed):
  `atexit.register` (`logging.rs:259-262`), `PyObject_Repr` in each `__repr__`
  (`repr.rs:7`) and `import_exception!` of `getstream_rtc.errors`
  (`errors.rs:4-12`). Also, `logging.rs:349` imports `getstream_rtc.logging`
  again for each record.

### Python and type stubs

- `getstream-rtc/getstream_rtc/_bindings.pyi:17,26` (medium, confirmed): the
  stub declares `CallingState(Enum)` and `TrackType(Enum)`. Type checkers accept
  `hash()`, `.name`, `.value` and iteration, which fail at runtime (see
  "Connection state").
- `getstream/video/rtc/connection_manager.py:280-286` and `:185` (low, not
  confirmed): `leave()` handles no exception. If `call.leave()` or a task in
  `gather()` raises, the audio and publish tasks are not cancelled, and
  `__aexit__` replaces the exception of the `async with` body. In `connect()`,
  a `call.leave()` that raises replaces the join error. One confirmed cause is
  the track queue overflow (see "Handlers, failures and lost events").
- `getstream/video/rtc/connection_manager.py:351-371` (low, not confirmed):
  `_stop_forwarding()` can cancel a task that is already in its
  `finally: await stop_publish(...)` because its source ended. The SDK stop is
  then dropped, and the old track can stay published. Two concurrent
  `add_tracks(audio=...)` calls overwrite `_publish_tasks["audio"]`, so the
  first forwarder is never cancelled.
- `getstream/video/rtc/audio_forwarder.py:69-72` (low, not confirmed):
  `flush()` can run while a `write_pcm()` of an earlier frame is in progress.
  That 20 ms frame then plays after a barge-in, or the first new frame is
  dropped.
- `getstream/video/rtc/video_forwarder.py:41-48` (low, not confirmed): the
  `duration` given for a frame is the gap since the previous frame, so each
  value is one frame late. This is wrong if the SDK reads it as the duration of
  the current frame.
- `getstream/video/rtc/connection_manager.py:258` (low, confirmed):
  `_emit_audio` reads `track.participant` for each 20 ms frame, and each read
  allocates a new `RemoteParticipant`.
- `getstream-rtc/getstream_rtc/__init__.py:14-52` (low, confirmed): 14 classes
  of `_bindings` are not exported at the package root: `AudioBitrate`,
  `AudioLevel`, `AudioSender`, `CallGrants`, `CallStateSnapshot`, `Codec`,
  `ConnectionQualityInfo`, `ErrorDetails`, `InboundVideoState`, `Pin`,
  `PublishOption`, `VideoDimension`, `VideoLayerSetting`, `VideoSender`.
  AGENTS.md says that the root exports every class.
- `getstream-rtc/getstream_rtc/_bindings.pyi:384` (low, confirmed): the stub
  declares an `Event` alias that does not exist at runtime.
- `getstream-rtc/getstream_rtc/_bindings.pyi:465-469` (low, confirmed): the
  docstring says only that a capacity below 0.02 s raises `MediaError`. A
  negative or NaN value raises `ValueError`.
- `getstream/video/rtc/audio_forwarder.py:50-51` (low, confirmed): the comment
  says that the aiortc Opus encoder accepts only `s16`. It converts every
  format to `s16` (see "Publishing audio").
- `getstream/video/rtc/connection_manager.py:67,175` (low, confirmed): the
  comments "as in the aiortc version" describe the migration, not the code.

### Tests

- `getstream-rtc/tests/test_logging.py:88-98` (medium, confirmed):
  `test_no_records_after_logging_is_stopped` cannot fail. The autouse fixture
  `forward_sdk_logs` forwards at INFO, and the `pcm_queue_overflow` record is
  DEBUG, so Rust filters it also while forwarding is on. Without the
  `configure_logging(None, logging.NOTSET)` call, the test still passes.
- `getstream-rtc/tests/test_call.py:214-223` (low, not confirmed):
  `test_cancelled_join_allows_new_join` cancels the join after 0.1 s. If the
  join completes faster, `pytest.raises(CancelledError)` fails.
- `async for ... break` loops without `else: pytest.fail(...)` (low, not
  confirmed): `getstream-rtc/tests/test_call.py:295, 317, 337, 346, 372, 397,
  415, 479, 501, 521, 542, 558, 712` and
  `tests/rtc/test_connection_manager.py:516, 525`. If the stream ends before the
  expected event, `test_calling_state_changed_to_joined` (397) and
  `test_track_published` (479) pass with no assertion. The other tests assert
  on the last event.
- Writer tasks that are cancelled and never awaited (low, not confirmed):
  `getstream-rtc/tests/test_call.py:79-81, 97-99, 367/370, 382/385` and
  `tests/rtc/test_connection_manager.py:84-86`. If `write_pcm` or
  `write_i420` raises, the receiving test waits for the 120 s timeout and does
  not show the cause.
- Type annotations (low, confirmed): the test methods in
  `getstream-rtc/tests/test_call.py`, `getstream-rtc/tests/test_logging.py`
  and `tests/rtc/test_connection_manager.py`, and in
  `tests/rtc/test_audio_forwarder.py:36,60` and
  `tests/rtc/test_video_forwarder.py:29`, have no `-> None`. The fixture
  `client()` in `tests/rtc/test_connection_manager.py:29` has no return type.
- Issues that existed before this branch (low, confirmed):
  - `tests/rtc/test_connection_manager.py:20` calls `load_dotenv()` at module
    level, not in a fixture.
  - `tests/test_audio_stream_track.py:284` requests `monkeypatch` and does not
    use it.
  - `tests/rtc/coordinator/test_custom_events.py:26,40` has a test outside a
    class and a fixture without annotations.
  - `tests/assets/` has 4 files over 256 KB that no test uses:
    `speech_48k.wav`, `speech_16k.wav`, `test_tone_48k.wav` and
    `formant_speech_48k.wav`.

### CI and release

- `.github/workflows/release.yml:222` (medium, confirmed): the `publish` job
  calls `python-uv-setup` without `build-extension: "false"`, so it compiles
  getstream-rtc, which `uv build` does not use. An apt, rustup or Rust build
  failure stops the PyPI release of `getstream`. The default of
  `build-extension` is `"true"`, so each new job that uses the action compiles
  getstream-rtc unless it sets the input.
- `.github/workflows/release.yml:225-229` (medium, not confirmed): no workflow
  builds or publishes getstream-rtc wheels or an sdist. The `webrtc` extra
  requires `getstream-rtc>=0.1.0,<0.2`, so `pip install "getstream[webrtc]"`
  fails until the package is on PyPI.
- `.github/workflows/run_tests.yml:47` (low, confirmed): the `rust` job has no
  `timeout-minutes`. The test jobs use 30.

### AGENTS.md

- Line 7 (low, confirmed): "exports every class at its root" is false (see the
  `__init__.py` item above).
- Line 4 (low, confirmed): `uv sync` without `--all-extras` does not remove
  `numpy`, because `getstream-rtc` depends on it. It removes `aiortc`, `av`
  and `aiohttp`.
- Lines 79-81 (low, confirmed): records of other crates use the less verbose
  of `level` and `third_party_level` (`logging.rs:285-286`), not only
  `third_party_level`.
- Line 7 (low, confirmed): the version text does not mention the range
  `getstream-rtc>=0.1.0,<0.2` in the root `pyproject.toml:38`.
- Line 7 (low, confirmed): on Debian/Ubuntu, `cargo test --lib` also needs
  `python3-dev`. CI installs it in `run_tests.yml:50-64`.
- Style (low): item 5 (line 7) has sentences of 40 to 70 words. "for no
  reason" (line 30) and "Keep both halves impossible" (line 43) are not clear.

### This guide

- The tables compare with 4.1.0, and origin/main is 6.1.1. The
  `getstream.video.rtc` code is the same. Decide whether the columns name
  6.1.1.

### Not verified

The review did not check these points:

- The statements of this guide that come from the SDK: the event names,
  VP8/VP9-only decoding, TURN over UDP only, token expiry, the stereo mixdown,
  the 48 kHz mono `PcmFrame`, the role order of `role_filters`, the empty
  subscription list, the logger name `getstream.rtc.join.lifecycle`, and
  `participant_joined` for the participants already in the call.
- Whether the SDK sends stats to the SFU, as `SfuStatsReporter` did in 4.1.0.
- Whether a coordinator WebSocket failure now fails the join. In 4.1.0 it did
  not.
- Whether the SDK reaches `LEFT` for other reasons than a leave or a call end
  (for example a kick or a block). `ConnectionManager` then emits `call_ended`
  and ends all streams.
- Whether `test_join_during_leave` (`getstream-rtc/tests/test_call.py:246-262`)
  can get an `RtcError` other than `IllegalStateError`.
- The meaning of the `duration` argument of `write_i420` in the SDK.
- The lock behavior inside tokio, whether webrtc-rs calls `on_track` under its
  own lock, and how pyo3 drops a `Py<PyAny>` without the GIL.
- The integration tests did not run (they need credentials), and no Rust code
  was compiled.
