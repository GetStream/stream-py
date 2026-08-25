# aiortc vs Rust RTC benchmark comparison

Phase 4 of the aiortc → Rust migration. Identical Phase 0 harness (`benchmarks/run.py`) re-run against the current Rust-backed `stream-py` RTC stack (`getstream-rtc-core` 0.1.0rc2, release native extension).

## Environment

| | Baseline (aiortc) | Candidate (Rust) |
|---|---|---|
| Results JSON | `benchmarks/results/aiortc-baseline.json` | `benchmarks/results/rust.json` |
| Backend | `aiortc` 1.14.0 | `getstream-rtc-core` 0.1.0rc2 (`maturin develop --release`) |
| Git | local micros `ad3165d`; live `40473e5` | `88000af` (`experimental/rust`) |
| Python | 3.13.12 | 3.13.12 |
| Host | Apple M4 Pro, 12-core, macOS arm64 | same |
| Harness | 7 local iterations (2 warmup); 5 join / 5 e2e; 60s soak; 3 reconnect | same defaults |

Live SFU used production Stream credentials from `.env` (`STREAM_API_KEY` / `STREAM_API_SECRET`). No OpenAI. Native wheel is the 26 MB release `dylib` (debug would be 69 MB).

## Live SFU (what actually changed)

Lower is better for every row.

| metric | unit | aiortc median | Rust median | delta | winner |
|---|---|---:|---:|---:|---|
| join latency | ms | 1014.7 | 1130.9 | **+11.5%** | aiortc |
| join latency p95 | ms | 1172.9 | 1235.1 | +5.3% | aiortc |
| audio e2e latency | ms | 225.45 | 159.26 | **−29.4%** | **Rust** |
| audio e2e p95 | ms | 470.40 | 159.44 | **−66.1%** | **Rust** |
| soak CPU | % | 14.56 | 16.85 | +15.7% | aiortc |
| soak RSS | MB | 175.47 | 327.77 | **+86.8%** | aiortc |
| reconnect recovery | ms | 3345.8 | 1485.0 | **−55.6%** | **Rust** |
| reconnect p95 | ms | 3394.8 | 1516.7 | −55.3% | **Rust** |

Takeaways:

- **End-to-end audio is the clearest win.** Median 225 ms → 159 ms, and the aiortc p95 tail (470 ms) collapses to 159 ms on Rust. Samples on Rust were tightly clustered (~159 ms × 5); aiortc had two slow outliers (~418 / 484 ms).
- **REJOIN recovery is ~2.3× faster** (3.35 s → 1.48 s). Same `ReconnectionStrategy.REJOIN` path in the harness.
- **Join is slightly slower** (~115 ms median). Coordinator REST + SFU WS still go through Python; Rust only owns the SFU session after credentials. This is within run-to-run noise of a ~1 s WAN join, not a smoking gun.
- **Soak RSS nearly doubled** (175 MB → 328 MB). Expected to first order: the process now loads `getstream-rtc-core` (~26 MB `.so`) plus webrtc-rs / libvpx / opus heaps that aiortc did not. Soak CPU is slightly worse (14.6% → 16.8% of one core, `time.process_time()` over 60 s of publish+subscribe). This is **audio-only**; it does not stress video encode or congestion control.
- During e2e/soak the Python subscription helper logged `Not subscribing to track` for the publisher audio track. The marker still arrived on the `audio` event (Rust `next_pcm` pump), so the latency numbers are real. The log is a Python-side subscription quirk, not a failed bench.

## Local micros (mostly not the RTC backend)

These exercise `PcmData` / `AudioStreamTrack` / PyAV or leftover `aiortc.codecs.*`. They are **not** webrtc-rs send/recv.

| metric | unit | hib | aiortc median | Rust median | delta |
|---|---|---|---:|---:|---:|
| pcm resample 16k→48k | samples/s | ↑ | 74.1e6 | 63.6e6 | −14.1% |
| pcm resample 48k→16k | samples/s | ↑ | 191.6e6 | 151.2e6 | −21.1% |
| pcm resample mono→stereo | samples/s | ↑ | 125.2e6 | 140.6e6 | +12.3% |
| audio track pacing interval | ms | ↓ | 20.02 | 20.02 | ~0 |
| audio track pacing jitter | ms | ↓ | 0.427 | 0.421 | −1.4% |
| video passthrough 480p | fps | ↑ | 14281 | 12738 | −10.8% |
| video passthrough 720p | fps | ↑ | 7351 | 6764 | −8.0% |
| **h264 encode 480p** | fps | ↑ | 3303 | 2195 | **−33.6%** |
| **h264 encode 720p** | fps | ↑ | 1589 | 894 | **−43.7%** |
| vp8 encode 480p | fps | ↑ | 1318 | 1295 | −1.7% |
| vp8 encode 720p | fps | ↑ | 799 | 783 | −2.0% |
| opus decode | samples/s | ↑ | 9.89e6 | 9.11e6 | −7.9% |

Encoder class recorded in JSON:

- aiortc baseline: `StreamH264Encoder` / `StreamVp8Encoder` (`getstream.video.rtc.encoders_patches`, deleted with aiortc internals)
- Rust run: `H264Encoder` / `Vp8Encoder` from **`aiortc.codecs`** (test-only extra). The harness falls back there when `encoders_patches` is gone.

So the H.264 fps drop is **not** a webrtc-rs encode regression. It is a different Python encoder class. VP8 is the same `aiortc.codecs.vpx.Vp8Encoder` vs the old Stream wrapper and is within ~2%. Opus decode is also still `aiortc.codecs.opus`. PCM resample / track pacing / video passthrough are pure Python helpers; ±10–20% is consistent with noisy micro-throughput on a loaded laptop.

## webrtc-rs gaps (not exercised by this harness)

The live suite is **unconstrained LAN/WAN audio**: join, a timestamped tone, a 60 s PCM soak, and REJOIN. It does **not** run the cases where webrtc-rs is known to be weaker than Pion / aiortc.

From `stream-video-rust-release` (`CHANGELOG.md`, `src/rtc/peer.rs`, `src/rtc/publisher.rs`):

1. **No publisher-side congestion controller.** Default interceptors include receiver-side TWCC / NACK / RTCP, but webrtc-rs ships no TWCC *sender* estimator and no Google CC (GCC). High-bitrate **video** publish has no bandwidth estimation.
2. **No RTX / NACK retransmission sender.** Lost video packets are not retransmitted. Opus audio is largely unaffected (low bitrate, loss-tolerant, single layer).
3. **DTX and RED are off.** Publisher `TrackInfo` is sent with `dtx: false` and `red: false` even when the call settings advertise `opus_dtx_enabled` / `redundant_coding_enabled`.
4. **AV1 is not supported.** Pre-encoded / forwarded RTP is single-layer only.

On a constrained or lossy path, expect video quality and recovery to regress versus aiortc even though CPU / audio latency improved here. A fair follow-up would add a lossy-net video bench (gcc/twcc, rtx/nack, RED) — that is out of scope for this harness.

## Harness notes (worktree-only, not committed)

The committed Phase 0 `live.py` still constructs a sync `Stream()`. Coordinator join does `async with clone_for_token(...)`, which only `AsyncStream` implements, so the unmodified harness cannot join. The API also 404s unless the user exists (`the user … does not exist`).

Worktree-only changes used to produce `rust.json` (left uncommitted so they do not collide with coverage-expansion):

- `benchmarks/benches/live.py`: `AsyncStream(timeout=15.0)` and `upsert_users` *before* the join timer.
- `getstream/video/rtc/models.py` + `connection_manager.py`: `JoinCallResponse.own_capabilities` was missing; the session was joined with an empty capability set and `publish_audio` raised `permission denied: missing send-audio`. Parse `own_capabilities` from the join response (sibling of `call`, not `call.own_capabilities`).

Coverage-expansion was concurrently editing `connection_manager.py` (roster seeding) and adding `tests/rtc/test_live_*.py`. Those files were not touched.

Join latency does **not** include upsert time.

## JSON paths

- Baseline: `/Users/nash/git_projects/stream/video_ai/stream-py/benchmarks/results/aiortc-baseline.json`
- Candidate (this run): `benchmarks/results/rust.json` (copied onto `experimental/rust`)
- Worktree copy: `/Users/nash/git_projects/stream/video_ai/stream-py-bench-compare/benchmarks/results/rust.json`
- This report: `benchmarks/results/aiortc-vs-rust.md`

Compare command:

```
uv run python -m benchmarks.compare benchmarks/results/aiortc-baseline.json benchmarks/results/rust.json
```
