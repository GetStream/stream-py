"""
Orchestrates stats collection and sending to SFU.
"""

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import aiortc

from getstream.version import VERSION
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.tracer import TraceSlice
from getstream.video.rtc.stats_tracer import _sanitize_value

if TYPE_CHECKING:
    from getstream.video.rtc.connection_manager import ConnectionManager
    from getstream.video.rtc.stats_tracer import ComputedStats

logger = logging.getLogger(__name__)


def _flatten_stats(report) -> List[Any]:
    """Flatten RTCStatsReport to an array of stats objects.

    Matches the JS SDK's flatten() function which converts
    RTCStatsReport (Map-like) to an array of RTCStats objects.

    Args:
        report: The RTCStatsReport from getStats()

    Returns:
        List of stats objects with sanitized values
    """
    if report is None:
        return []

    stats = []
    if hasattr(report, "items"):
        # Dict-like report (aiortc RTCStatsReport)
        for stat_id, stat in report.items():
            stat_obj = {"id": stat_id}
            if hasattr(stat, "__dict__"):
                for key, value in vars(stat).items():
                    stat_obj[key] = _sanitize_value(value)
            elif isinstance(stat, dict):
                for key, value in stat.items():
                    stat_obj[key] = _sanitize_value(value)
            stats.append(stat_obj)
    elif hasattr(report, "__iter__"):
        # List-like report
        for stat in report:
            if hasattr(stat, "__dict__"):
                stat_obj = {k: _sanitize_value(v) for k, v in vars(stat).items()}
                stats.append(stat_obj)

    return stats


# Default stats reporting interval in milliseconds
DEFAULT_STATS_INTERVAL_MS = 8000


class SfuStatsReporter:
    """Orchestrates stats collection and sending to SFU.

    Collects WebRTC stats from publisher and subscriber peer connections,
    combines them with trace records, and sends to the SFU via SendStats RPC.
    """

    def __init__(
        self,
        connection_manager: "ConnectionManager",
        interval_ms: int = DEFAULT_STATS_INTERVAL_MS,
    ):
        """Initialize the stats reporter.

        Args:
            connection_manager: The connection manager instance
            interval_ms: Interval between stats reports in milliseconds (default 8000)
        """
        self._cm = connection_manager
        self._interval_ms = interval_ms
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._one_off_task: Optional[asyncio.Task] = None

    def start(self) -> None:
        """Start the periodic stats reporting loop.

        Does nothing if interval is <= 0 or already running.
        """
        if self._interval_ms <= 0 or self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._run_loop())
        logger.info(f"SfuStatsReporter started (interval={self._interval_ms}ms)")

    async def stop(self) -> None:
        """Stop the stats reporting loop and cancel pending tasks."""
        self._running = False

        # Cancel and await both tasks
        for task in [self._task, self._one_off_task]:
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        self._task = None
        self._one_off_task = None
        logger.info("SfuStatsReporter stopped")

    async def _run_loop(self) -> None:
        """Main loop that periodically collects and sends stats."""
        while self._running:
            await asyncio.sleep(self._interval_ms / 1000)
            if not self._running:
                break
            try:
                await self._run()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Failed to send stats: {e}")

    async def _run(self) -> None:
        """Collect and send stats once.

        Gets stats from publisher/subscriber peer connections,
        traces the stats, takes a snapshot of traces, and sends to SFU.
        """
        pm = self._cm._peer_manager
        tracer = self._cm.tracer

        # Get stats from publisher/subscriber
        pub_stats: Optional["ComputedStats"] = None
        sub_stats: Optional["ComputedStats"] = None

        if pm.publisher_pc and pm.publisher_stats:
            try:
                pub_stats = await pm.publisher_stats.get()
                tracer.trace("getstats", self._cm.pc_id("pub"), pub_stats.delta)
            except Exception as e:
                logger.debug(f"Failed to get publisher stats: {e}")
                tracer.trace("getstatsOnFailure", self._cm.pc_id("pub"), str(e))

        if pm.subscriber_pc and pm.subscriber_stats:
            try:
                sub_stats = await pm.subscriber_stats.get()
                tracer.trace("getstats", self._cm.pc_id("sub"), sub_stats.delta)
            except Exception as e:
                logger.debug(f"Failed to get subscriber stats: {e}")
                tracer.trace("getstatsOnFailure", self._cm.pc_id("sub"), str(e))

        # Take trace buffer snapshot
        trace_slice = tracer.take()

        try:
            await self._send_stats(trace_slice, pub_stats, sub_stats)
        except Exception as e:
            # Rollback traces on failure so they can be sent on next attempt
            trace_slice.rollback()
            logger.debug(f"Stats send failed, traces rolled back: {e}")
            raise

    async def _send_stats(
        self,
        trace_slice: TraceSlice,
        pub_stats: Optional["ComputedStats"],
        sub_stats: Optional["ComputedStats"],
    ) -> None:
        """Send stats to SFU via SendStats RPC.

        Args:
            trace_slice: Snapshot of trace records
            pub_stats: Publisher stats (if available)
            sub_stats: Subscriber stats (if available)
        """
        client = self._cm.twirp_signaling_client
        ctx = self._cm.twirp_context

        if not client or not ctx:
            logger.debug("Cannot send stats: signaling client not available")
            return

        # Get performance stats
        encode_stats: List[Any] = []
        decode_stats: List[Any] = []

        if pub_stats and pub_stats.performance_stats:
            encode_stats = pub_stats.performance_stats
        if sub_stats and sub_stats.performance_stats:
            decode_stats = sub_stats.performance_stats

        # Get aiortc version
        webrtc_version = getattr(aiortc, "__version__", "unknown")

        # Serialize traces to JSON - this is the core tracing data
        rtc_stats_json = json.dumps(trace_slice.snapshot, separators=(",", ":"))

        # Flatten raw stats to arrays (matching JS SDK format)
        # JS SDK sends: subscriberStats: JSON.stringify(flatten(subscriberStats.stats))
        publisher_stats_json = json.dumps(
            _flatten_stats(pub_stats.stats) if pub_stats else [],
            separators=(",", ":"),
        )
        subscriber_stats_json = json.dumps(
            _flatten_stats(sub_stats.stats) if sub_stats else [],
            separators=(",", ":"),
        )

        request = signal_pb2.SendStatsRequest(
            session_id=self._cm.session_id,
            sdk="stream-python",
            sdk_version=VERSION,
            webrtc_version=webrtc_version,
            # Raw stats per peer connection (matching JS SDK)
            publisher_stats=publisher_stats_json,
            subscriber_stats=subscriber_stats_json,
            # Core tracing fields per spec
            rtc_stats=rtc_stats_json,
            encode_stats=encode_stats,
            decode_stats=decode_stats,
        )

        # Send stats (don't use the SignalClient wrapper to avoid tracing SendStats)
        # We access the parent class method directly
        from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_twirp import (
            AsyncSignalServerClient,
        )

        # Call the parent method directly to avoid the wrapper
        await AsyncSignalServerClient.SendStats(
            client, ctx=ctx, request=request, server_path_prefix=""
        )
        logger.debug(f"SendStats: {len(trace_slice.snapshot)} traces")

    def schedule_one(self, delay_ms: int = 3000) -> None:
        """Schedule a one-off stats send after delay.

        Useful for sending stats shortly after publishing a video track.

        Args:
            delay_ms: Delay in milliseconds before sending stats (default 3000)
        """
        # Cancel any existing one-off task
        if self._one_off_task and not self._one_off_task.done():
            self._one_off_task.cancel()

        self._one_off_task = asyncio.create_task(self._delayed_run(delay_ms))

    async def _delayed_run(self, delay_ms: int) -> None:
        """Run stats collection after a delay.

        Args:
            delay_ms: Delay in milliseconds
        """
        try:
            await asyncio.sleep(delay_ms / 1000)
            await self._run()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning(f"Delayed stats send failed: {e}")

    def flush(self) -> None:
        """Immediate flush (fire-and-forget).

        Triggers a stats send without waiting for the result.
        """
        if not self._running:
            return
        asyncio.create_task(self._run())
