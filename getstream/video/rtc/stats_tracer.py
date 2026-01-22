"""
Handles getStats() and delta compression for a PeerConnection.
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2

logger = logging.getLogger(__name__)


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
    """

    def __init__(self, pc, peer_type: str):
        """Initialize StatsTracer for a peer connection.

        Args:
            pc: The RTCPeerConnection to collect stats from
            peer_type: "publisher" or "subscriber"
        """
        self._pc = pc
        self._peer_type = peer_type
        self._previous_stats: Dict[str, Dict] = {}
        self._frame_time_history: List[float] = []
        self._fps_history: List[float] = []

    async def get(self) -> ComputedStats:
        """Get stats with delta compression and performance metrics.

        Returns:
            ComputedStats with raw stats, delta-compressed stats, and performance metrics
        """
        report = await self._pc.getStats()
        current_stats = self._report_to_dict(report)

        # Calculate performance stats based on peer type
        performance_stats = (
            self._get_decode_stats(current_stats)
            if self._peer_type == "subscriber"
            else self._get_encode_stats(current_stats)
        )

        # Apply delta compression
        delta = self._delta_compress(self._previous_stats, current_stats)
        self._previous_stats = current_stats

        # Keep last 2 samples for averaging (3 total including current)
        self._frame_time_history = self._frame_time_history[-2:]
        self._fps_history = self._fps_history[-2:]

        return ComputedStats(
            stats=report, delta=delta, performance_stats=performance_stats
        )

    def _report_to_dict(self, report) -> Dict[str, Dict]:
        """Convert RTCStatsReport to dict.

        Args:
            report: The RTCStatsReport from getStats()

        Returns:
            Dict mapping stat IDs to their properties
        """
        result = {}

        # Handle different report formats
        if hasattr(report, "items"):
            # Dict-like report
            for stat_id, stat in report.items():
                if hasattr(stat, "__dict__"):
                    result[stat_id] = dict(vars(stat))
                elif isinstance(stat, dict):
                    result[stat_id] = stat.copy()
                else:
                    result[stat_id] = {"value": stat}
        elif hasattr(report, "__iter__"):
            # List-like report
            for stat in report:
                if hasattr(stat, "id"):
                    stat_id = stat.id
                    if hasattr(stat, "__dict__"):
                        result[stat_id] = dict(vars(stat))
                    else:
                        result[stat_id] = {"id": stat_id}

        return result

    def _delta_compress(
        self, old: Dict[str, Dict], new: Dict[str, Dict]
    ) -> Dict[str, Any]:
        """Apply delta compression - reduces size by ~90%.

        Only includes values that have changed since the previous stats.

        Args:
            old: Previous stats dict
            new: Current stats dict

        Returns:
            Delta-compressed stats dict
        """
        try:
            # Deep copy via JSON to ensure clean serialization
            compressed = json.loads(json.dumps(new, default=str))
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
        """Calculate encode performance for video outbound-rtp.

        Uses delta calculation between current and previous samples,
        matching the JS SDK implementation.

        Args:
            stats: Current stats dict

        Returns:
            List of PerformanceStats for encode metrics
        """
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

            # Extract video dimensions
            frame_width = report.get("frameWidth", 0)
            frame_height = report.get("frameHeight", 0)

            # Calculate delta encode time (time spent encoding per frame)
            total_encode_time = report.get("totalEncodeTime", 0)
            prev_total_encode_time = prev_report.get("totalEncodeTime", 0)
            delta_total_encode_time = total_encode_time - prev_total_encode_time

            frames_sent = report.get("framesSent", 0)
            prev_frames_sent = prev_report.get("framesSent", 0)
            delta_frames_sent = frames_sent - prev_frames_sent

            # Calculate frame encode time from deltas
            frame_encode_time_ms = 0.0
            if delta_frames_sent > 0:
                frame_encode_time_ms = (delta_total_encode_time / delta_frames_sent) * 1000

            self._frame_time_history.append(frame_encode_time_ms)

            # Calculate FPS
            frames_per_second = report.get("framesPerSecond", 0)
            self._fps_history.append(frames_per_second)

            # Average over history (last 3 samples)
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

            # Get target bitrate
            target_bitrate = report.get("targetBitrate", 0)

            # Get codec info
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
        """Calculate decode performance for highest-res video inbound-rtp.

        Uses delta calculation between current and previous samples,
        matching the JS SDK implementation.

        Args:
            stats: Current stats dict

        Returns:
            List of PerformanceStats for decode metrics
        """
        result = []

        # Find the highest resolution inbound video track
        best_report = None
        best_stat_id = None
        best_resolution = 0

        for stat_id, report in stats.items():
            if not isinstance(report, dict):
                continue

            stat_type = report.get("type", "")
            kind = report.get("kind", "")

            if stat_type != "inbound-rtp" or kind != "video":
                continue

            frame_width = report.get("frameWidth", 0)
            frame_height = report.get("frameHeight", 0)
            resolution = frame_width * frame_height

            if resolution > best_resolution:
                best_resolution = resolution
                best_report = report
                best_stat_id = stat_id

        if best_report is None or best_stat_id is None:
            return result

        # Skip if we don't have previous stats for this report
        if best_stat_id not in self._previous_stats:
            return result

        report = best_report
        prev_report = self._previous_stats.get(best_stat_id, {})

        # Extract video dimensions
        frame_width = report.get("frameWidth", 0)
        frame_height = report.get("frameHeight", 0)

        # Calculate delta decode time (time spent decoding per frame)
        total_decode_time = report.get("totalDecodeTime", 0)
        prev_total_decode_time = prev_report.get("totalDecodeTime", 0)
        delta_total_decode_time = total_decode_time - prev_total_decode_time

        frames_decoded = report.get("framesDecoded", 0)
        prev_frames_decoded = prev_report.get("framesDecoded", 0)
        delta_frames_decoded = frames_decoded - prev_frames_decoded

        # Calculate frame decode time from deltas
        frame_decode_time_ms = 0.0
        if delta_frames_decoded > 0:
            frame_decode_time_ms = (delta_total_decode_time / delta_frames_decoded) * 1000

        self._frame_time_history.append(frame_decode_time_ms)

        # Calculate FPS
        frames_per_second = report.get("framesPerSecond", 0)
        self._fps_history.append(frames_per_second)

        # Average over history (last 3 samples)
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

        # Get codec info
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
        """Get codec info from stats.

        Args:
            stats: Current stats dict
            codec_id: The codec stat ID to look up

        Returns:
            Codec proto or None if not found
        """
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
