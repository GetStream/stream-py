import asyncio
import logging
from typing import Optional

import ping3
from pyee.asyncio import AsyncIOEventEmitter

logger = logging.getLogger(__name__)


class NetworkMonitor(AsyncIOEventEmitter):
    """Monitors network connectivity and emits events."""

    def __init__(
        self,
        connectivity_hosts: list = None,
        connectivity_timeout: float = 3.0,
        check_interval: float = 1.0,
        required_successful_pings: int = 1,
    ):
        """
        Initialize network monitor.

        Args:
            connectivity_hosts: List of hosts to ping for connectivity checks
            connectivity_timeout: Timeout for ping checks
            check_interval: Seconds between connectivity checks
            required_successful_pings: Number of successful pings needed to consider network online
        """
        super().__init__()

        # Default reliable hosts for connectivity checking
        self.connectivity_hosts = connectivity_hosts or [
            "8.8.8.8",  # Google DNS
            "1.1.1.1",  # Cloudflare DNS
            "208.67.222.222",  # OpenDNS
        ]

        self.connectivity_timeout = connectivity_timeout
        self.check_interval = check_interval
        self.required_successful_pings = required_successful_pings
        self.is_online = True
        self.monitor_task: Optional[asyncio.Task] = None
        self.logger = logger

    async def start_monitoring(self):
        """Start network connectivity monitoring."""
        if self.monitor_task and not self.monitor_task.done():
            self.logger.warning("Network monitoring already started")
            return

        self.logger.info("Starting network connectivity monitoring")
        self.monitor_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop network connectivity monitoring."""
        if self.monitor_task:
            self.logger.info("Stopping network connectivity monitoring")
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
            finally:
                self.monitor_task = None

    async def _monitor_loop(self):
        """Main monitoring loop to detect network changes."""
        while True:
            try:
                current_status = await self._check_connectivity()
                if current_status != self.is_online:
                    self.is_online = current_status
                    await self._handle_network_change(current_status)
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                self.logger.debug("Network monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(
                    "Error in network monitoring",
                    exc_info=e,
                    extra={"check_interval": self.check_interval},
                )
                await asyncio.sleep(self.check_interval)

    async def _check_connectivity(self) -> bool:
        """
        Check connectivity using ping3 package.

        Returns:
            True if required number of pings succeed, False otherwise
        """
        successful_pings = 0

        for host in self.connectivity_hosts:
            try:
                # Run ping in executor to avoid blocking
                response_time = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: ping3.ping(host, timeout=self.connectivity_timeout)
                )

                if response_time is not None:
                    successful_pings += 1
                    self.logger.debug(
                        f"Ping to {host} successful: {response_time:.2f}s"
                    )

                    # If we've reached the required number of successful pings, we're online
                    if successful_pings >= self.required_successful_pings:
                        return True
                else:
                    self.logger.debug(f"Ping to {host} failed")

            except Exception as e:
                self.logger.debug(f"Ping to {host} error: {e}")

        return False

    async def _handle_network_change(self, online: bool):
        """
        Handle network status changes and emit events.

        Args:
            online: True if network is now available, False if unavailable
        """
        status = "online" if online else "offline"
        self.logger.debug(f"Network status changed to {status}")

        # Emit network change event using AsyncIOEventEmitter
        self.emit(
            "network_changed",
            {"online": online, "timestamp": asyncio.get_event_loop().time()},
        )

        # Also emit specific online/offline events
        if online:
            self.emit("network_online", {"timestamp": asyncio.get_event_loop().time()})
        else:
            self.emit("network_offline", {"timestamp": asyncio.get_event_loop().time()})
