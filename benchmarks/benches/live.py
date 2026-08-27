"""Live SFU benchmarks. Skip unless STREAM_API_KEY and STREAM_API_SECRET are set."""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
import uuid
from contextlib import contextmanager
from typing import Any, Iterator

import numpy as np

from getstream.models import UserRequest
from getstream.stream import AsyncStream
from getstream.video.rtc import AudioStreamTrack, PcmData, join
from getstream.video.rtc.reconnection import ReconnectionStrategy
from getstream.video.rtc.track_util import AudioFormat

from benchmarks._support import TONE_16K, current_rss_bytes, summarize

logger = logging.getLogger("benchmarks.live")

MARKER_FREQ_HZ = 2500.0
MARKER_MS = 80
GOERTZEL_RATIO = 8.0
SOAK_REPEATS = 3
RSS_SAMPLE_INTERVAL_S = 0.2
BYTES_PER_MB = 1024 * 1024


def _sine_pcm(freq: float, sample_rate: int, duration_ms: int, amplitude: int = 18000) -> PcmData:
    n = int(sample_rate * duration_ms / 1000)
    t = np.arange(n) / sample_rate
    envelope = np.sin(np.pi * np.arange(n) / max(n, 1))
    samples = (envelope * np.sin(2 * np.pi * freq * t) * amplitude).astype(np.int16)
    return PcmData(
        samples=samples,
        sample_rate=sample_rate,
        format=AudioFormat.S16,
        channels=1,
    )


def _silence_pcm(sample_rate: int, duration_ms: int) -> PcmData:
    n = int(sample_rate * duration_ms / 1000)
    return PcmData(
        samples=np.zeros(n, dtype=np.int16),
        sample_rate=sample_rate,
        format=AudioFormat.S16,
        channels=1,
    )


def _goertzel_power(samples: np.ndarray, sample_rate: int, freq: float) -> float:
    n = samples.size
    if n < 32:
        return 0.0
    k = int(0.5 + (n * freq) / sample_rate)
    omega = 2.0 * np.pi * k / n
    coeff = 2.0 * np.cos(omega)
    s0 = 0.0
    s1 = 0.0
    s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2 = s1
        s1 = s0
    return s1 * s1 + s2 * s2 - coeff * s1 * s2


def _contains_marker(pcm: PcmData, freq: float = MARKER_FREQ_HZ) -> bool:
    samples = np.asarray(pcm.samples, dtype=np.float64).ravel()
    if samples.size < 64:
        return False
    rms = float(np.sqrt(np.mean(samples * samples)))
    if rms < 200.0:
        return False
    target = _goertzel_power(samples, pcm.sample_rate, freq)
    neighbor = _goertzel_power(samples, pcm.sample_rate, freq * 0.5)
    return neighbor > 0 and (target / neighbor) >= GOERTZEL_RATIO


def _client() -> AsyncStream:
    # Coordinator join uses `async with clone_for_token(...)`, which only
    # AsyncStream supports. Sync Stream is not an async context manager.
    return AsyncStream(timeout=15.0)


async def _ensure_users(client: AsyncStream, *user_ids: str) -> None:
    await client.upsert_users(*[UserRequest(id=uid) for uid in user_ids])


@contextmanager
def _join_probes(client: AsyncStream, timings: dict[str, float]) -> Iterator[None]:
    """Time token mint, coordinator REST, and RtcSession.join on the live path."""
    import getstream.video.rtc.connection_manager as cm

    orig_create_token = client.create_token
    orig_join_call = cm.join_call
    orig_join_rtc = cm.ConnectionManager._join_rtc_session

    def timed_create_token(*args: Any, **kwargs: Any):
        t0 = time.perf_counter()
        result = orig_create_token(*args, **kwargs)
        dt = (time.perf_counter() - t0) * 1000.0
        if "token_mint_ms" not in timings:
            timings["token_mint_ms"] = dt
        return result

    async def timed_join_call(*args: Any, **kwargs: Any):
        t0 = time.perf_counter()
        result = await orig_join_call(*args, **kwargs)
        wall = (time.perf_counter() - t0) * 1000.0
        token = timings.get("token_mint_ms", 0.0)
        timings["coordinator_rest_ms"] = max(0.0, wall - token)
        return result

    async def timed_join_rtc_session(self):
        t0 = time.perf_counter()
        result = await orig_join_rtc(self)
        timings["rtc_session_join_ms"] = (time.perf_counter() - t0) * 1000.0
        return result

    client.create_token = timed_create_token
    cm.join_call = timed_join_call
    cm.ConnectionManager._join_rtc_session = timed_join_rtc_session
    try:
        yield
    finally:
        client.create_token = orig_create_token
        cm.join_call = orig_join_call
        cm.ConnectionManager._join_rtc_session = orig_join_rtc


async def _join_once(client: AsyncStream) -> dict[str, float]:
    call = client.video.call("default", f"bench-join-{uuid.uuid4().hex[:12]}")
    user_id = f"bench-join-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, user_id)
    timings: dict[str, float] = {}
    with _join_probes(client, timings):
        t0 = time.perf_counter()
        async with await join(call, user_id) as connection:
            timings["total_ms"] = (time.perf_counter() - t0) * 1000.0
            await connection.leave()
    for key in ("token_mint_ms", "coordinator_rest_ms", "rtc_session_join_ms"):
        timings.setdefault(key, 0.0)
    return timings


async def _audio_e2e_latency_ms(client: AsyncStream) -> float:
    call_id = f"bench-e2e-{uuid.uuid4().hex[:12]}"
    call = client.video.call("default", call_id)
    pub_id = f"bench-pub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-sub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)
    detected: asyncio.Event = asyncio.Event()
    recv_at: dict[str, float] = {}

    async with await join(call, sub_id) as subscriber:

        def on_audio(pcm: PcmData, *args: Any) -> None:
            if detected.is_set():
                return
            if _contains_marker(pcm):
                recv_at["t"] = time.perf_counter()
                detected.set()

        subscriber.on("audio", on_audio)

        async with await join(call, pub_id) as publisher:
            track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
            await publisher.add_tracks(audio=track)
            # Let ICE / subscriptions settle before the marker.
            await asyncio.sleep(2.0)
            await track.write(_silence_pcm(48000, 200))
            await asyncio.sleep(0.3)
            send_at = time.perf_counter()
            await track.write(_sine_pcm(MARKER_FREQ_HZ, 48000, MARKER_MS), final=True)
            try:
                await asyncio.wait_for(detected.wait(), timeout=15.0)
            finally:
                track.stop()
            if "t" not in recv_at:
                raise TimeoutError("subscriber did not observe the marker tone")
            return (recv_at["t"] - send_at) * 1000.0


def _warmup_seconds(soak_seconds: float) -> float:
    return min(10.0, max(0.0, soak_seconds * 0.2))


def _linear_slope(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return 0.0
    x_mean = sum(xs) / n
    y_mean = sum(ys) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
    den = sum((x - x_mean) ** 2 for x in xs)
    if den == 0.0:
        return 0.0
    return num / den


async def _rss_sampler(
    stop: asyncio.Event, *, interval: float
) -> list[tuple[float, int]]:
    samples: list[tuple[float, int]] = []
    while not stop.is_set():
        samples.append((time.monotonic(), current_rss_bytes()))
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
    samples.append((time.monotonic(), current_rss_bytes()))
    return samples


async def _soak(client: AsyncStream, *, seconds: float) -> dict[str, float]:
    """Publish + subscribe for `seconds`; return soak CPU/RSS breakdown."""
    import soundfile as sf

    data, sample_rate = sf.read(str(TONE_16K), dtype="int16")
    source = np.asarray(data).ravel()
    call = client.video.call("default", f"bench-soak-{uuid.uuid4().hex[:12]}")
    pub_id = f"bench-soak-pub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-soak-sub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)

    warmup_s = _warmup_seconds(seconds)
    baseline_rss = current_rss_bytes()
    stop_sampler = asyncio.Event()
    sampler_task: asyncio.Task[list[tuple[float, int]]] | None = None
    cpu_armed = False
    cpu_start = 0.0
    wall_start = 0.0
    joined_at = 0.0
    rss_series: list[tuple[float, int]] = []

    try:
        async with await join(call, sub_id) as subscriber:

            @subscriber.on("audio")
            def _on_audio(pcm: PcmData, *args: Any) -> None:
                return

            async with await join(call, pub_id) as publisher:
                joined_at = time.monotonic()
                sampler_task = asyncio.create_task(
                    _rss_sampler(stop_sampler, interval=RSS_SAMPLE_INTERVAL_S),
                    name="soak-rss-sampler",
                )
                track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
                await publisher.add_tracks(audio=track)
                await asyncio.sleep(1.0)
                chunk = int(sample_rate * 0.1)
                offset = 0
                deadline = time.monotonic() + seconds
                warmup_until = joined_at + warmup_s
                cpu_armed = warmup_s <= 0.0
                if cpu_armed:
                    cpu_start = time.process_time()
                    wall_start = time.monotonic()
                while time.monotonic() < deadline:
                    now = time.monotonic()
                    if not cpu_armed and now >= warmup_until:
                        cpu_start = time.process_time()
                        wall_start = now
                        cpu_armed = True
                    end = offset + chunk
                    if end > source.size:
                        offset = 0
                        end = chunk
                    pcm = PcmData(
                        samples=source[offset:end],
                        sample_rate=int(sample_rate),
                        format=AudioFormat.S16,
                        channels=1,
                    )
                    await track.write(pcm)
                    offset = end
                    await asyncio.sleep(0.05)
                track.stop()
    finally:
        stop_sampler.set()
        if sampler_task is not None:
            rss_series = await sampler_task

    wall = (time.monotonic() - wall_start) if cpu_armed else 0.0
    cpu_percent = (
        ((time.process_time() - cpu_start) / wall) * 100.0 if wall > 0 else 0.0
    )
    post_join = [(t, rss) for t, rss in rss_series if t >= joined_at] or rss_series
    peak_rss_mb = (
        max(rss for _, rss in post_join) / BYTES_PER_MB if post_join else 0.0
    )
    warmup_until = joined_at + warmup_s
    steady = [(t, rss) for t, rss in post_join if t >= warmup_until] or post_join
    steady_mb = [rss / BYTES_PER_MB for _, rss in steady]
    steady_median_mb = float(statistics.median(steady_mb)) if steady_mb else 0.0
    slope = _linear_slope(
        [t - warmup_until for t, _ in steady],
        steady_mb,
    )
    return {
        "cpu_percent": cpu_percent,
        "rss_baseline_mb": baseline_rss / BYTES_PER_MB,
        "rss_steady_median_mb": steady_median_mb,
        "rss_peak_mb": peak_rss_mb,
        "rss_growth_slope_mb_per_s": slope,
        "warmup_s": warmup_s,
    }


async def _reconnect_recovery_ms(client: AsyncStream) -> float:
    call = client.video.call("default", f"bench-re-{uuid.uuid4().hex[:12]}")
    user_id = f"bench-re-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, user_id)
    async with await join(call, user_id) as connection:
        await asyncio.sleep(1.5)
        done = asyncio.Event()
        payload: dict[str, Any] = {}

        def on_success(data: Any, *args: Any) -> None:
            payload["data"] = data
            done.set()

        def on_failed(data: Any, *args: Any) -> None:
            payload["error"] = data
            done.set()

        connection.on("reconnection_success", on_success)
        connection.on("reconnection_failed", on_failed)
        t0 = time.perf_counter()
        await connection.reconnector.reconnect(
            ReconnectionStrategy.REJOIN, "benchmark"
        )
        await asyncio.wait_for(done.wait(), timeout=30.0)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        if "error" in payload:
            raise RuntimeError(f"reconnection failed: {payload['error']}")
        return elapsed_ms


async def _repeat(
    name: str,
    fn,
    *,
    runs: int,
    unit: str,
    higher_is_better: bool,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    samples: list[float] = []
    for i in range(runs):
        logger.info("%s run %d/%d", name, i + 1, runs)
        samples.append(float(await fn()))
    return summarize(
        name,
        samples,
        category="live",
        unit=unit,
        higher_is_better=higher_is_better,
        extra=extra,
    )


async def run_live_benches(
    *, runs: int, soak_seconds: float, reconnect_runs: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    client = _client()

    async def _capture(name: str, factory) -> None:
        try:
            results.append(await factory())
        except Exception as exc:
            logger.exception("live bench %s failed", name)
            errors.append({"name": name, "reason": str(exc)})

    try:
        join_runs: list[dict[str, float]] = []
        for i in range(runs):
            logger.info("live.join_latency_ms run %d/%d", i + 1, runs)
            join_runs.append(await _join_once(client))
        join_metrics = (
            ("live.join_latency_ms", "total_ms"),
            ("live.join_token_mint_ms", "token_mint_ms"),
            ("live.join_coordinator_rest_ms", "coordinator_rest_ms"),
            ("live.join_rtc_session_ms", "rtc_session_join_ms"),
        )
        for name, key in join_metrics:
            results.append(
                summarize(
                    name,
                    [run[key] for run in join_runs],
                    category="live",
                    unit="ms",
                    higher_is_better=False,
                )
            )
    except Exception as exc:
        logger.exception("live bench live.join_latency_ms failed")
        for name in (
            "live.join_latency_ms",
            "live.join_token_mint_ms",
            "live.join_coordinator_rest_ms",
            "live.join_rtc_session_ms",
        ):
            errors.append({"name": name, "reason": str(exc)})
    await _capture(
        "live.audio_e2e_latency_ms",
        lambda: _repeat(
            "live.audio_e2e_latency_ms",
            lambda: _audio_e2e_latency_ms(client),
            runs=runs,
            unit="ms",
            higher_is_better=False,
            extra={"marker_freq_hz": MARKER_FREQ_HZ, "marker_ms": MARKER_MS},
        ),
    )

    soak_metrics = (
        ("live.soak_cpu_percent", "cpu_percent", "percent"),
        ("live.soak_rss_baseline_mb", "rss_baseline_mb", "mb"),
        ("live.soak_rss_steady_median_mb", "rss_steady_median_mb", "mb"),
        ("live.soak_rss_peak_mb", "rss_peak_mb", "mb"),
        ("live.soak_rss_growth_slope_mb_per_s", "rss_growth_slope_mb_per_s", "mb_per_s"),
    )
    try:
        soak_runs: list[dict[str, float]] = []
        for i in range(SOAK_REPEATS):
            logger.info(
                "live soak %d/%d for %.1fs", i + 1, SOAK_REPEATS, soak_seconds
            )
            soak_runs.append(await _soak(client, seconds=soak_seconds))
        extra = {
            "duration_s": soak_seconds,
            "repeats": SOAK_REPEATS,
            "warmup_s": soak_runs[0]["warmup_s"],
            "rss_sample_interval_s": RSS_SAMPLE_INTERVAL_S,
        }
        for name, key, unit in soak_metrics:
            results.append(
                summarize(
                    name,
                    [run[key] for run in soak_runs],
                    category="live",
                    unit=unit,
                    higher_is_better=False,
                    extra=extra,
                )
            )
    except Exception as exc:
        logger.exception("live soak failed")
        for name, _key, _unit in soak_metrics:
            errors.append({"name": name, "reason": str(exc)})

    await _capture(
        "live.reconnect_recovery_ms",
        lambda: _repeat(
            "live.reconnect_recovery_ms",
            lambda: _reconnect_recovery_ms(client),
            runs=reconnect_runs,
            unit="ms",
            higher_is_better=False,
        ),
    )
    return results, skipped, errors
