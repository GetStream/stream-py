import asyncio
import json
import time
from typing import Any, Dict, List, Optional

import aiortc

from getstream.version import VERSION
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2


def _timestamp_ms() -> int:
    return int(time.time() * 1000)


def _sanitize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(k): _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(v) for v in value]
    return str(value)


class StatsTracer:
    def __init__(self, connection_manager) -> None:
        self._connection_manager = connection_manager
        self._trace_buffer: List[List[Any]] = []
        self._trace_lock = asyncio.Lock()

        self._stats_interval_seconds = 8.0
        self._send_interval_seconds = 10.0

        self._running = False
        self._stats_task: Optional[asyncio.Task] = None
        self._send_task: Optional[asyncio.Task] = None
        self._one_off_send_task: Optional[asyncio.Task] = None

        self._prev_stats: Dict[str, Dict[str, Dict[str, Any]]] = {
            "pub": {},
            "sub": {},
        }
        self._last_outbound_stats: Dict[str, Dict[str, Any]] = {}
        self._last_inbound_stats: Dict[str, Dict[str, Any]] = {}
        self._encode_samples: Dict[str, List[Dict[str, Any]]] = {}
        self._decode_samples: Dict[str, List[Dict[str, Any]]] = {}
        self._last_decode_track_id: Optional[str] = None

    def update_stats_options(self, stats_options: Optional[dict]) -> None:
        if not stats_options:
            return
        send_interval_ms = (
            stats_options.get("send_stats_interval_ms")
            or stats_options.get("send_interval_ms")
        )
        rtc_stats_interval_ms = (
            stats_options.get("rtc_stats_interval_ms")
            or stats_options.get("stats_interval_ms")
        )
        if isinstance(send_interval_ms, (int, float)) and send_interval_ms > 0:
            self._send_interval_seconds = float(send_interval_ms) / 1000.0
        if isinstance(rtc_stats_interval_ms, (int, float)) and rtc_stats_interval_ms > 0:
            self._stats_interval_seconds = float(rtc_stats_interval_ms) / 1000.0

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stats_task = asyncio.create_task(self._stats_loop(), name="rtc-stats")
        self._send_task = asyncio.create_task(self._send_loop(), name="rtc-send-stats")

    async def stop(self) -> None:
        self._running = False
        tasks = [t for t in [self._stats_task, self._send_task, self._one_off_send_task] if t]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await self.flush_now()

    def trace(self, tag: str, pc_id: Optional[str], data: Any) -> None:
        record = [tag, pc_id, _sanitize_value(data), _timestamp_ms()]
        asyncio.create_task(self._append_trace(record))

    def trace_rpc(self, method_name: str, payload: Any) -> None:
        self.trace(method_name, None, payload)

    def trace_rpc_failure(self, method_name: str, payload: Any, error: Exception) -> None:
        self.trace(f"{method_name}OnFailure", None, [payload, str(error)])

    def trace_sfu_event(self, tag: str, payload: Any) -> None:
        self.trace(tag, None, payload)

    def trace_coordinator_event(self, tag: str, payload: Any) -> None:
        self.trace(tag, None, payload)

    def schedule_one_off_send(self, delay_seconds: float = 3.0) -> None:
        if self._one_off_send_task:
            self._one_off_send_task.cancel()
        self._one_off_send_task = asyncio.create_task(
            self._delayed_send(delay_seconds), name="rtc-send-stats-once"
        )

    def request_flush(self) -> None:
        asyncio.create_task(self.flush_now())

    async def flush_now(self) -> None:
        await self._send_stats(force=True)

    async def _append_trace(self, record: List[Any]) -> None:
        async with self._trace_lock:
            self._trace_buffer.append(record)

    async def _delayed_send(self, delay_seconds: float) -> None:
        await asyncio.sleep(delay_seconds)
        await self._send_stats(force=True)

    async def _stats_loop(self) -> None:
        while self._running:
            await self._collect_stats()
            await asyncio.sleep(self._stats_interval_seconds)

    async def _send_loop(self) -> None:
        while self._running:
            await asyncio.sleep(self._send_interval_seconds)
            await self._send_stats(force=False)

    async def _collect_stats(self) -> None:
        if not self._connection_manager:
            return
        publisher_pc = self._connection_manager.publisher_pc
        subscriber_pc = self._connection_manager.subscriber_pc
        if publisher_pc and publisher_pc.connectionState != "closed":
            await self._collect_pc_stats(publisher_pc, "pub")
        if subscriber_pc and subscriber_pc.connectionState != "closed":
            await self._collect_pc_stats(subscriber_pc, "sub")

    async def _collect_pc_stats(self, pc: aiortc.RTCPeerConnection, pc_id: str) -> None:
        try:
            report = await pc.getStats()
        except Exception as exc:
            self.trace("getstatsOnFailure", pc_id, str(exc))
            return

        stats_dict = self._stats_report_to_dict(report)
        self._update_performance_stats(stats_dict, pc_id)
        delta = self._delta_compress(self._prev_stats[pc_id], stats_dict)
        self._prev_stats[pc_id] = stats_dict
        self.trace("getstats", pc_id, delta)

    def _stats_report_to_dict(self, report) -> Dict[str, Dict[str, Any]]:
        stats_dict: Dict[str, Dict[str, Any]] = {}
        for stat_id, stat in report.items():
            stat_values = {}
            for key, value in vars(stat).items():
                stat_values[key] = _sanitize_value(value)
            stats_dict[stat_id] = stat_values
        return stats_dict

    def _delta_compress(
        self, old_stats: Dict[str, Dict[str, Any]], new_stats: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        compressed = json.loads(json.dumps(new_stats))
        for stat_id, report in compressed.items():
            report.pop("id", None)
            old_report = old_stats.get(stat_id)
            if not old_report:
                continue
            for name in list(report.keys()):
                if old_report.get(name) == report.get(name):
                    del report[name]

        max_timestamp = float("-inf")
        for report in compressed.values():
            ts = report.get("timestamp")
            if isinstance(ts, (int, float)) and ts > max_timestamp:
                max_timestamp = ts
        if max_timestamp != float("-inf"):
            for report in compressed.values():
                if report.get("timestamp") == max_timestamp:
                    report["timestamp"] = 0
            compressed["timestamp"] = max_timestamp
        return compressed

    def _update_performance_stats(
        self, stats_dict: Dict[str, Dict[str, Any]], pc_id: str
    ) -> None:
        if pc_id == "pub":
            self._update_encode_stats(stats_dict)
        if pc_id == "sub":
            self._update_decode_stats(stats_dict)

    def _update_encode_stats(self, stats_dict: Dict[str, Dict[str, Any]]) -> None:
        codec_map = self._build_codec_map(stats_dict)
        for stat_id, report in stats_dict.items():
            if report.get("type") != "outbound-rtp":
                continue
            if report.get("kind") != "video":
                continue
            prev = self._last_outbound_stats.get(stat_id)
            self._last_outbound_stats[stat_id] = report
            sample = self._build_perf_sample(report, prev, codec_map=codec_map)
            if not sample:
                continue
            samples = self._encode_samples.setdefault(stat_id, [])
            samples.append(sample)
            if len(samples) > 3:
                samples.pop(0)

    def _update_decode_stats(self, stats_dict: Dict[str, Dict[str, Any]]) -> None:
        codec_map = self._build_codec_map(stats_dict)
        best_id, best_area = None, 0
        for stat_id, report in stats_dict.items():
            if report.get("type") != "inbound-rtp":
                continue
            if report.get("kind") != "video":
                continue
            width = report.get("frameWidth") or report.get("width") or 0
            height = report.get("frameHeight") or report.get("height") or 0
            area = int(width) * int(height)
            if area > best_area:
                best_area = area
                best_id = stat_id

        if not best_id:
            return

        report = stats_dict.get(best_id)
        if not report:
            return
        prev = self._last_inbound_stats.get(best_id)
        self._last_inbound_stats[best_id] = report
        sample = self._build_perf_sample(
            report, prev, decode=True, codec_map=codec_map
        )
        if not sample:
            return
        samples = self._decode_samples.setdefault(best_id, [])
        samples.append(sample)
        if len(samples) > 3:
            samples.pop(0)
        self._last_decode_track_id = best_id

    def _build_perf_sample(
        self,
        report: Dict[str, Any],
        prev: Optional[Dict[str, Any]],
        decode: bool = False,
        codec_map: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not prev:
            return None

        timestamp = report.get("timestamp")
        prev_timestamp = prev.get("timestamp")
        if not isinstance(timestamp, (int, float)) or not isinstance(
            prev_timestamp, (int, float)
        ):
            return None
        delta_time_ms = float(timestamp) - float(prev_timestamp)
        if delta_time_ms <= 0:
            return None

        frames_key = "framesDecoded" if decode else "framesEncoded"
        frames = report.get(frames_key)
        prev_frames = prev.get(frames_key)
        if not isinstance(frames, (int, float)) or not isinstance(
            prev_frames, (int, float)
        ):
            if decode:
                frames = report.get("framesReceived")
                prev_frames = prev.get("framesReceived")
        if not isinstance(frames, (int, float)) or not isinstance(
            prev_frames, (int, float)
        ):
            return None
        delta_frames = float(frames) - float(prev_frames)
        if delta_frames <= 0:
            return None

        time_key = "totalDecodeTime" if decode else "totalEncodeTime"
        ms_time_key = "totalDecodeTimeMs" if decode else "totalEncodeTimeMs"
        total_time = report.get(time_key)
        prev_total_time = prev.get(time_key)
        time_multiplier = 1.0
        if not isinstance(total_time, (int, float)) or not isinstance(
            prev_total_time, (int, float)
        ):
            total_time = report.get(ms_time_key)
            prev_total_time = prev.get(ms_time_key)
            time_multiplier = 0.001
        if not isinstance(total_time, (int, float)) or not isinstance(
            prev_total_time, (int, float)
        ):
            return None
        delta_time_seconds = (
            float(total_time) - float(prev_total_time)
        ) * time_multiplier
        if delta_time_seconds <= 0:
            return None

        avg_frame_time_ms = (delta_time_seconds / delta_frames) * 1000.0
        avg_fps = delta_frames / (delta_time_ms / 1000.0)

        width = report.get("frameWidth") or report.get("width")
        height = report.get("frameHeight") or report.get("height")
        codec = self._extract_codec(report, codec_map)
        target_bitrate = report.get("targetBitrate")

        return {
            "avg_frame_time_ms": avg_frame_time_ms,
            "avg_fps": avg_fps,
            "width": int(width) if isinstance(width, (int, float)) else None,
            "height": int(height) if isinstance(height, (int, float)) else None,
            "codec": codec,
            "target_bitrate": int(target_bitrate)
            if isinstance(target_bitrate, (int, float))
            else None,
            "weight": delta_frames,
        }

    def _build_codec_map(
        self, stats_dict: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        codec_map: Dict[str, Dict[str, Any]] = {}
        for stat_id, report in stats_dict.items():
            if report.get("type") != "codec":
                continue
            mime_type = report.get("mimeType")
            name = None
            if isinstance(mime_type, str) and "/" in mime_type:
                name = mime_type.split("/", 1)[1]
            elif isinstance(mime_type, str):
                name = mime_type
            payload_type = report.get("payloadType")
            clock_rate = report.get("clockRate")
            fmtp = report.get("sdpFmtpLine")
            codec_map[stat_id] = {
                "name": name,
                "payload_type": int(payload_type)
                if isinstance(payload_type, (int, float))
                else None,
                "clock_rate": int(clock_rate)
                if isinstance(clock_rate, (int, float))
                else None,
                "fmtp": fmtp if isinstance(fmtp, str) else None,
            }
        return codec_map

    def _extract_codec(
        self, report: Dict[str, Any], codec_map: Optional[Dict[str, Dict[str, Any]]]
    ) -> Optional[Dict[str, Any]]:
        if not codec_map:
            return None
        codec_id = report.get("codecId")
        if not codec_id:
            return None
        return codec_map.get(codec_id)

    def _build_encode_stats(self) -> List[models_pb2.PerformanceStats]:
        return self._build_performance_stats(self._encode_samples)

    def _build_decode_stats(self) -> List[models_pb2.PerformanceStats]:
        if not self._last_decode_track_id:
            return []
        samples = {
            self._last_decode_track_id: self._decode_samples.get(
                self._last_decode_track_id, []
            )
        }
        return self._build_performance_stats(samples)

    def _build_performance_stats(
        self, samples_map: Dict[str, List[Dict[str, Any]]]
    ) -> List[models_pb2.PerformanceStats]:
        stats_list: List[models_pb2.PerformanceStats] = []
        for samples in samples_map.values():
            if not samples:
                continue
            aggregated = self._aggregate_samples(samples)
            if not aggregated:
                continue
            perf = models_pb2.PerformanceStats(
                track_type=models_pb2.TRACK_TYPE_VIDEO,
                avg_frame_time_ms=aggregated["avg_frame_time_ms"],
                avg_fps=aggregated["avg_fps"],
            )
            codec = aggregated.get("codec")
            if codec:
                if codec.get("name"):
                    perf.codec.name = codec["name"]
                if codec.get("payload_type") is not None:
                    perf.codec.payload_type = codec["payload_type"]
                if codec.get("clock_rate") is not None:
                    perf.codec.clock_rate = codec["clock_rate"]
                if codec.get("fmtp"):
                    perf.codec.fmtp = codec["fmtp"]
            if aggregated.get("width") and aggregated.get("height"):
                perf.video_dimension.width = aggregated["width"]
                perf.video_dimension.height = aggregated["height"]
            if aggregated.get("target_bitrate") is not None:
                perf.target_bitrate = aggregated["target_bitrate"]
            stats_list.append(perf)
        return stats_list

    def _aggregate_samples(self, samples: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not samples:
            return None
        weighted_frame_time = 0.0
        weighted_fps = 0.0
        total_weight = 0.0
        width = None
        height = None
        target_bitrate = None
        codec = None
        for sample in samples[-3:]:
            weight = sample.get("weight") or 0.0
            if weight <= 0:
                continue
            weighted_frame_time += sample["avg_frame_time_ms"] * weight
            weighted_fps += sample["avg_fps"] * weight
            total_weight += weight
            if sample.get("width") and sample.get("height"):
                width = sample["width"]
                height = sample["height"]
            if sample.get("target_bitrate") is not None:
                target_bitrate = sample["target_bitrate"]
            if sample.get("codec"):
                codec = sample["codec"]
        if total_weight <= 0:
            return None
        return {
            "avg_frame_time_ms": weighted_frame_time / total_weight,
            "avg_fps": weighted_fps / total_weight,
            "width": width,
            "height": height,
            "target_bitrate": target_bitrate,
            "codec": codec,
        }

    async def _send_stats(self, force: bool) -> None:
        client = self._connection_manager.twirp_signaling_client
        ctx = self._connection_manager.twirp_context
        session_id = self._connection_manager.session_id
        if not client or not ctx or not session_id:
            return

        async with self._trace_lock:
            if not self._trace_buffer and not force:
                return
            traces = self._trace_buffer
            self._trace_buffer = []

        encode_stats = self._build_encode_stats()
        decode_stats = self._build_decode_stats()
        if not traces and not encode_stats and not decode_stats and not force:
            return

        rtc_stats_payload = json.dumps(traces, separators=(",", ":")) if traces else ""
        request = signal_pb2.SendStatsRequest(
            session_id=session_id,
            rtc_stats=rtc_stats_payload,
            sdk="python",
            sdk_version=VERSION,
            webrtc_version=aiortc.__version__,
            encode_stats=encode_stats,
            decode_stats=decode_stats,
        )
        await client.SendStats(ctx=ctx, request=request, server_path_prefix="")
