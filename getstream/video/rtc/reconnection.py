"""
Handles reconnection logic for the video connection.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Dict, Optional

from getstream.video.rtc.connection_utils import ConnectionState

logger = logging.getLogger(__name__)

# Constants
_DISCONNECTION_TIMEOUT_SECONDS = 30
_DEFAULT_MAX_ATTEMPTS = 3
_DEFAULT_MIN_WAIT = 1
_DEFAULT_MAX_WAIT = 5


class ReconnectionStrategy:
    """Reconnection strategies."""

    UNSPECIFIED = "UNSPECIFIED"
    FAST = "FAST"
    REJOIN = "REJOIN"
    MIGRATE = "MIGRATE"
    DISCONNECT = "DISCONNECT"


@dataclass
class ReconnectionInfo:
    """Stores information about the current reconnection attempt."""

    strategy: str = ReconnectionStrategy.UNSPECIFIED
    reason: str = ""
    attempts: int = 0
    last_offline_timestamp: Optional[float] = None
    published_tracks: Dict = field(default_factory=dict)

    def reset_state(self):
        """Reset reconnection state."""
        self.strategy = ReconnectionStrategy.UNSPECIFIED
        self.reason = ""
        self.attempts = 0
        self.last_offline_timestamp = None
        # Don't reset published_tracks as they're needed for restoration

    def add_published_track(self, track_id: str, track, track_info, media_relay):
        """Store track info for reconnection."""
        self.published_tracks[track_id] = {
            "track": track,
            "track_info": track_info,
            "media_relay": media_relay,
        }


class ReconnectionManager:
    """Manages reconnection logic and state for the ConnectionManager."""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.reconnection_info = ReconnectionInfo()
        self.set_network_event = None
        self._reconnect_lock = asyncio.Lock()
        self._fast_reconnect_deadline_seconds = 10

    async def reconnect(self, strategy: str, reason: str):
        """
        Main reconnection orchestrator.

        Args:
            strategy: The reconnection strategy to use
            reason: Human-readable reason for the reconnection
        """
        async with self._reconnect_lock:
            # Check if already in a reconnection state
            if self.connection_manager.connection_state in [
                ConnectionState.RECONNECTING,
                ConnectionState.MIGRATING,
                ConnectionState.RECONNECTING_FAILED,
            ]:
                logger.debug(
                    "Reconnection already in progress",
                    extra={
                        "current_state": self.connection_manager.connection_state.value
                    },
                )
                return

            reconnect_start_time = time.time()
            self.reconnection_info.strategy = strategy
            self.reconnection_info.reason = reason

            logger.info(
                "Starting reconnection", extra={"strategy": strategy, "reason": reason}
            )

            try:
                await self._execute_reconnection_loop(reconnect_start_time)
            except Exception as e:
                logger.error("Reconnection orchestrator failed", exc_info=e)
                self.connection_manager.connection_state = (
                    ConnectionState.RECONNECTING_FAILED
                )
                self.connection_manager.emit("reconnection_failed", {"reason": str(e)})

    async def _execute_reconnection_loop(self, reconnect_start_time: float):
        """Execute the main reconnection retry loop."""
        while True:
            # Check disconnection timeout
            timeout = _DISCONNECTION_TIMEOUT_SECONDS
            if 0 < timeout < (time.time() - reconnect_start_time):
                logger.warning(
                    "Stopping reconnection attempts after reaching disconnection timeout"
                )
                self.connection_manager.connection_state = (
                    ConnectionState.RECONNECTING_FAILED
                )
                self.connection_manager.emit(
                    "reconnection_failed", {"reason": "Disconnection timeout exceeded"}
                )
                return

            # Increment attempts (except for FAST strategy)
            if self.reconnection_info.strategy != ReconnectionStrategy.FAST:
                self.reconnection_info.attempts += 1

            try:
                # Wait for network availability
                if self.set_network_event:
                    logger.debug("Waiting for network availability")
                    await self.set_network_event.wait()

                logger.info(
                    f"Executing reconnection with strategy {self.reconnection_info.strategy}"
                )

                # Execute strategy-specific reconnection
                await self._execute_reconnection_strategy()

                # If we reach here, reconnection was successful
                duration = time.time() - reconnect_start_time
                self.connection_manager.emit(
                    "reconnection_success",
                    {"strategy": self.reconnection_info.strategy, "duration": duration},
                )
                # Reset reconnection state after successful connection
                self.reconnection_info.reset_state()
                self.set_network_event = None
                logger.debug("Reconnection state reset")
                break

            except Exception as error:
                if self.connection_manager.connection_state == ConnectionState.OFFLINE:
                    logger.debug("Can't reconnect while offline, stopping attempts")
                    break

                logger.warning(
                    f"Reconnection failed, attempting with REJOIN: {error}",
                    exc_info=error,
                )
                await asyncio.sleep(0.5)  # Brief delay before retry
                self.reconnection_info.strategy = ReconnectionStrategy.REJOIN

            # Check if we should exit the loop
            if self.connection_manager.connection_state in [
                ConnectionState.JOINED,
                ConnectionState.RECONNECTING_FAILED,
                ConnectionState.LEFT,
            ]:
                break

        logger.info("Reconnection flow finished")

    async def _execute_reconnection_strategy(self):
        """Execute the strategy-specific reconnection logic."""
        strategy = self.reconnection_info.strategy

        if strategy == ReconnectionStrategy.FAST:
            await self._reconnect_fast()
        elif strategy == ReconnectionStrategy.REJOIN:
            await self._reconnect_rejoin()
        elif strategy == ReconnectionStrategy.MIGRATE:
            await self._reconnect_migrate()
        elif strategy == ReconnectionStrategy.DISCONNECT:
            await self.connection_manager.leave()
            return
        else:
            logger.debug(f"No-op strategy {strategy}")

    async def _reconnect_fast(self):
        """Fast reconnection strategy - minimal disruption."""
        logger.info("Executing FAST reconnection strategy")
        self.connection_manager.connection_state = ConnectionState.RECONNECTING

        try:
            if (
                self.connection_manager.ws_client
                and self.connection_manager.ws_client.running
            ):
                # Simple ICE restart if WebSocket is healthy
                if self.connection_manager.publisher_pc:
                    await self.connection_manager.publisher_pc.restartIce()
                logger.info("ICE restart completed for healthy WebSocket")
            else:
                # Full reconnection needed
                self.connection_manager._connection_options.fast_reconnect = True
                previous_ws_client = self.connection_manager.ws_client

                # Use _connect_internal with existing connection info
                await self.connection_manager._connect_internal(
                    region=self.connection_manager._connection_options.region,
                    token=self.connection_manager.join_response.data.credentials.token
                    if self.connection_manager.join_response
                    else None,
                    session_id=self.connection_manager.session_id,
                )

                # Clean up old WebSocket after successful connection
                if previous_ws_client:
                    previous_ws_client.close()

                # Restore published tracks with stored MediaRelay instances
                await self.connection_manager._restore_published_tracks()

            self.connection_manager.connection_state = ConnectionState.JOINED
            logger.info("FAST reconnection completed successfully")
        except Exception as e:
            logger.error("FAST reconnection failed", exc_info=e)
            self.connection_manager.connection_state = (
                ConnectionState.RECONNECTING_FAILED
            )
            raise

    async def _reconnect_rejoin(self):
        """Rejoin reconnection strategy - full reconnection."""
        logger.info("Executing REJOIN reconnection strategy")
        self.connection_manager.connection_state = ConnectionState.RECONNECTING

        # Store references to old connections for cleanup
        old_publisher = self.connection_manager.publisher_pc
        old_subscriber = self.connection_manager.subscriber_pc
        old_ws_client = self.connection_manager.ws_client

        # Clear the old connections so new ones can be created
        self.connection_manager.publisher_pc = None
        self.connection_manager.subscriber_pc = None
        self.connection_manager.ws_client = None

        try:
            # Close old connections efficiently
            await self.connection_manager._cleanup_connections(
                old_ws_client, old_publisher, old_subscriber
            )

            # Use _connect_internal for fresh connection
            await self.connection_manager._connect_internal()

            # Restore published tracks after successful reconnection
            await self.connection_manager._restore_published_tracks()

            logger.info("REJOIN reconnection completed successfully")
        except Exception as error:
            logger.error("REJOIN reconnection failed", exc_info=error)
            # Ensure connection state is properly set on failure
            self.connection_manager.connection_state = (
                ConnectionState.RECONNECTING_FAILED
            )
            raise

    async def _reconnect_migrate(self):
        """Migration reconnection strategy - server-coordinated."""
        logger.info("Executing MIGRATE reconnection strategy")

        current_ws_client = self.connection_manager.ws_client
        current_publisher = self.connection_manager.publisher_pc
        current_subscriber = self.connection_manager.subscriber_pc

        self.connection_manager.connection_state = ConnectionState.MIGRATING

        if current_publisher and hasattr(current_publisher, "removeListener"):
            current_publisher.removeListener("connectionstatechange")
        if current_subscriber and hasattr(current_subscriber, "removeListener"):
            current_subscriber.removeListener("connectionstatechange")

        try:
            migrating_from = getattr(current_ws_client, "edge_name", None)

            # Set migration options for connection
            if hasattr(self.connection_manager, "_connection_options"):
                self.connection_manager._connection_options.fast_reconnect = False
                self.connection_manager._connection_options.migrating_from = (
                    migrating_from
                )
                self.connection_manager._connection_options.previous_session_id = (
                    self.connection_manager.session_id if migrating_from else None
                )

            # Use _connect_internal for migration
            await self.connection_manager._connect_internal(
                region=self.connection_manager._connection_options.region,
                session_id=self.connection_manager.session_id,
            )

            await self.connection_manager._restore_published_tracks()

            self.connection_manager.connection_state = ConnectionState.JOINED
            logger.info("MIGRATE reconnection completed successfully")

        finally:
            # Clean up old connections
            await self.connection_manager._cleanup_connections(
                current_ws_client, current_publisher, current_subscriber
            )
