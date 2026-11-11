# Changelog

## 0.1.0 (2026-10-22)


### ⚠ BREAKING CHANGES

* **rtc:** move the WebRTC transport from aiortc to the Rust Video SDK. See [#303](https://github.com/GetStream/stream-py/pull/303) and the [migration guide](https://github.com/GetStream/stream-py/blob/main/MIGRATION_v6_to_v7.md) for all changes. The main changes:
    * the `webrtc` extra installs the new package `getstream-rtc`, which has wheels only for Linux x86_64 and aarch64 and macOS arm64
    * `rtc.join()` takes only `create` and `subscription_config`; `**kwargs` and `max_join_retries` are removed
    * `connection_state` returns `CallingState` and is read only; `ConnectionState` is removed
    * event payloads are `getstream_rtc` classes, not SFU protobuf messages, and `participant` is a `RemoteParticipant`
    * the SFU transport events and the reconnection events are not emitted; watch `connection.state_changed`
    * `track_added` gives a `RemoteTrack` with `next_pcm()` and `video_frames()`; `add_track_subscriber()` is removed
    * errors are `getstream_rtc` errors (subclasses of `RustError`), not `SfuJoinError` or `SfuRpcError`
    * `add_tracks()` replaces the published track of the same kind, and video is sent as VP9
    * `AudioStreamTrack` has `pace=False` by default; set `pace=True` to send it through your own aiortc connection
    * remote H.264 video is not decoded; the SDK decodes only VP8 and VP9
    * local recording is removed; use the server recording (`call.start_recording()`)

### Features

* **rtc:** move the WebRTC transport from aiortc to the Rust Video SDK ([206c695](https://github.com/GetStream/stream-py/commit/206c695a3c9246e7528ab12ba3ee97761e1b6700)), closes [#303](https://github.com/GetStream/stream-py/issues/303)
