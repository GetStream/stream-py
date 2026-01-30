"""
Handles getStats() and delta compression for a PeerConnection.
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

logger = logging.getLogger(__name__)


def _sanitize_value(value: Any) -> Any:
    """Sanitize a value for JSON serialization."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return int(value.timestamp() * 1000)
    if isinstance(value, dict):
        return {str(k): _sanitize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize_value(v) for v in value]
    return str(value)


@dataclass
class ComputedStats:
    """Computed stats with delta compression and performance metrics."""

    stats: Any  # Raw RTCStatsReport
    delta: Dict[str, Any]  # Delta-compressed stats
    performance_stats: List[models_pb2.PerformanceStats] = field(default_factory=list)


class StatsTracer:
    """Handles getStats() and delta compression for a PeerConnection.

    Provides:
    - Delta compression to reduce size by ~90%
    - Performance stats calculation (encode/decode metrics)
    - Frame time and FPS history for averaging
    - Integration with VideoFrameTracker/BufferedMediaTrack for frame metrics
    """

    def __init__(self, pc, peer_type: str, interval_s: float = 8.0):
        """Initialize StatsTracer for a peer connection.

        Args:
            pc: The RTCPeerConnection to collect stats from
            peer_type: "publisher" or "subscriber"
            interval_s: Interval between stats collections in seconds (for FPS calculation)
        """
        self._pc = pc
        self._peer_type = peer_type
        self._interval_s = interval_s
        self._previous_stats: Dict[str, Dict] = {}
        self._frame_time_history: List[float] = []
        self._fps_history: List[float] = []
        self._frame_tracker: Optional[Any] = None

    def set_frame_tracker(self, tracker: Any) -> None:
        """Set the frame tracker for publisher stats (video track wrapper)."""
        self._frame_tracker = tracker

    async def get(self) -> ComputedStats:
        """Get stats with delta compression and performance metrics.

        Returns:
            ComputedStats with raw stats, delta-compressed stats, and performance metrics
        """
        report = await self._pc.getStats()
        current_stats = self._report_to_dict(report)

        performance_stats = (
            self._get_decode_stats(current_stats)
            if self._peer_type == "subscriber"
            else self._get_encode_stats(current_stats)
        )

        delta = self._delta_compress(self._previous_stats, current_stats)
        self._previous_stats = current_stats

        self._frame_time_history = self._frame_time_history[-2:]
        self._fps_history = self._fps_history[-2:]

        return ComputedStats(
            stats=report, delta=delta, performance_stats=performance_stats
        )

    def _report_to_dict(self, report) -> Dict[str, Dict]:
        """Convert RTCStatsReport to dict with sanitized values."""
        result = {}

        # Handle different report formats
        if hasattr(report, "items"):
            # Dict-like report (aiortc RTCStatsReport)
            for stat_id, stat in report.items():
                stat_values = {}
                if hasattr(stat, "__dict__"):
                    for key, value in vars(stat).items():
                        stat_values[key] = _sanitize_value(value)
                elif isinstance(stat, dict):
                    for key, value in stat.items():
                        stat_values[key] = _sanitize_value(value)
                else:
                    stat_values = {"value": _sanitize_value(stat)}
                result[stat_id] = stat_values
        elif hasattr(report, "__iter__"):
            # List-like report
            for stat in report:
                if hasattr(stat, "id"):
                    stat_id = stat.id
                    stat_values = {}
                    if hasattr(stat, "__dict__"):
                        for key, value in vars(stat).items():
                            stat_values[key] = _sanitize_value(value)
                    else:
                        stat_values = {"id": stat_id}
                    result[stat_id] = stat_values

        # Filter out spurious stats from aiortc (creates sender/receiver for all transceivers)
        # Subscriber shouldn't have outbound-rtp, publisher shouldn't have inbound-rtp
        if self._peer_type == "subscriber":
            result = {
                k: v for k, v in result.items() if v.get("type") != "outbound-rtp"
            }
        elif self._peer_type == "publisher":
            result = {k: v for k, v in result.items() if v.get("type") != "inbound-rtp"}

        # Add codec stats and enhance RTP stats with mid/codecId/mediaType (not provided by aiortc)
        self._add_codec_and_media_stats(result)

        # Add ICE candidate stats (not provided by aiortc getStats)
        self._add_ice_candidate_stats(result)

        # Inject frame stats from tracker (not provided by aiortc)
        self._inject_frame_stats(result)

        return result

    def _delta_compress(
        self, old: Dict[str, Dict], new: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Apply delta compression - only include changed values."""
        try:
            # Deep copy via JSON (values already sanitized by _report_to_dict)
            compressed = json.loads(json.dumps(new))
        except (TypeError, ValueError) as e:
            logger.debug(f"Error serializing stats: {e}")
            compressed = {}

        for stat_id, report in list(compressed.items()):
            if not isinstance(report, dict):
                continue

            # Remove 'id' field as it's redundant (already the key)
            report.pop("id", None)

            if stat_id not in old:
                continue

            # Remove unchanged values
            for name in list(report.keys()):
                if old[stat_id].get(name) == report.get(name):
                    del report[name]

        # Normalize timestamps - set the max timestamp to 0 and store actual value at top level
        max_ts = 0
        for report in compressed.values():
            if isinstance(report, dict):
                ts = report.get("timestamp", 0)
                if isinstance(ts, (int, float)) and ts > max_ts:
                    max_ts = ts

        for report in compressed.values():
            if isinstance(report, dict) and report.get("timestamp") == max_ts:
                report["timestamp"] = 0

        compressed["timestamp"] = max_ts

        return compressed

    def _get_encode_stats(
        self, stats: Dict[str, Dict]
    ) -> List[models_pb2.PerformanceStats]:
        """Calculate encode performance for video outbound-rtp."""
        result = []

        for stat_id, report in stats.items():
            if not isinstance(report, dict):
                continue

            stat_type = report.get("type", "")
            kind = report.get("kind", "")

            if stat_type != "outbound-rtp" or kind != "video":
                continue

            # Skip if we don't have previous stats for this report
            if stat_id not in self._previous_stats:
                continue

            prev_report = self._previous_stats.get(stat_id, {})

            frame_width = report.get("frameWidth", 0)
            frame_height = report.get("frameHeight", 0)

            total_encode_time = report.get("totalEncodeTime", 0)
            prev_total_encode_time = prev_report.get("totalEncodeTime", 0)
            delta_total_encode_time = total_encode_time - prev_total_encode_time

            frames_sent = report.get("framesSent", 0)
            prev_frames_sent = prev_report.get("framesSent", 0)
            delta_frames_sent = frames_sent - prev_frames_sent

            frame_encode_time_ms = 0.0
            if delta_frames_sent > 0:
                frame_encode_time_ms = (
                    delta_total_encode_time / delta_frames_sent
                ) * 1000
            self._frame_time_history.append(frame_encode_time_ms)

            frames_per_second = report.get("framesPerSecond", 0)
            self._fps_history.append(frames_per_second)

            avg_frame_time_ms = (
                sum(self._frame_time_history) / len(self._frame_time_history)
                if self._frame_time_history
                else 0.0
            )
            avg_fps = (
                sum(self._fps_history) / len(self._fps_history)
                if self._fps_history
                else 0.0
            )

            target_bitrate = report.get("targetBitrate", 0)
            codec_id = report.get("codecId", "")
            codec = self._get_codec_from_stats(stats, codec_id)

            perf_stats = models_pb2.PerformanceStats(
                track_type=models_pb2.TRACK_TYPE_VIDEO,
                codec=codec,
                avg_frame_time_ms=avg_frame_time_ms,
                avg_fps=avg_fps,
                video_dimension=models_pb2.VideoDimension(
                    width=frame_width, height=frame_height
                ),
                target_bitrate=int(target_bitrate),
            )
            result.append(perf_stats)

        return result

    def _get_decode_stats(
        self, stats: Dict[str, Dict]
    ) -> List[models_pb2.PerformanceStats]:
        """Calculate decode performance for highest-res video inbound-rtp."""
        result = []

        best_report = None
        best_stat_id = None
        best_resolution = 0

        for stat_id, report in stats.items():
            if not isinstance(report, dict):
                continue
            if report.get("type") != "inbound-rtp" or report.get("kind") != "video":
                continue

            resolution = report.get("frameWidth", 0) * report.get("frameHeight", 0)
            if resolution > best_resolution:
                best_resolution = resolution
                best_report = report
                best_stat_id = stat_id

        if best_report is None or best_stat_id not in self._previous_stats:
            return result

        report = best_report
        prev_report = self._previous_stats.get(best_stat_id, {})

        frame_width = report.get("frameWidth", 0)
        frame_height = report.get("frameHeight", 0)

        total_decode_time = report.get("totalDecodeTime", 0)
        prev_total_decode_time = prev_report.get("totalDecodeTime", 0)
        delta_total_decode_time = total_decode_time - prev_total_decode_time

        frames_decoded = report.get("framesDecoded", 0)
        prev_frames_decoded = prev_report.get("framesDecoded", 0)
        delta_frames_decoded = frames_decoded - prev_frames_decoded

        frame_decode_time_ms = 0.0
        if delta_frames_decoded > 0:
            frame_decode_time_ms = (
                delta_total_decode_time / delta_frames_decoded
            ) * 1000
        self._frame_time_history.append(frame_decode_time_ms)

        frames_per_second = report.get("framesPerSecond", 0)
        self._fps_history.append(frames_per_second)

        avg_frame_time_ms = (
            sum(self._frame_time_history) / len(self._frame_time_history)
            if self._frame_time_history
            else 0.0
        )
        avg_fps = (
            sum(self._fps_history) / len(self._fps_history)
            if self._fps_history
            else 0.0
        )
        codec_id = report.get("codecId", "")
        codec = self._get_codec_from_stats(stats, codec_id)

        perf_stats = models_pb2.PerformanceStats(
            track_type=models_pb2.TRACK_TYPE_VIDEO,
            codec=codec,
            avg_frame_time_ms=avg_frame_time_ms,
            avg_fps=avg_fps,
            video_dimension=models_pb2.VideoDimension(
                width=frame_width, height=frame_height
            ),
            target_bitrate=0,  # Not applicable for decode
        )
        result.append(perf_stats)

        return result

    def _get_codec_from_stats(
        self, stats: Dict[str, Dict], codec_id: str
    ) -> Optional[models_pb2.Codec]:
        """Get codec info from stats, or None if not found."""
        if not codec_id:
            return None

        codec_report = stats.get(codec_id)
        if not codec_report or not isinstance(codec_report, dict):
            return None

        return models_pb2.Codec(
            payload_type=codec_report.get("payloadType", 0),
            name=codec_report.get("mimeType", "").split("/")[-1],
            clock_rate=codec_report.get("clockRate", 0),
        )

    def _candidate_id(self, candidate, transport_index: int) -> str:
        """Generate stable 8-char hex ID for a candidate."""
        foundation = getattr(candidate, "foundation", "")
        component = getattr(candidate, "component", 1)
        ip = getattr(candidate, "ip", None) or getattr(candidate, "host", "")
        port = getattr(candidate, "port", 0)
        key = f"{foundation}:{component}:{ip}:{port}:{transport_index}"
        return hashlib.md5(key.encode()).hexdigest()[:8]

    def _pair_state_to_string(self, state) -> str:
        """Convert CandidatePair.State enum to JS SDK string."""
        from aioice.ice import CandidatePair

        mapping = {
            CandidatePair.State.FROZEN: "frozen",
            CandidatePair.State.WAITING: "waiting",
            CandidatePair.State.IN_PROGRESS: "in-progress",
            CandidatePair.State.SUCCEEDED: "succeeded",
            CandidatePair.State.FAILED: "failed",
        }
        return mapping.get(state, "unknown")

    def _add_ice_candidate_stats(self, result: Dict[str, Dict]) -> None:
        """Add ICE candidate stats not provided by aiortc getStats()."""
        try:
            from aioice.ice import CandidatePair

            ice_transports = getattr(
                self._pc, "_RTCPeerConnection__iceTransports", set()
            )

            for transport_index, transport in enumerate(ice_transports):
                transport_id = f"transport_{transport_index}"

                gatherer = getattr(transport, "iceGatherer", None)
                if gatherer:
                    for candidate in gatherer.getLocalCandidates():
                        cid = self._candidate_id(candidate, transport_index)
                        result[cid] = {
                            "type": "local-candidate",
                            "address": candidate.ip,
                            "candidateType": candidate.type,
                            "port": candidate.port,
                            "priority": candidate.priority,
                            "protocol": candidate.protocol.lower(),
                            "timestamp": 0,
                        }

                for candidate in transport.getRemoteCandidates():
                    cid = self._candidate_id(candidate, transport_index)
                    ip = getattr(candidate, "ip", None) or getattr(
                        candidate, "host", ""
                    )
                    protocol = getattr(candidate, "protocol", "") or getattr(
                        candidate, "transport", "udp"
                    )
                    result[cid] = {
                        "type": "remote-candidate",
                        "address": ip,
                        "candidateType": candidate.type,
                        "port": candidate.port,
                        "priority": candidate.priority,
                        "protocol": protocol.lower(),
                        "timestamp": 0,
                    }

                connection = getattr(transport, "_connection", None)
                if not connection:
                    continue

                check_list = getattr(connection, "_check_list", [])
                nominated = getattr(connection, "_nominated", {})

                for pair in check_list:
                    local_id = self._candidate_id(pair.local_candidate, transport_index)
                    remote_id = self._candidate_id(
                        pair.remote_candidate, transport_index
                    )

                    is_nominated = any(p is pair for p in nominated.values())
                    is_selected = (
                        is_nominated and pair.state == CandidatePair.State.SUCCEEDED
                    )
                    is_connected = pair.state == CandidatePair.State.SUCCEEDED

                    pair_key = f"{local_id}:{remote_id}:{transport_index}"
                    pair_id = hashlib.md5(pair_key.encode()).hexdigest()[:8]

                    result[pair_id] = {
                        "type": "candidate-pair",
                        "localCandidateId": local_id,
                        "remoteCandidateId": remote_id,
                        "state": self._pair_state_to_string(pair.state),
                        "nominated": is_nominated,
                        "selected": is_selected,
                        "priority": min(
                            getattr(pair.local_candidate, "priority", 0),
                            getattr(pair.remote_candidate, "priority", 0),
                        ),
                        "transportId": transport_id,
                        "readable": is_connected,
                        "writable": is_connected,
                        "bytesReceived": 0,
                        "bytesSent": 0,
                        "currentRoundTripTime": 0,
                        "totalRoundTripTime": 0,
                        "lastPacketReceivedTimestamp": 0,
                        "lastPacketSentTimestamp": 0,
                        "responsesReceived": 0,
                        "timestamp": 0,
                    }

        except Exception as e:
            logger.debug(f"Failed to extract ICE candidate stats: {e}")

    def _add_codec_and_media_stats(self, result: Dict[str, Dict]) -> None:
        """Add codec stats and enhance RTP stats with mid/codecId/mediaType.

        aiortc doesn't include codec stats entries or mid/codecId fields in RTP stats.
        This method adds them to match the JS SDK format by reading from transceivers.
        """
        try:
            transceivers = self._pc.getTransceivers()

            # Build mapping of SSRC -> transceiver info
            ssrc_to_transceiver: Dict[int, Dict[str, Any]] = {}
            codec_entries: Dict[str, Dict[str, Any]] = {}

            for transceiver in transceivers:
                mid = transceiver.mid
                kind = transceiver.kind
                codecs = getattr(transceiver, "_codecs", [])

                # Get sender SSRC
                sender = transceiver.sender
                sender_ssrc = getattr(sender, "_ssrc", None)
                if sender_ssrc:
                    ssrc_to_transceiver[sender_ssrc] = {
                        "mid": mid,
                        "kind": kind,
                        "codecs": codecs,
                    }

                # Get receiver SSRCs (may have multiple from remote streams)
                receiver = transceiver.receiver
                # aiortc stores remote SSRCs in __remote_streams dict
                remote_streams = getattr(
                    receiver, "_RTCRtpReceiver__remote_streams", {}
                )
                for recv_ssrc in remote_streams.keys():
                    ssrc_to_transceiver[recv_ssrc] = {
                        "mid": mid,
                        "kind": kind,
                        "codecs": codecs,
                    }

                # Create codec stats entries for this transceiver
                for codec in codecs:
                    codec_id = self._codec_id(codec, mid)
                    if codec_id not in codec_entries:
                        codec_type = (
                            "encode" if self._peer_type == "publisher" else "decode"
                        )
                        codec_entries[codec_id] = {
                            "type": "codec",
                            "payloadType": codec.payloadType,
                            "mimeType": codec.mimeType,
                            "clockRate": codec.clockRate,
                            "codecType": codec_type,
                            "timestamp": 0,
                        }
                        # Add channels for audio codecs
                        if kind == "audio":
                            channels = getattr(codec, "channels", None)
                            if channels:
                                codec_entries[codec_id]["channels"] = channels
                        # Add sdpFmtpLine if parameters exist
                        params = getattr(codec, "parameters", {})
                        if params:
                            fmtp_parts = [f"{k}={v}" for k, v in params.items()]
                            if fmtp_parts:
                                codec_entries[codec_id]["sdpFmtpLine"] = ";".join(
                                    fmtp_parts
                                )

            # Enhance RTP stats with mid, codecId, and mediaType
            for stat in result.values():
                if not isinstance(stat, dict):
                    continue

                stat_type = stat.get("type", "")
                if stat_type not in (
                    "outbound-rtp",
                    "inbound-rtp",
                    "remote-inbound-rtp",
                    "remote-outbound-rtp",
                ):
                    continue

                ssrc = stat.get("ssrc")
                if ssrc is None:
                    continue

                transceiver_info = ssrc_to_transceiver.get(ssrc)
                if transceiver_info:
                    # Add mid if available
                    if transceiver_info["mid"] is not None:
                        stat["mid"] = transceiver_info["mid"]

                    # Add mediaType (same as kind, but JS SDK includes both)
                    kind = transceiver_info["kind"]
                    if kind:
                        stat["mediaType"] = kind

                    # Add codecId linking to first matching codec
                    codecs = transceiver_info["codecs"]
                    if codecs:
                        # Use first non-RTX codec
                        for codec in codecs:
                            if not getattr(codec, "mimeType", "").endswith("/rtx"):
                                codec_id = self._codec_id(
                                    codec, transceiver_info["mid"]
                                )
                                stat["codecId"] = codec_id
                                break

            # Add codec entries to result
            result.update(codec_entries)

        except Exception as e:
            logger.debug(f"Failed to add codec/media stats: {e}")

    def _codec_id(self, codec, mid: Optional[str]) -> str:
        """Generate stable 8-char hex ID for a codec."""
        mime_type = getattr(codec, "mimeType", "")
        payload_type = getattr(codec, "payloadType", 0)
        clock_rate = getattr(codec, "clockRate", 0)
        key = f"{mime_type}:{payload_type}:{clock_rate}:{mid}"
        return hashlib.md5(key.encode()).hexdigest()[:8]

    def _inject_frame_stats(self, result: Dict[str, Dict]) -> None:
        """Inject frame stats from trackers into RTP stats.

        aiortc doesn't provide frame metrics (dimensions, frame count, encode/decode time).
        We inject these from our frame trackers into the appropriate RTP stats entries.
        """
        if self._peer_type == "publisher":
            self._inject_publisher_stats(result)
        else:
            self._inject_subscriber_stats(result)

    def _inject_publisher_stats(self, result: Dict[str, Dict]) -> None:
        """Inject stats for publisher (outbound-rtp)."""
        if not self._frame_tracker:
            return

        try:
            frame_stats = self._frame_tracker.get_frame_stats()
            if frame_stats.get("framesSent", 0) == 0:
                return

            for stat in result.values():
                if not isinstance(stat, dict):
                    continue
                if stat.get("kind") != "video" or stat.get("type") != "outbound-rtp":
                    continue

                stat["framesSent"] = frame_stats["framesSent"]
                stat["frameWidth"] = frame_stats["frameWidth"]
                stat["frameHeight"] = frame_stats["frameHeight"]
                stat["totalEncodeTime"] = frame_stats["totalEncodeTime"]

                if self._previous_stats:
                    prev = self._previous_stats.get(stat.get("id", ""), {})
                    delta = frame_stats["framesSent"] - prev.get("framesSent", 0)
                    if delta > 0:
                        stat["framesPerSecond"] = delta / self._interval_s

        except Exception as e:
            logger.debug(f"Failed to inject publisher stats: {e}")

    def _inject_subscriber_stats(self, result: Dict[str, Dict]) -> None:
        """Inject frame stats for subscriber (inbound-rtp video).

        Note: When multiple video tracks exist (e.g., webcam + screenshare),
        get_video_frame_tracker() returns the first by insertion order, which
        may not match the actively consumed track. This is a known limitation;
        _get_decode_stats() mitigates by selecting the highest-resolution track
        for performance calculations.
        """
        # Get video tracker from PC if not set
        if not self._frame_tracker and hasattr(self._pc, "get_video_frame_tracker"):
            self._frame_tracker = self._pc.get_video_frame_tracker()

        if not self._frame_tracker:
            return

        try:
            frame_stats = self._frame_tracker.get_frame_stats()
            if frame_stats.get("framesDecoded", 0) == 0:
                return

            for stat in result.values():
                if not isinstance(stat, dict):
                    continue
                if stat.get("type") != "inbound-rtp" or stat.get("kind") != "video":
                    continue

                stat["framesDecoded"] = frame_stats["framesDecoded"]
                stat["frameWidth"] = frame_stats["frameWidth"]
                stat["frameHeight"] = frame_stats["frameHeight"]
                stat["totalDecodeTime"] = frame_stats["totalDecodeTime"]

                if self._previous_stats:
                    prev = self._previous_stats.get(stat.get("id", ""), {})
                    delta = frame_stats["framesDecoded"] - prev.get("framesDecoded", 0)
                    if delta > 0:
                        stat["framesPerSecond"] = delta / self._interval_s

        except Exception as e:
            logger.debug(f"Failed to inject subscriber stats: {e}")
