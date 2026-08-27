"""Live SFU benchmarks. Skip unless STREAM_API_KEY and STREAM_API_SECRET are set."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import Any

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


async def _join_latency_ms(client: AsyncStream) -> float:
    call = client.video.call("default", f"bench-join-{uuid.uuid4().hex[:12]}")
    user_id = f"bench-join-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, user_id)
    t0 = time.perf_counter()
    async with await join(call, user_id) as connection:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        await connection.leave()
    return latency_ms


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


async def _soak(
    client: AsyncStream, *, seconds: float
) -> tuple[float, float]:
    """Publish + subscribe for `seconds`; return (cpu_percent, peak_rss_mb)."""
    import soundfile as sf

    data, sample_rate = sf.read(str(TONE_16K), dtype="int16")
    source = np.asarray(data).ravel()
    call = client.video.call("default", f"bench-soak-{uuid.uuid4().hex[:12]}")
    pub_id = f"bench-soak-pub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-soak-sub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)

    rss_samples: list[int] = [current_rss_bytes()]
    cpu_start = time.process_time()
    wall_start = time.monotonic()

    async with await join(call, sub_id) as subscriber:

        @subscriber.on("audio")
        def _on_audio(pcm: PcmData, *args: Any) -> None:
            return

        async with await join(call, pub_id) as publisher:
            track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
            await publisher.add_tracks(audio=track)
            await asyncio.sleep(1.0)
            chunk = int(sample_rate * 0.1)
            offset = 0
            deadline = time.monotonic() + seconds
            while time.monotonic() < deadline:
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
                rss_samples.append(current_rss_bytes())
                await asyncio.sleep(0.05)
            track.stop()

    wall = time.monotonic() - wall_start
    cpu_percent = ((time.process_time() - cpu_start) / wall) * 100.0 if wall > 0 else 0.0
    peak_rss_mb = max(rss_samples) / (1024 * 1024)
    return cpu_percent, peak_rss_mb


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

    await _capture(
        "live.join_latency_ms",
        lambda: _repeat(
            "live.join_latency_ms",
            lambda: _join_latency_ms(client),
            runs=runs,
            unit="ms",
            higher_is_better=False,
        ),
    )
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

    soak_name_cpu = "live.soak_cpu_percent"
    soak_name_rss = "live.soak_rss_mb"
    try:
        logger.info("live soak for %.1fs", soak_seconds)
        cpu_percent, rss_mb = await _soak(client, seconds=soak_seconds)
        extra = {"duration_s": soak_seconds}
        results.append(
            summarize(
                soak_name_cpu,
                [cpu_percent],
                category="live",
                unit="percent",
                higher_is_better=False,
                extra=extra,
            )
        )
        results.append(
            summarize(
                soak_name_rss,
                [rss_mb],
                category="live",
                unit="mb",
                higher_is_better=False,
                extra=extra,
            )
        )
    except Exception as exc:
        logger.exception("live soak failed")
        errors.append({"name": soak_name_cpu, "reason": str(exc)})
        errors.append({"name": soak_name_rss, "reason": str(exc)})

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
