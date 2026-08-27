"""Live SFU benchmarks. Skip unless STREAM_API_KEY and STREAM_API_SECRET are set."""

from __future__ import annotations

import asyncio
import logging
import statistics
import time
import uuid
from contextlib import contextmanager
from fractions import Fraction
from typing import Any, Iterator

import av
import numpy as np

from getstream.models import (
    AudioSettingsRequest,
    CallRequest,
    CallSettingsRequest,
    UserRequest,
)
from getstream.stream import AsyncStream
from getstream.video.rtc import AudioStreamTrack, PcmData, join
from getstream.video.rtc.reconnection import ReconnectionStrategy
from getstream.video.rtc.track_util import AudioFormat

from benchmarks._support import (
    SPEECH_48K,
    TONE_16K,
    current_nthreads,
    current_rss_bytes,
    gap_metrics,
    outbound_rtp_totals,
    poll_stats,
    rusage_maxrss_bytes,
    summarize,
    video_codec,
)

try:
    from getstream.video.rtc.media import MediaStreamError
except ImportError:
    from aiortc.mediastreams import MediaStreamError


class _StatsUnavailable(RuntimeError):
    """Raised when this RTC stack has no ConnectionManager.stats()."""

logger = logging.getLogger("benchmarks.live")

MARKER_FREQ_HZ = 2500.0
MARKER_MS = 80
GOERTZEL_RATIO = 8.0
SOAK_REPEATS = 3
RSS_SAMPLE_INTERVAL_S = 0.2
BYTES_PER_MB = 1024 * 1024
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 720
VIDEO_FPS = 30.0
VIDEO_SECONDS = 15.0
DTX_SECONDS = 15.0
# DTX bench asks the coordinator for Opus DTX so the join response actually
# has opus_dtx_enabled=True even if the app's default call type leaves it off.
_DTX_CALL_DATA = CallRequest(
    settings_override=CallSettingsRequest(
        audio=AudioSettingsRequest(
            default_device="speaker",
            opus_dtx_enabled=True,
        )
    )
)


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
    orig_join_rtc = None
    try:
        orig_join_rtc = cm.ConnectionManager._join_rtc_session
    except AttributeError:
        logger.info("RtcSession.join probe unavailable on this RTC stack")

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
    if orig_join_rtc is not None:
        cm.ConnectionManager._join_rtc_session = timed_join_rtc_session
    try:
        yield
    finally:
        client.create_token = orig_create_token
        cm.join_call = orig_join_call
        if orig_join_rtc is not None:
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
) -> list[tuple[float, int, int]]:
    samples: list[tuple[float, int, int]] = []
    while not stop.is_set():
        samples.append((time.monotonic(), current_rss_bytes(), current_nthreads()))
        try:
            await asyncio.wait_for(stop.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
    samples.append((time.monotonic(), current_rss_bytes(), current_nthreads()))
    return samples


async def _join_for_soak(call, user_id: str, *, video: bool):
    if not video:
        return await join(call, user_id)
    try:
        from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
            TRACK_TYPE_AUDIO,
            TRACK_TYPE_VIDEO,
        )
        from getstream.video.rtc.tracks import (
            SubscriptionConfig,
            TrackSubscriptionConfig,
        )

        config = SubscriptionConfig(
            default=TrackSubscriptionConfig(
                track_types=[TRACK_TYPE_AUDIO, TRACK_TYPE_VIDEO]
            )
        )
        return await join(call, user_id, subscription_config=config)
    except TypeError:
        return await join(call, user_id)


def _resource_metrics(
    *,
    cpu_start: float,
    wall_start: float,
    cpu_armed: bool,
    joined_at: float,
    warmup_s: float,
    rss_import: int,
    rss_baseline: int,
    series: list[tuple[float, int, int]],
) -> dict[str, float]:
    wall = (time.monotonic() - wall_start) if cpu_armed else 0.0
    cpu_percent = (
        ((time.process_time() - cpu_start) / wall) * 100.0 if wall > 0 else 0.0
    )
    post_join = [row for row in series if row[0] >= joined_at] or series
    peak_rss_mb = (
        max(rss for _, rss, _ in post_join) / BYTES_PER_MB if post_join else 0.0
    )
    warmup_until = joined_at + warmup_s
    steady = [row for row in post_join if row[0] >= warmup_until] or post_join
    steady_mb = [rss / BYTES_PER_MB for _, rss, _ in steady]
    threads = [n for _, _, n in steady]
    slope = _linear_slope(
        [t - warmup_until for t, _, _ in steady],
        steady_mb,
    )
    return {
        "cpu_percent": cpu_percent,
        "rss_import_mb": rss_import / BYTES_PER_MB,
        "rss_baseline_mb": rss_baseline / BYTES_PER_MB,
        "rss_steady_median_mb": float(statistics.median(steady_mb)) if steady_mb else 0.0,
        "rss_peak_mb": peak_rss_mb,
        "rss_maxrss_mb": rusage_maxrss_bytes() / BYTES_PER_MB,
        "rss_growth_slope_mb_per_s": slope,
        "nthreads_median": float(statistics.median(threads)) if threads else 0.0,
        "warmup_s": warmup_s,
    }


async def _soak(
    client: AsyncStream, *, seconds: float, video: bool = False
) -> dict[str, float]:
    """Publish + subscribe for `seconds` in a process that has not just done 30 joins."""
    import soundfile as sf

    rss_import = current_rss_bytes()
    data, sample_rate = sf.read(str(TONE_16K), dtype="int16")
    source = np.asarray(data).ravel()
    kind = "video" if video else "audio"
    call = client.video.call("default", f"bench-soak-{kind}-{uuid.uuid4().hex[:12]}")
    pub_id = f"bench-soak-pub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-soak-sub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)

    warmup_s = _warmup_seconds(seconds)
    baseline_rss = current_rss_bytes()
    stop_sampler = asyncio.Event()
    sampler_task: asyncio.Task[list[tuple[float, int, int]]] | None = None
    cpu_armed = False
    cpu_start = 0.0
    wall_start = 0.0
    joined_at = 0.0
    series: list[tuple[float, int, int]] = []

    try:
        async with await _join_for_soak(call, sub_id, video=video) as subscriber:

            @subscriber.on("audio")
            def _on_audio(pcm: PcmData, *args: Any) -> None:
                return

            async with await _join_for_soak(call, pub_id, video=video) as publisher:
                joined_at = time.monotonic()
                sampler_task = asyncio.create_task(
                    _rss_sampler(stop_sampler, interval=RSS_SAMPLE_INTERVAL_S),
                    name="soak-rss-sampler",
                )
                audio = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
                video_track = _I420VideoTrack() if video else None
                await publisher.add_tracks(audio=audio, video=video_track)
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
                    await audio.write(pcm)
                    offset = end
                    await asyncio.sleep(0.05)
                audio.stop()
                if video_track is not None:
                    video_track.stop()
    finally:
        stop_sampler.set()
        if sampler_task is not None:
            series = await sampler_task

    return _resource_metrics(
        cpu_start=cpu_start,
        wall_start=wall_start,
        cpu_armed=cpu_armed,
        joined_at=joined_at,
        warmup_s=warmup_s,
        rss_import=rss_import,
        rss_baseline=baseline_rss,
        series=series,
    )


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


class _I420VideoTrack:
    """Duck-typed 720p30 I420 source fed through LocalVideoTrack via add_tracks."""

    kind = "video"

    def __init__(
        self,
        width: int = VIDEO_WIDTH,
        height: int = VIDEO_HEIGHT,
        fps: float = VIDEO_FPS,
    ) -> None:
        self._id = str(uuid.uuid4())
        self._ready_state = "live"
        self.width = width
        self.height = height
        self._interval = 1.0 / fps
        self._time_base = Fraction(1, int(fps))
        self._pts = 0
        y = np.full((height, width), 41, dtype=np.uint8)
        u = np.full((height // 4, width), 240, dtype=np.uint8)
        v = np.full((height // 4, width), 110, dtype=np.uint8)
        self._i420 = np.concatenate([y, u, v], axis=0)

    @property
    def id(self) -> str:
        return self._id

    @property
    def readyState(self) -> str:
        return self._ready_state

    def stop(self) -> None:
        self._ready_state = "ended"

    async def recv(self):
        if self._ready_state != "live":
            raise MediaStreamError("Track is ended")
        await asyncio.sleep(self._interval)
        frame = av.VideoFrame.from_ndarray(self._i420, format="yuv420p")
        frame.pts = self._pts
        frame.duration = 1
        frame.time_base = self._time_base
        self._pts += 1
        return frame


async def _write_pcm_for(
    track: AudioStreamTrack, source: np.ndarray, sample_rate: int, seconds: float
) -> None:
    chunk_s = 0.02
    chunk = max(int(sample_rate * chunk_s), 1)
    offset = 0
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and track.readyState == "live":
        end = offset + chunk
        if end > source.size:
            offset = 0
            end = min(chunk, source.size)
        pcm = PcmData(
            samples=source[offset:end],
            sample_rate=int(sample_rate),
            format=AudioFormat.S16,
            channels=1,
        )
        await track.write(pcm)
        offset = end
        await asyncio.sleep(chunk_s)


def _last_snapshot(samples: list[dict[str, Any]]) -> Any:
    for item in reversed(samples):
        if item.get("stats") is not None:
            return item["stats"]
    return None


async def _require_stats(connection: Any) -> None:
    try:
        await connection.stats()
    except AttributeError as exc:
        raise _StatsUnavailable(
            "ConnectionManager.stats() is not available on this RTC stack"
        ) from exc


async def _video_publish_720p30(client: AsyncStream) -> dict[str, Any]:
    call = client.video.call("default", f"bench-video-{uuid.uuid4().hex[:12]}")
    pub_id = f"bench-vpub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-vsub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)
    stop = asyncio.Event()
    samples: list[dict[str, Any]] = []
    async with await join(call, sub_id):
        async with await join(call, pub_id) as publisher:
            await _require_stats(publisher)
            track = _I420VideoTrack()
            await publisher.add_tracks(video=track)
            poller = asyncio.create_task(
                poll_stats(publisher, stop), name="video-stats-poll"
            )
            try:
                await asyncio.sleep(VIDEO_SECONDS)
            finally:
                stop.set()
                samples = await poller
                track.stop()
    snapshot = _last_snapshot(samples)
    totals = outbound_rtp_totals(snapshot, kind="video")
    if totals["packetsSent"] == 0.0 and totals["bytesSent"] == 0.0:
        totals = outbound_rtp_totals(snapshot)
    metrics = gap_metrics(snapshot, kind="video")
    return {
        "bytes_sent": totals["bytesSent"],
        "packets_sent": totals["packetsSent"],
        "nack_count": totals["nackCount"],
        "pli_count": totals["pliCount"],
        "fir_count": totals["firCount"],
        "packets_lost": metrics["packetsLost"],
        "fraction_lost": metrics["fractionLost"],
        "round_trip_time": metrics["roundTripTime"],
        "available_outgoing_bitrate": metrics["availableOutgoingBitrate"],
        "stats_gap": metrics["stats_gap"],
        "gap_metrics": metrics,
        "polls": len(samples),
    }


async def _dtx_bytes_sent(client: AsyncStream, *, speech: bool) -> dict[str, Any]:
    import soundfile as sf

    if speech:
        data, sample_rate = sf.read(str(SPEECH_48K), dtype="int16")
        source = np.asarray(data).ravel()
        label = "speech"
    else:
        sample_rate = 48000
        source = np.zeros(int(sample_rate * DTX_SECONDS), dtype=np.int16)
        label = "silence"
    call = client.video.call("default", f"bench-dtx-{label}-{uuid.uuid4().hex[:12]}")
    pub_id = f"bench-dtx-pub-{uuid.uuid4().hex[:8]}"
    sub_id = f"bench-dtx-sub-{uuid.uuid4().hex[:8]}"
    await _ensure_users(client, pub_id, sub_id)
    stop = asyncio.Event()
    samples: list[dict[str, Any]] = []
    opus_dtx_enabled = False
    async with await join(call, sub_id, data=_DTX_CALL_DATA) as subscriber:

        @subscriber.on("audio")
        def _on_audio(pcm: PcmData, *args: Any) -> None:
            return

        async with await join(call, pub_id) as publisher:
            await _require_stats(publisher)
            opus_dtx_enabled = (
                publisher.join_response.call.settings.audio.opus_dtx_enabled
            )
            track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
            await publisher.add_tracks(audio=track)
            poller = asyncio.create_task(
                poll_stats(publisher, stop), name=f"dtx-{label}-stats-poll"
            )
            try:
                await _write_pcm_for(track, source, int(sample_rate), DTX_SECONDS)
            finally:
                stop.set()
                samples = await poller
                track.stop()
    snapshot = _last_snapshot(samples)
    totals = outbound_rtp_totals(snapshot, kind="audio")
    if totals["packetsSent"] == 0.0 and totals["bytesSent"] == 0.0:
        totals = outbound_rtp_totals(snapshot)
    metrics = gap_metrics(snapshot, kind="audio")
    return {
        "bytes_sent": totals["bytesSent"],
        "packets_sent": totals["packetsSent"],
        "nack_count": totals["nackCount"],
        "packets_lost": metrics["packetsLost"],
        "fraction_lost": metrics["fractionLost"],
        "round_trip_time": metrics["roundTripTime"],
        "available_outgoing_bitrate": metrics["availableOutgoingBitrate"],
        "stats_gap": metrics["stats_gap"],
        "gap_metrics": metrics,
        "polls": len(samples),
        "kind": label,
        "opus_dtx_enabled": opus_dtx_enabled,
    }


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
    failed_runs = 0
    for i in range(runs):
        logger.info("%s run %d/%d", name, i + 1, runs)
        try:
            samples.append(float(await fn()))
        except Exception:
            failed_runs += 1
            logger.exception("%s run %d/%d failed", name, i + 1, runs)
    if not samples:
        raise RuntimeError(f"{name} produced no samples ({failed_runs} failed runs)")
    payload = dict(extra or {})
    payload["failed_runs"] = failed_runs
    return summarize(
        name,
        samples,
        category="live",
        unit=unit,
        higher_is_better=higher_is_better,
        extra=payload,
    )


SOAK_RESOURCE_METRICS = (
    ("cpu_percent", "percent"),
    ("rss_import_mb", "mb"),
    ("rss_baseline_mb", "mb"),
    ("rss_steady_median_mb", "mb"),
    ("rss_peak_mb", "mb"),
    ("rss_maxrss_mb", "mb"),
    ("rss_growth_slope_mb_per_s", "mb_per_s"),
    ("nthreads_median", "count"),
)


async def run_resource_benches(
    *, soak_seconds: float, soak_repeats: int = SOAK_REPEATS
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[dict[str, str]]]:
    """CPU/RSS soaks in this process. Call from a fresh interpreter."""
    results: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    client = _client()

    async def _run_kind(prefix: str, *, video: bool) -> None:
        soak_runs: list[dict[str, float]] = []
        soak_failures = 0
        for i in range(soak_repeats):
            logger.info(
                "%s soak %d/%d for %.1fs", prefix, i + 1, soak_repeats, soak_seconds
            )
            try:
                soak_runs.append(await _soak(client, seconds=soak_seconds, video=video))
            except Exception:
                soak_failures += 1
                logger.exception("%s soak %d/%d failed", prefix, i + 1, soak_repeats)
        if not soak_runs:
            raise RuntimeError(
                f"{prefix} soak produced no samples ({soak_failures} failed repeats)"
            )
        extra = {
            "duration_s": soak_seconds,
            "repeats": soak_repeats,
            "warmup_s": soak_runs[0]["warmup_s"],
            "rss_sample_interval_s": RSS_SAMPLE_INTERVAL_S,
            "failed_runs": soak_failures,
            "isolated_process": True,
            "video": video,
            "video_codec": video_codec() if video else "opus",
        }
        for key, unit in SOAK_RESOURCE_METRICS:
            results.append(
                summarize(
                    f"live.{prefix}_{key}",
                    [run[key] for run in soak_runs],
                    category="live",
                    unit=unit,
                    higher_is_better=False,
                    extra=extra,
                )
            )

    try:
        await _run_kind("soak", video=False)
    except Exception as exc:
        logger.exception("audio resource soak failed")
        for key, _unit in SOAK_RESOURCE_METRICS:
            errors.append({"name": f"live.soak_{key}", "reason": str(exc)})
    try:
        await _run_kind("video_soak", video=True)
    except Exception as exc:
        logger.exception("video resource soak failed")
        for key, _unit in SOAK_RESOURCE_METRICS:
            errors.append({"name": f"live.video_soak_{key}", "reason": str(exc)})
    return results, skipped, errors


async def run_live_benches(
    *, runs: int, reconnect_runs: int
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
        join_failures = 0
        for i in range(runs):
            logger.info("live.join_latency_ms run %d/%d", i + 1, runs)
            try:
                join_runs.append(await _join_once(client))
            except Exception:
                join_failures += 1
                logger.exception("live.join_latency_ms run %d/%d failed", i + 1, runs)
        if not join_runs:
            raise RuntimeError(
                f"live.join_latency_ms produced no samples ({join_failures} failed runs)"
            )
        join_metrics = (
            ("live.join_latency_ms", "total_ms"),
            ("live.join_token_mint_ms", "token_mint_ms"),
            ("live.join_coordinator_rest_ms", "coordinator_rest_ms"),
            ("live.join_rtc_session_ms", "rtc_session_join_ms"),
        )
        for name, key in join_metrics:
            samples = [run[key] for run in join_runs if key in run]
            if len(samples) != len(join_runs):
                skipped.append(
                    {
                        "name": name,
                        "reason": "join probe not available on this RTC stack",
                    }
                )
                continue
            results.append(
                summarize(
                    name,
                    samples,
                    category="live",
                    unit="ms",
                    higher_is_better=False,
                    extra={"failed_runs": join_failures},
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

    video_name = "live.video_publish_720p30_bytes_sent"
    try:
        logger.info("live 720p30 video publish for %.1fs", VIDEO_SECONDS)
        video = await _video_publish_720p30(client)
        extra = {
            "width": VIDEO_WIDTH,
            "height": VIDEO_HEIGHT,
            "fps": VIDEO_FPS,
            "duration_s": VIDEO_SECONDS,
            "packets_sent": video["packets_sent"],
            "nack_count": video["nack_count"],
            "pli_count": video["pli_count"],
            "fir_count": video["fir_count"],
            "packets_lost": video["packets_lost"],
            "fraction_lost": video["fraction_lost"],
            "round_trip_time": video["round_trip_time"],
            "available_outgoing_bitrate": video["available_outgoing_bitrate"],
            "polls": video["polls"],
            "stats_gap": video["stats_gap"],
            "gap_metrics": video["gap_metrics"],
        }
        results.append(
            summarize(
                video_name,
                [video["bytes_sent"]],
                category="live",
                unit="bytes",
                higher_is_better=False,
                extra=extra,
            )
        )
        results.append(
            summarize(
                "live.video_publish_720p30_packets_sent",
                [video["packets_sent"]],
                category="live",
                unit="packets",
                higher_is_better=False,
                extra=extra,
            )
        )
    except _StatsUnavailable as exc:
        logger.info("skipping video publish bench: %s", exc)
        skipped.append({"name": video_name, "reason": str(exc)})
        skipped.append(
            {
                "name": "live.video_publish_720p30_packets_sent",
                "reason": str(exc),
            }
        )
    except Exception as exc:
        logger.exception("live video publish bench failed")
        errors.append({"name": video_name, "reason": str(exc)})
        errors.append(
            {"name": "live.video_publish_720p30_packets_sent", "reason": str(exc)}
        )

    dtx_names = (
        "live.dtx_silence_bytes_sent",
        "live.dtx_speech_bytes_sent",
    )
    try:
        logger.info("live DTX silence vs speech for %.1fs each", DTX_SECONDS)
        silence = await _dtx_bytes_sent(client, speech=False)
        speech = await _dtx_bytes_sent(client, speech=True)
        ratio = (
            silence["bytes_sent"] / speech["bytes_sent"]
            if speech["bytes_sent"]
            else None
        )
        dtx_extra = {
            "duration_s": DTX_SECONDS,
            "silence_packets_sent": silence["packets_sent"],
            "speech_packets_sent": speech["packets_sent"],
            "silence_nack_count": silence["nack_count"],
            "speech_nack_count": speech["nack_count"],
            "silence_packets_lost": silence["packets_lost"],
            "speech_packets_lost": speech["packets_lost"],
            "silence_round_trip_time": silence["round_trip_time"],
            "speech_round_trip_time": speech["round_trip_time"],
            "silence_available_outgoing_bitrate": silence["available_outgoing_bitrate"],
            "speech_available_outgoing_bitrate": speech["available_outgoing_bitrate"],
            "bytes_ratio_silence_over_speech": ratio,
            "silence_stats_gap": silence["stats_gap"],
            "speech_stats_gap": speech["stats_gap"],
            "silence_gap_metrics": silence["gap_metrics"],
            "speech_gap_metrics": speech["gap_metrics"],
            "opus_dtx_enabled": silence["opus_dtx_enabled"]
            and speech["opus_dtx_enabled"],
            "silence_opus_dtx_enabled": silence["opus_dtx_enabled"],
            "speech_opus_dtx_enabled": speech["opus_dtx_enabled"],
        }
        results.append(
            summarize(
                dtx_names[0],
                [silence["bytes_sent"]],
                category="live",
                unit="bytes",
                higher_is_better=False,
                extra=dtx_extra,
            )
        )
        results.append(
            summarize(
                dtx_names[1],
                [speech["bytes_sent"]],
                category="live",
                unit="bytes",
                higher_is_better=False,
                extra=dtx_extra,
            )
        )
    except _StatsUnavailable as exc:
        logger.info("skipping DTX bench: %s", exc)
        for name in dtx_names:
            skipped.append({"name": name, "reason": str(exc)})
    except Exception as exc:
        logger.exception("live DTX bench failed")
        for name in dtx_names:
            errors.append({"name": name, "reason": str(exc)})

    return results, skipped, errors
