"""
Orchestrates stats collection and sending to SFU.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, List, Optional

from getstream.version import VERSION
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.tracer import TraceSlice

if TYPE_CHECKING:
    from getstream.video.rtc.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


def _sanitize_value(value: Any) -> Any:
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


def _flatten_stats(report) -> List[Any]:
    """Flatten a stats snapshot to an array of stats objects."""
    if report is None:
        return []

    if isinstance(report, dict):
        if "id" in report or "type" in report:
            return [_sanitize_value(report)]
        stats = []
        for stat_id, stat in report.items():
            if isinstance(stat, dict):
                stat_obj = {"id": stat_id, **{k: _sanitize_value(v) for k, v in stat.items()}}
                stats.append(stat_obj)
            else:
                stats.append({"id": stat_id, "value": _sanitize_value(stat)})
        return stats

    if isinstance(report, list):
        return [_sanitize_value(stat) for stat in report]

    return [_sanitize_value(report)]


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
        tracer = self._cm.tracer
        session = self._cm._rtc_session
        pub_stats = None
        sub_stats = None

        if session is not None:
            try:
                snapshot = await session.stats()
                if snapshot:
                    pub_stats = snapshot.get("publisher")
                    sub_stats = snapshot.get("subscriber")
                    tracer.trace("getstats", self._cm.pc_id("pub"), pub_stats)
                    tracer.trace("getstats", self._cm.pc_id("sub"), sub_stats)
            except Exception as e:
                logger.debug(f"Failed to get RTC stats: {e}")
                tracer.trace("getstatsOnFailure", self._cm.pc_id("pub"), str(e))

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
        pub_stats: Optional[Any],
        sub_stats: Optional[Any],
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

        try:
            import getstream_rtc_core

            webrtc_version = getstream_rtc_core.__version__
        except Exception:
            webrtc_version = "unknown"

        # Serialize traces to JSON - this is the core tracing data
        rtc_stats_json = json.dumps(trace_slice.snapshot, separators=(",", ":"))

        # Flatten raw stats to arrays (matching JS SDK format)
        publisher_stats_json = json.dumps(
            _flatten_stats(pub_stats) if pub_stats else [],
            separators=(",", ":"),
        )
        subscriber_stats_json = json.dumps(
            _flatten_stats(sub_stats) if sub_stats else [],
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
