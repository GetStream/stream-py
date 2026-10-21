# Migration Guide: aiortc transport → Rust Video SDK

This guide lists the breaking changes in `getstream.video.rtc` when the WebRTC
transport moves from aiortc to the Rust Video SDK
([stream-video-rust](https://github.com/GetStream/stream-video-rust)). It
compares with stream-py 6.1.1. The work is not released yet; this guide is
updated with each change.

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
`getstream` itself stays pure Python.

`getstream-rtc` needs Python 3.10 or later, as `getstream` does. PyPI has
`getstream-rtc` wheels for Linux x86_64 and aarch64 (glibc 2.28 or later) and
for macOS arm64 (macOS 11 or later), and no sdist. On other platforms, for
example Windows and Intel macOS, `pip install "getstream[webrtc]"` fails; 6.1.1
installed there.

Building `getstream-rtc` from a git checkout needs the Rust toolchain pinned in
`getstream-rtc/rust-toolchain.toml` and a C compiler (macOS:
`xcode-select --install`; Debian/Ubuntu: `apt install build-essential`). The
Rust SDK crate links its own static libvpx and libopus.

The `webrtc` extra no longer installs `scipy`, `soundfile`, `websockets`,
`websocket-client`, `structlog`, `tenacity` and `ping3`; no stream-py code uses
them. Code that imports one of them must declare it itself.

## Breaking Changes

### Connection state

| 6.1.1 | Now | Notes |
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

| Event | 6.1.1 payload | Now |
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
| `audio` | `PcmData`, 48 kHz mono `s16`; `participant` is `models_pb2.Participant` | `PcmData`, 48 kHz mono `s16`; `participant` is a `RemoteParticipant`; `pts` (the RTP timestamp), `dts` (`None`) and `time_base` (`1/48000`) as in 6.1.1 |

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
  `False`. Compare `session_id`. In 6.1.1 the protobuf `Participant` compared
  by value.
- The other protobuf enum fields keep their `int` values, as in 6.1.1:
  `participant.connection_quality`, `participant.source`,
  `TrackUnpublished.cause`, `CallEnded.reason`. A `connection_quality` or
  `source` value that the SDK protocol does not know (from a newer SFU)
  becomes 0, and an unknown track type is not in `published_tracks`. 6.1.1
  kept these `int` values.
- `TrackPublished.participant`, `TrackUnpublished.participant` and
  `CallGrantsUpdated.current_grants` are `None` when the SFU does not send
  them; in 6.1.1 they were always an object.
- `InboundVideoState.track_type`, `PublishOption.track_type`,
  `AudioSender.track_type` and `VideoSender.track_type` use the `TrackType`
  enum.
- `codec` (on `PublishOption`, `AudioSender`, `VideoSender`,
  `VideoLayerSetting`) and `PublishOption.video_dimension` are `None` when the
  SFU does not send them.
- `PublishOption` and `VideoSender` also have `degradation_preference` (`int`),
  from a newer SFU protocol than 6.1.1.
- The nested error of the `Error` event is an `ErrorDetails`; the data path
  (`event.error.code`) is the same as in 6.1.1. `Error` is an event class, not
  an exception.
- `ICERestart` arrives after the SDK has handled the SFU's restart request;
  in 6.1.1 it was the request itself.
- A `call_ended` after a coordinator end, or after the SDK leaves the call by
  itself (see "Joining, waiting and leaving"), carries `reason` 0
  (`CALL_ENDED_REASON_UNSPECIFIED`). `call_ended` is emitted once, after the
  SFU events that arrived before the end, so an SFU `call_ended` keeps its
  `reason`.

### Events that are no longer emitted

| 6.1.1 event | Now |
| --- | --- |
| `subscriber_offer`, `publisher_answer`, `ice_trickle`, `join_response`, `health_check_response`, `go_away`, `participant_migration_complete` | Not emitted. The SDK handles these SFU transport events itself. For the participant count of `health_check_response`, use `participant_count_changed`. |
| `connection_lost`, `reconnection_success`, `reconnection_failed` | Not emitted. The SDK reconnects by itself; watch `connection.state_changed` (`RECONNECTING`, `MIGRATING`, `RECONNECTING_FAILED`). |
| coordinator events other than `custom` | Not emitted, as in 6.1.1. They are logged at DEBUG. |

### Remote tracks

| 6.1.1 | Now | Notes |
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
  app that chooses H.264 as its codec) gives no video track. 6.1.1 decoded
  H.264 with aiortc.
- A track ends (`None`, or the end of its `VideoFrameStream`s) when its
  participant leaves, when this client leaves, or when this client rejoins
  with a new session; after a rejoin a new `track_added` arrives.

### Joining, waiting and leaving

| 6.1.1 | Now | Notes |
| --- | --- | --- |
| `participant_joined` only for participants who join after you | also for the participants already in the call at join | Handlers registered before `__aenter__()` get them. |
| `wait()` returns after `leave()` | also returns when the call ends or the SDK leaves the call | It does not return at `RECONNECTING_FAILED`; call `leave()`. |
| `call_ended` only from the SFU | also when the coordinator ends the call | Emitted once. After a coordinator end, the payload is a `CallEnded` that stream-py makes. |
| after an SFU `error` with the `DISCONNECT` strategy, only the `error` event; a failed reconnection gives `RECONNECTING_FAILED` and `reconnection_failed` | the SDK leaves the call: `connection.state_changed` gives `LEFT`, `call_ended` comes with `reason` 0, and `wait()` returns | The SDK also leaves when ICE never connects after several tries, when it reaches its rejoin rate limit, and after too many failed negotiations. Other reconnection failures give `RECONNECTING_FAILED`. |
| the join continues when the coordinator WebSocket cannot connect; the failure is logged | `connect()` raises, for example `CoordinatorError` | After the join, a closed coordinator WebSocket or a failed coordinator health check makes the SDK rejoin the call with a new session (see "Remote tracks"). 6.1.1 reconnected only the WebSocket. |
| `connect()` retries with `max_join_retries` and other SFUs | the SDK retries | The `max_join_retries` argument is removed. |
| `rtc.join(call, user_id, **kwargs)` passes `kwargs` to the join request | `rtc.join(call, user_id, create, subscription_config)` | Other keyword arguments raise `TypeError`. For the join request arguments `data`, `ring`, `notify` and `video`, call `await call.get_or_create(...)` with them before `rtc.join()`; it takes the same arguments. |
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
  garbled. In 6.1.1 the aiortc Opus encoder converted every format to `s16`.
- The SDK takes the sample rate of the first frame of a published track. A
  later frame at another rate raises `PcmRateMismatchError` (`expected`,
  `actual`), which stops the forwarding and unpublishes the track.
  `AudioStreamTrack` always gives frames at its own `sample_rate`.
- `AudioStreamTrack` has a new setting `pace`, `False` by default:
  - `pace=False`: `recv()` returns the next queued frame at once and waits for
    the next `write()` when the queue is empty. This is the right setting for
    `add_tracks`.
  - `pace=True`: the 6.1.1 behavior, one frame per 20 ms and silence when the
    queue is empty. Code that passes an `AudioStreamTrack` to its own aiortc
    connection needs `pace=True`.
- `AudioStreamTrack.wait_for_flush()` is new: it returns at the next
  `flush()`. `add_tracks` uses it, so `flush()` also drops the audio that is
  already queued for sending and the audio of a write to the SDK that is in
  progress.
- When more audio is queued than `audio_buffer_size_ms`, the oldest audio is
  dropped, as in 6.1.1, with an "Audio buffer overflow" DEBUG record from
  `getstream.video.rtc.audio_forwarder`. `add_tracks` raises `MediaError` for
  an `audio_buffer_size_ms` below 20 (one frame) and `ValueError` for a
  negative value.
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`. In 6.1.1 the packets only stopped.
- A new `add_tracks(audio=new_track)` replaces the published audio track: the
  earlier track is unpublished first, also while it is still live. In 6.1.1
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
- `PyAVResampler` is removed. No replacement works the same:
  - `Resampler(format, sample_rate, channels).resample(pcm)` takes the same
    arguments (without `frame_size`) and returns `PcmData`, but it
    interpolates linearly and keeps no state between calls.
  - `FrameResampler(rate, layout, format, frame_size)` keeps state between
    calls, as `PyAVResampler` did, but it returns a `list` of `av.AudioFrame`
    without `pts`, and its only output format is `s16`.

### Publishing video

- `add_tracks(video=track)` accepts any aiortc video track; the track paces
  itself, as in 6.1.1.
- The video is sent as VP9, the SFU's default publish option for camera
  video. 6.1.1 sent H264 (aiortc without VP8).
- The environment variables `STREAM_PATCH_AIORTC_BITRATES` and
  `STREAM_PATCH_AIORTC_H264_PRESET` have no effect: the aiortc encoder patches
  are removed. The SDK encoder starts at its default bitrate and follows the
  SFU's publish quality settings (`change_publish_quality`).
- The whole track has the size of its first frame. Later frames of another
  size are scaled to it, and an odd width or height is raised to the next
  even value. In 6.1.1 each frame kept its own size.
- The frame duration comes from the `pts` difference; frames without `pts`
  count as 1/30 s.
- After `track.stop()`, the track is unpublished, so other participants get
  `track_unpublished`.
- A new `add_tracks(video=new_track)` replaces the published video track: the
  earlier track is unpublished first, also while it is still live. Other
  participants get the new frames on their existing `RemoteTrack`. In 6.1.1
  each call added one more video track.

### Permissions to publish

In 6.1.1, stream-py did not change the published tracks when the permissions
of the user changed. Now the SDK does:

- When the `send-audio` or `send-video` capability is removed, the SDK
  unpublishes the track of that kind.
- When the SFU removes the grant (`call_grants_updated`), the SDK mutes the
  track.
- When the permission is given back, the SDK does not publish or unmute the
  track. Call `add_tracks()` again.

### Handlers, failures and lost events

- A handler that raises does not stop the other events, `wait()` or
  `leave()`. pyee passes its exception to the `error` event. Without an `error`
  handler, the exception is logged at ERROR with its traceback, with the
  message "A 'error' handler failed". With an `error` handler (for example for
  the SFU `Error` event), that handler gets the exception, and nothing is
  logged. This is true for `ConnectionManager` and `participants_state`.
- If `connect()` fails or is cancelled after the SDK join, it leaves the call
  before it raises.
- If the forwarding of a track from `add_tracks` raises, for example for the
  `fltp` frames or the rate change in "Publishing audio", the track is
  unpublished, and the exception is logged at ERROR with its traceback, with
  the message "The forwarding of a published track failed".
- If the event loop is blocked long enough that `ConnectionManager` falls
  behind an SDK event stream (1024 buffered events per stream), the lost events are
  skipped with a `stream.rtc.events.lagged` WARNING (field `skipped`), and
  `participants_state` is filled again from the SDK's participant list.
- If the event loop is blocked long enough that more than 64 new remote tracks
  wait to be read, the SDK unsubscribes from the tracks that do not fit, and
  `ConnectionManager` logs a WARNING. These tracks give no `track_added` and no
  `audio` until they are published again. The tracks that come after them
  arrive as usual.

### `participants_state`

- `get_participants()` and the `map()` handlers give a list of
  `RemoteParticipant`, not `models_pb2.Participant`. The list includes this
  participant (the agent) and is keyed by `session_id`. To skip the agent,
  compare `participant.user_id` with `connection.user_id`; this also skips the
  other sessions of the same user. The `participant_joined` and
  `participant_left` events of `participants_state` also give a
  `RemoteParticipant`.
- After the join, and again after each reconnect, the list is filled from the
  SDK's participants; then `participant_joined` and `participant_left` update
  it. `participant_updated` does not change it, as in 6.1.1.
- `track_published` does not change the list. In 6.1.1 it replaced the
  participant (with its new `published_tracks`) and called the `map()`
  handlers. Now `published_tracks` in the list keeps the value from the join
  or from `participant_joined`.
- `get_user_from_track_id()`, `get_stream_id_from_track_id()` and
  `set_track_stream_mapping()` are removed: they mapped aiortc track ids. A
  `RemoteTrack` carries its `participant`.

### Subscriptions

`subscription_config` of `rtc.join` has the same fields as in 6.1.1
(`default`, `role_filters`, `max_subscriptions`, separate video and screen
share sizes). The SDK applies it again on each participant and track event.
The differences:

- `role_filters` also applies to the tracks that are published after the
  join. In 6.1.1 these tracks got the `default` rule, except in large calls:
  the SFU sends the participant of `track_published` only in large calls.
- The SDK makes the list of matching tracks again on each event and keeps the
  first `max_subscriptions` of them, so a new track can take the place of a
  track that is already subscribed. In 6.1.1 the tracks that were subscribed
  first stayed, and a track over the limit was skipped.
- A participant with two roles that both have a rule in `role_filters` gets
  the rule of the first role in its `roles` list. In 6.1.1 the choice was not
  defined.
- When no track matches any more, the SDK sends an empty subscription list to
  the SFU. The first list after a join or a reconnect is never empty. 6.1.1
  never sent an empty list.
- The SFU sends remote audio without a request, also without a
  `subscription_config`, as in 6.1.1. It is not verified whether a config
  without `TRACK_TYPE_AUDIO` stops it.

### Errors

| 6.1.1 | Now |
| --- | --- |
| `SfuJoinError`, `SfuConnectionError` | Errors from `getstream_rtc`, all subclasses of `RustError`: |
| | `ApiError` (coordinator HTTP error: `code`, `status_code`, `message`, `unrecoverable`) |
| | `CoordinatorError` (coordinator connection or authentication failed) |
| | `PermissionDeniedError` (`capability`), `IllegalStateError`, `MediaError`, `PcmQueueOverflowError`, `PcmRateMismatchError` (`expected`, `actual`) |
| | `RtcError` (other RTC failures), `ConfigError` (invalid client configuration) |

`rtc.join()` and `ConnectionManager()` create the SDK client. For an invalid
client configuration they raise `ConfigError`, and for other client errors
`RustError` itself, before `connect()`.

`add_tracks()` raised `SfuRpcError` when the SFU rejected the publish and
`TimeoutError` when the publisher did not connect in 15 s. Now it raises:

- `PermissionDeniedError` when the user does not have the `send-audio` or
  `send-video` capability.
- `IllegalStateError` before the join.
- `MediaError` when the SFU has no unused publish option for the codec of the
  track.
- `RtcError` for other publish failures.

### `ConnectionManager` attributes

These attributes and methods of the aiortc transport are removed:

- `join_response`, `session_id`, `running`, `local_sfu`, `kwargs`.
- `ws_client`, `publisher_pc`, `subscriber_pc`, `publisher_negotiation_lock`,
  `subscriber_negotiation_lock`, `twirp_signaling_client`, `twirp_context`,
  `stats_reporter`, `tracer`, `reconnector`.
- `pc_id()`, `sfu_id()`, `republish_tracks()`.

`call`, `user_id`, `create`, `participants_state` and `connection_state` stay.
For the call data of `join_response`, use `await call.get()`. `session_id` has
no replacement.

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
- `rtc.join()` starts the threads of the SDK runtime, and the first
  `connect()` (or `getstream_rtc.configure_logging()`) starts the thread
  `getstream-logging`, which hands the Rust records to `logging`. An import
  starts no thread. `fork()` copies only the calling thread, so a process
  forked after that cannot use the SDK. In a process forked after `connect()`,
  `connect()` raises `RuntimeError`. In a process forked after `rtc.join()`
  only, SDK calls never complete, and `connect()` never returns. Start the
  worker processes before the first `rtc.join()`, as
  `gunicorn --preload` and the Celery prefork pool do, or use the `spawn` or
  `forkserver` start method of `multiprocessing`.

### Telemetry

- Only the OpenTelemetry spans `connect`, `leave` and `rtc.add_tracks` stay.
  The spans of the aiortc transport steps are removed, for example
  `coordinator-setup`, `coordinator-join-call`, `sfu-signaling-ws-connect`,
  `rtc.on_subscriber_offer`, `rtc.publisher_pc.create_offer` and
  `signaling.twirp.<method>`.

### Network

- TURN works only over UDP. Networks that allow only TCP or TLS (for example
  port 443 only) cannot connect; aiortc supported TURN over TCP and TLS.
- When the `Stream` client has the API secret, the SDK creates a new user
  token for each join, rejoin and migration. Each token is valid for 10
  minutes.
- When the `Stream` client has only a user token, the SDK cannot refresh it.
  If that token has an `expiration` and expires during the call, each later
  rejoin or migration fails. Tokens from `create_token()` without
  `expiration` do not expire.

### Local recording

Local recording is removed. stream-video-js, the Go SDK and the Rust SDK do
not have local call recording either.

| 6.1.1 | Now |
| --- | --- |
| `connection.start_recording()`, `stop_recording()`, `is_recording`, `get_recording_status()` | removed |
| `connection.recording_manager` and the module `getstream.video.rtc.recording` (`RecordingManager`, `RecordingType`, `RecordingConfig` and the recorder classes) | removed |
| the `recording_manager` events `recording_started`, `recording_stopped`, `user_recording_started`, `user_recording_stopped`, `composite_recording_started`, `composite_recording_stopped`, `recording_error` | removed |

To record a call, use the server recording:
`call.start_recording(recording_type)` and
`call.stop_recording(recording_type)`. The coordinator event
`call.recording_ready` tells when a file is ready; `ConnectionManager` does not
emit it, so receive it with a webhook. To write files locally, read the `audio`
event (`PcmData` with `participant`, `pts` and `time_base`) and
`track.video_frames()`.

## Other bugs

The code review of this branch found these issues in addition to the changes
that the sections above describe. They are not addressed yet. Each item gives
its location, its severity, and whether the review confirmed it in the code or
in a test run ("confirmed") or found only its cause ("not confirmed").

### Rust bindings

- `getstream-rtc/rustsrc/tracks.rs:100` (low, confirmed): if Python cancels
  the awaitable after the Rust future is complete (for example
  `asyncio.wait_for(anext(tracks), timeout)`), pyo3-async-runtimes discards
  the result (`generic.rs:348`). The `RemoteTrack` is dropped and the SDK
  unsubscribes from it. The track is lost until it is published again.
  `EventStream` and `next_pcm()` can lose one item in the same way.

### Python and type stubs

- `getstream-rtc/getstream_rtc/_bindings.pyi:26,35` (medium, confirmed): the
  stub declares `CallingState(Enum)` and `TrackType(Enum)`. Type checkers accept
  `hash()`, `.name`, `.value` and iteration, which fail at runtime (see
  "Connection state").
- `getstream/video/rtc/connection_manager.py:391-409` (low, not confirmed):
  `_stop_forwarding()` can cancel a task that is already in its
  `finally: await stop_publish(...)` because its source ended. The SDK stop is
  then dropped. If this occurs during the mute request to the SFU, the old
  track stays in the SDK with a pending stop and keeps the publish option of
  its kind, so the publish of the new track raises `MediaError`. Two
  concurrent `add_tracks(audio=...)` calls do not leave a forwarder that runs:
  the second publish raises `MediaError`, because the first track has the
  only audio publish option.
- `getstream/video/rtc/video_forwarder.py:41-48` (low, confirmed): the SDK
  uses `duration` as the length of the frame and adds it to the RTP
  timestamp after that frame. The forwarder gives the gap since the previous
  frame, so each value is one frame late. The RTP timestamps are wrong only
  when the frame rate changes.
- `getstream-rtc/getstream_rtc/_bindings.pyi:475-478` (low, confirmed): the
  docstring says only that a capacity below 0.02 s raises `MediaError`. A
  negative or NaN value raises `ValueError`.
- `getstream/video/rtc/audio_forwarder.py:50-51` (low, confirmed): the comment
  says that the aiortc Opus encoder accepts only `s16`. It converts every
  format to `s16` (see "Publishing audio").
- `getstream/video/rtc/connection_manager.py:67,177` (low, confirmed): the
  comments "as in the aiortc version" describe the migration, not the code.

### Tests

- `getstream-rtc/tests/test_logging.py:200-211` (medium, confirmed):
  `test_no_records_after_logging_is_stopped` cannot fail. The autouse fixture
  `forward_sdk_logs` forwards at INFO, and the `pcm_queue_overflow` record is
  DEBUG, so Rust filters it also while forwarding is on. Without the
  `configure_logging(None, logging.NOTSET)` call, the test still passes.
- `getstream-rtc/tests/test_call.py:214-223` (low, not confirmed):
  `test_cancelled_join_allows_new_join` cancels the join after 0.1 s. If the
  join completes faster, `pytest.raises(CancelledError)` fails.
- `async for ... break` loops without `else: pytest.fail(...)` (low, not
  confirmed): `getstream-rtc/tests/test_call.py:295, 317, 337, 346, 372, 397,
  415, 479, 501, 528, 547, 568, 584, 738` and
  `tests/rtc/test_connection_manager.py:664, 673`. If the stream ends before the
  expected event, `test_calling_state_changed_to_joined` (397) and
  `test_track_published` (479) pass with no assertion. The other tests assert
  on the last event.
- Writer tasks that are cancelled and never awaited (low, not confirmed):
  `getstream-rtc/tests/test_call.py:79-81, 97-99, 367/370, 382/385` and
  `tests/rtc/test_connection_manager.py:88-90`. If `write_pcm` or
  `write_i420` raises, the receiving test waits for the 120 s timeout and does
  not show the cause.
- Type annotations (low, confirmed): the test methods in
  `getstream-rtc/tests/test_call.py`, `getstream-rtc/tests/test_logging.py`
  and `tests/rtc/test_connection_manager.py`, and in
  `tests/rtc/test_audio_forwarder.py:36,60` and
  `tests/rtc/test_video_forwarder.py:29`, have no `-> None`. The fixture
  `client()` in `tests/rtc/test_connection_manager.py:30` has no return type.

### Not verified

The review did not check these points:

- The event names that the SDK emits.
- Whether the SFU sends an `Error` with the `DISCONNECT` strategy when it
  kicks or blocks a participant. The SDK has no other handling for a kick or a
  block.
- The lock behavior inside tokio, and how pyo3 drops a `Py<PyAny>` without the
  GIL.
