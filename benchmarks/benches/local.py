"""Local, deterministic RTC microbenchmarks.

These exercise public stream-py media helpers (PcmData, AudioStreamTrack) and
the encoder/decoder path the current RTC stack uses. They do not require Stream
API credentials and are backend-agnostic at the call site: encoder classes are
resolved from the loaded stack when present.
"""

from __future__ import annotations

import fractions
import gc
import logging
import time
from typing import Any, Callable

import av
import numpy as np
import soundfile as sf

from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.track_util import AudioFormat, PcmData, VideoFrameTracker

from benchmarks._support import SPEECH_16K, SPEECH_48K, summarize

logger = logging.getLogger("benchmarks.local")

VIDEO_TIME_BASE = fractions.Fraction(1, 30)


def _load_pcm(path) -> PcmData:
    data, sample_rate = sf.read(str(path), dtype="int16")
    if data.ndim == 1:
        samples = data
        channels = 1
    else:
        samples = data.T
        channels = data.shape[1]
    return PcmData(
        samples=samples,
        sample_rate=int(sample_rate),
        format=AudioFormat.S16,
        channels=channels,
    )


def _timed(fn: Callable[[], None], *, warmup: int, iterations: int) -> list[float]:
    for _ in range(warmup):
        fn()
    gc.collect()
    samples: list[float] = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        samples.append(time.perf_counter() - t0)
    return samples


def _throughput(
    fn: Callable[[], None],
    *,
    work_units: float,
    warmup: int,
    iterations: int,
) -> list[float]:
    elapsed = _timed(fn, warmup=warmup, iterations=iterations)
    return [work_units / e if e > 0 else 0.0 for e in elapsed]


def _make_i420_frame(width: int, height: int, pts: int) -> av.VideoFrame:
    rgb = np.empty((height, width, 3), dtype=np.uint8)
    rgb[:, :, 0] = (pts * 3) % 255
    rgb[:, :, 1] = 128
    rgb[:, :, 2] = 200
    frame = av.VideoFrame.from_ndarray(rgb, format="rgb24").reformat(format="yuv420p")
    frame.pts = pts
    frame.time_base = VIDEO_TIME_BASE
    return frame


def _pcm_sample_count(pcm: PcmData) -> int:
    if pcm.samples.ndim == 2:
        if pcm.samples.shape[0] == pcm.channels:
            return int(pcm.samples.shape[1])
        return int(pcm.samples.shape[0])
    return int(pcm.samples.shape[0])


def _resolve_video_encoders() -> list[tuple[str, Callable[[], Any]]]:
    try:
        from getstream.video.rtc.encoders_patches import (
            StreamH264Encoder,
            StreamVp8Encoder,
        )

        if StreamH264Encoder is not None and StreamVp8Encoder is not None:
            return [("h264", StreamH264Encoder), ("vp8", StreamVp8Encoder)]
    except ImportError:
        pass
    from aiortc.codecs.h264 import H264Encoder
    from aiortc.codecs.vpx import Vp8Encoder

    return [("h264", H264Encoder), ("vp8", Vp8Encoder)]


def _bench_pcm_resample(
    *, iterations: int, warmup: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    speech_16k = _load_pcm(SPEECH_16K)
    speech_48k = _load_pcm(SPEECH_48K)
    n_16k = _pcm_sample_count(speech_16k)
    n_48k = _pcm_sample_count(speech_48k)

    benches = [
        (
            "pcm_resample_16k_to_48k",
            lambda: speech_16k.resample(48000),
            n_16k,
        ),
        (
            "pcm_resample_48k_to_16k",
            lambda: speech_48k.resample(16000),
            n_48k,
        ),
        (
            "pcm_resample_mono_to_stereo",
            lambda: speech_16k.resample(16000, target_channels=2),
            n_16k,
        ),
    ]
    for name, fn, units in benches:
        try:
            samples = _throughput(
                fn, work_units=units, warmup=warmup, iterations=iterations
            )
            results.append(
                summarize(
                    name,
                    samples,
                    category="local",
                    unit="samples_per_sec",
                    higher_is_better=True,
                    extra={"input_samples": units},
                )
            )
        except Exception as exc:
            logger.exception("local bench %s failed", name)
            errors.append({"name": name, "reason": str(exc)})
    return results, errors


async def _bench_audio_track_pacing(
    *, iterations: int,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Measure AudioStreamTrack recv() interval and jitter over 20ms frames."""
    name_interval = "audio_track_pacing_interval_ms"
    name_jitter = "audio_track_pacing_jitter_ms"
    frames_per_run = 50
    interval_samples: list[float] = []
    jitter_samples: list[float] = []
    try:
        for _ in range(iterations):
            track = AudioStreamTrack(sample_rate=48000, channels=1, format="s16")
            # Queue more than enough 20ms frames so recv never synthesizes silence.
            total_ms = (frames_per_run + 5) * 20
            n = int(48000 * total_ms / 1000)
            pcm = PcmData(
                samples=np.zeros(n, dtype=np.int16),
                sample_rate=48000,
                format=AudioFormat.S16,
                channels=1,
            )
            await track.write(pcm)
            stamps: list[float] = []
            for _ in range(frames_per_run):
                await track.recv()
                stamps.append(time.perf_counter())
            track.stop()
            deltas_ms = [
                (stamps[i] - stamps[i - 1]) * 1000.0 for i in range(1, len(stamps))
            ]
            interval_samples.append(float(np.mean(deltas_ms)))
            jitter_samples.append(float(np.std(deltas_ms)))
        return [
            summarize(
                name_interval,
                interval_samples,
                category="local",
                unit="ms",
                higher_is_better=False,
                extra={"expected_ms": 20.0, "frames_per_run": frames_per_run},
            ),
            summarize(
                name_jitter,
                jitter_samples,
                category="local",
                unit="ms",
                higher_is_better=False,
                extra={"frames_per_run": frames_per_run},
            ),
        ], []
    except Exception as exc:
        logger.exception("audio track pacing bench failed")
        return [], [
            {"name": name_interval, "reason": str(exc)},
            {"name": name_jitter, "reason": str(exc)},
        ]


class _ImmediateVideoTrack:
    kind = "video"

    def __init__(self, frames: list[av.VideoFrame]):
        self._frames = frames
        self._index = 0
        self.id = "bench-video"
        self.readyState = "live"

    async def recv(self) -> av.VideoFrame:
        if self._index >= len(self._frames):
            raise EOFError("no more frames")
        frame = self._frames[self._index]
        self._index += 1
        copied = av.VideoFrame.from_ndarray(
            frame.to_ndarray(), format=frame.format.name
        )
        copied.pts = frame.pts
        copied.time_base = frame.time_base
        return copied

    def stop(self) -> None:
        self.readyState = "ended"


async def _bench_video_passthrough(
    *, iterations: int, warmup: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    for width, height, label in ((640, 480, "480p"), (1280, 720, "720p")):
        name = f"video_passthrough_{label}_fps"
        frames_per_run = 60
        try:
            frames = [_make_i420_frame(width, height, i) for i in range(frames_per_run)]

            async def _drain(source_frames: list[av.VideoFrame] = frames) -> None:
                track = _ImmediateVideoTrack(source_frames)
                wrapped = VideoFrameTracker(track)
                for _ in range(len(source_frames)):
                    await wrapped.recv()
                wrapped.stop()
                track.stop()

            for _ in range(warmup):
                await _drain()
            gc.collect()
            samples: list[float] = []
            for _ in range(iterations):
                t0 = time.perf_counter()
                await _drain()
                elapsed = time.perf_counter() - t0
                samples.append(frames_per_run / elapsed if elapsed > 0 else 0.0)
            results.append(
                summarize(
                    name,
                    samples,
                    category="local",
                    unit="fps",
                    higher_is_better=True,
                    extra={"width": width, "height": height, "frames": frames_per_run},
                )
            )
        except Exception as exc:
            logger.exception("video passthrough %s failed", label)
            errors.append({"name": name, "reason": str(exc)})
    return results, errors


def _bench_video_encode(
    *, iterations: int, warmup: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []
    encoders = _resolve_video_encoders()
    for codec_name, encoder_cls in encoders:
        for width, height, label in ((640, 480, "480p"), (1280, 720, "720p")):
            name = f"{codec_name}_encode_{label}_fps"
            frames_per_run = 30
            try:
                frames = [
                    _make_i420_frame(width, height, i) for i in range(frames_per_run)
                ]

                def _encode(
                    cls: Callable[[], Any] = encoder_cls,
                    source: list[av.VideoFrame] = frames,
                ) -> None:
                    encoder = cls()
                    for i, frame in enumerate(source):
                        encoder.encode(frame, force_keyframe=(i == 0))

                samples = _throughput(
                    _encode,
                    work_units=frames_per_run,
                    warmup=warmup,
                    iterations=iterations,
                )
                results.append(
                    summarize(
                        name,
                        samples,
                        category="local",
                        unit="fps",
                        higher_is_better=True,
                        extra={
                            "width": width,
                            "height": height,
                            "frames": frames_per_run,
                            "encoder": encoder_cls.__name__,
                        },
                    )
                )
            except Exception as exc:
                logger.exception("%s failed", name)
                errors.append({"name": name, "reason": str(exc)})
    return results, errors


def _pcm_to_s16_frame(pcm: PcmData, offset: int, samples: int) -> av.AudioFrame:
    data = np.asarray(pcm.samples).ravel()[offset : offset + samples]
    if data.size < samples:
        data = np.pad(data, (0, samples - data.size))
    frame = av.AudioFrame.from_ndarray(
        data.reshape(1, -1), format="s16", layout="mono"
    )
    frame.sample_rate = pcm.sample_rate
    frame.pts = offset
    frame.time_base = fractions.Fraction(1, pcm.sample_rate)
    return frame


def _bench_opus_decode(
    *, iterations: int, warmup: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    name = "opus_decode_samples_per_sec"
    try:
        from aiortc.codecs.opus import OpusDecoder, OpusEncoder
        from aiortc.jitterbuffer import JitterFrame
    except ImportError as exc:
        return [], [{"name": name, "reason": f"opus codec unavailable: {exc}"}]

    try:
        speech = _load_pcm(SPEECH_16K).resample(48000)
        frame_samples = 960  # 20ms at 48 kHz
        total = _pcm_sample_count(speech)
        encoder = OpusEncoder()
        packets: list[tuple[bytes, int]] = []
        offset = 0
        while offset + frame_samples <= total:
            frame = _pcm_to_s16_frame(speech, offset, frame_samples)
            payloads, timestamp = encoder.encode(frame)
            if payloads and timestamp is not None:
                packets.append((b"".join(payloads), int(timestamp)))
            offset += frame_samples
        if not packets:
            return [], [{"name": name, "reason": "opus encoder produced no packets"}]
        decoded_samples_per_run = len(packets) * frame_samples

        def _decode() -> None:
            decoder = OpusDecoder()
            for data, ts in packets:
                decoder.decode(JitterFrame(data=data, timestamp=ts))

        samples = _throughput(
            _decode,
            work_units=decoded_samples_per_run,
            warmup=warmup,
            iterations=iterations,
        )
        return [
            summarize(
                name,
                samples,
                category="local",
                unit="samples_per_sec",
                higher_is_better=True,
                extra={
                    "packets": len(packets),
                    "decoded_samples": decoded_samples_per_run,
                },
            )
        ], []
    except Exception as exc:
        logger.exception("opus decode bench failed")
        return [], [{"name": name, "reason": str(exc)}]


async def run_local_benches(
    *, iterations: int, warmup: int
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    results: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    pcm_results, pcm_errors = _bench_pcm_resample(
        iterations=iterations, warmup=warmup
    )
    results.extend(pcm_results)
    errors.extend(pcm_errors)

    pace_results, pace_errors = await _bench_audio_track_pacing(iterations=iterations)
    results.extend(pace_results)
    errors.extend(pace_errors)

    video_results, video_errors = await _bench_video_passthrough(
        iterations=iterations, warmup=warmup
    )
    results.extend(video_results)
    errors.extend(video_errors)

    encode_results, encode_errors = _bench_video_encode(
        iterations=iterations, warmup=warmup
    )
    results.extend(encode_results)
    errors.extend(encode_errors)

    opus_results, opus_errors = _bench_opus_decode(
        iterations=iterations, warmup=warmup
    )
    results.extend(opus_results)
    errors.extend(opus_errors)

    return results, errors
