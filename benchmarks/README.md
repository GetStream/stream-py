# RTC benchmark harness

This suite is the only supported way to compare aiortc and Rust RTC. Numbers
from mixed trees, mixed hosts, or a loaded laptop are not canonical.

## The only valid A/B procedure

Run both sides on the **same idle Linux x86_64 host**. Do not compare macOS against
Linux, and do not merge result JSONs from different SHAs or OSes.

1. Confirm the host is idle (`uptime`; 1-minute load should be well below CPU
   count). The harness aborts when `loadavg / ncpu >= 0.75` and warns at
   `0.25`. Override only with `STREAM_BENCH_ALLOW_LOAD=1`.
2. Place credentials in an untracked `.env` (`STREAM_API_KEY`,
   `STREAM_API_SECRET`). Live benches skip cleanly when they are unset.
3. **aiortc baseline** — commit `40473e5`, separate venv, **no**
   `getstream-rtc-core`:

   ```bash
   git checkout 40473e5
   uv venv .venv-aiortc
   source .venv-aiortc/bin/activate
   uv sync --extra webrtc
   # ensure getstream-rtc-core is not installed
   STREAM_RTC_BACKEND=aiortc uv run python -m benchmarks.run \
     --output benchmarks/results/aiortc-baseline.json \
     --profile clean
   ```

4. **Rust candidate** — branch `experimental/rust` with a natively built
   **release** `getstream-rtc-core` wheel (do not copy a macOS dylib onto
   Linux):

   ```bash
   git checkout experimental/rust
   uv venv .venv-rust
   source .venv-rust/bin/activate
   uv sync --extra webrtc
   # install the Linux x86_64 release wheel built on this host
   uv run python -m benchmarks.run \
     --output benchmarks/results/rust.json \
     --profile clean
   ```

5. Compare:

   ```bash
   uv run python -m benchmarks.compare \
     benchmarks/results/aiortc-baseline.json \
     benchmarks/results/rust.json
   ```

   `p95` is omitted when either side has `n < 20`.

Identical CLI flags on both sides. Nothing else scheduled on the box. Result
JSON records `host_class` (`canonical-linux-x86_64` vs `non-canonical`),
`getstream_rtc_core_version`, native extension SHA-256, loadavg, and
`netem_profile`. Laptop runs are for iteration only; they are labeled
non-canonical and must not be published as the comparison.

This is a cross-stack E2E comparison (Python coordinator + SFU + RTC), not an
isolated webrtc-rs micro swap.

## Flags

| Flag | Default | Notes |
|---|---|---|
| `--live-runs` | 30 | Join + audio e2e repeats |
| `--reconnect-runs` | 15 | REJOIN recovery repeats |
| `--soak-seconds` | 60 | Each soak repeat (3× audio, 3× 720p video) |
| `--resource-only` | off | CPU/RSS soaks only, this process |
| `--resource-inline` | off | Debug: soaks in the join/e2e process (polluted) |
| `--profile` | `clean` | Recorded in metadata; apply netem separately |
| `--live-only` / `--local-only` | off | Restrict categories |
| `--output` | `benchmarks/results/latest.json` | |
| `STREAM_BENCH_VIDEO_CODEC` | `vp9` | Rust publish codec: `vp9` (default), `vp8`, or `h264`. Diagnostic only; does not change the public `add_tracks` API. aiortc ignores this. Live VP8/H264 only works if the SFU advertises that codec. |

CPU and RSS are **not** taken in the same process as the 30 join/leave
cycles. The default path spawns `python -m benchmarks.run --resource-only`
so `time.process_time()` and `VmRSS` are a clean interpreter plus one
publish/subscribe pair. The earlier 32% Rust soak CPU was leftover Tokio
workers spinning after `leave()`, not encode cost.

Audio soak is Opus only (too cheap to tell the stacks apart). Video soak
publishes 720p30 I420 so encode/decode CPU is actually in the sample.
Each reports: CPU % of one core (`process_time / wall`), RSS at import,
RSS before join, steady-state median, peak, `RUSAGE_SELF.ru_maxrss`,
growth slope, and thread count.

## Reconnect timers (same on both stacks)

The REJOIN bench calls Python `ReconnectionManager.reconnect(REJOIN)` on
both aiortc `40473e5` and Rust. Shared constants:

- disconnection timeout **30s** (only aborts a *failed* retry loop)
- bench `wait_for(..., timeout=30)` (failure ceiling, not a sleep)
- `_DEFAULT_MIN_WAIT` / `_DEFAULT_MAX_WAIT` / `_DEFAULT_MAX_ATTEMPTS` are
  **dead** (never used)
- 0.5s sleep only after a failed attempt

Rust `retry_interval` (250–5000 ms JS backoff) is not on this path: the
harness drives a single successful REJOIN, not the Rust reconnect state
machine. The ~4.4s vs ~0.5s gap is ICE/PC teardown+setup vs
`RtcSession.join`, not a different timeout.

Soak reports baseline RSS (before join), steady-state median, peak, and growth
slope. Join also reports token mint, coordinator REST, and `RtcSession.join`.

Video (720p30 via `LocalVideoTrack`) and DTX (`bytesSent` silence vs speech)
poll `ConnectionManager.stats()` at 1 Hz. The live path passes
`join_response.call.settings.audio.opus_dtx_enabled` into `RtcSession.join`.
The DTX bench additionally creates the call with `opus_dtx_enabled=True` so
the measurement is not hostage to the app's default call-type settings.

## Netem profiles (Linux host, later)

Apply **before** `benchmarks.run --profile …`. Requires root and `tc`:

```bash
sudo benchmarks/netem/apply.sh clean          # or omit; default iface
sudo benchmarks/netem/apply.sh loss-1pct
sudo benchmarks/netem/apply.sh loss-5pct
sudo benchmarks/netem/apply.sh cap-1mbps
sudo benchmarks/netem/apply.sh rtt-200ms      # +200ms egress delay
sudo benchmarks/netem/apply.sh clean          # restore
```

Pass the matching `--profile` so JSON files stay comparable across impairment
levels. Do not apply netem inside Docker Desktop on macOS.
