import asyncio
import logging
from typing import Optional, Any

import aiortc
from aiortc.contrib.media import MediaRelay

from getstream.video.rtc.track_util import AudioTrackHandler
from pyee.asyncio import AsyncIOEventEmitter

logger = logging.getLogger(__name__)


def parse_track_id(id: str) -> tuple[str, str]:
    """
    Parse the webRTC media track and returns a tuple including: the id of the participant, the type of track
    """
    participant_id, track_type, _ = id.split(":")
    return participant_id, track_type


class PublisherPeerConnection(aiortc.RTCPeerConnection):
    def __init__(
        self,
        manager: Any,
        configuration: Optional[aiortc.RTCConfiguration] = None,
    ) -> None:
        if configuration is None:
            configuration = aiortc.RTCConfiguration(
                iceServers=[aiortc.RTCIceServer(urls="stun:stun.l.google.com:19302")]
            )
        logger.info(
            f"Creating publisher peer connection with configuration: {configuration}"
        )
        super().__init__(configuration)
        self.manager = manager
        self._connected_event = asyncio.Event()

        @self.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            logger.info(
                f"Publisher ICE gathering state changed to {self.iceGatheringState}"
            )
            if self.iceGatheringState == "complete":
                logger.info("Publisher: All ICE candidates have been gathered.")

        @self.on("iceconnectionstatechange")
        def on_iceconnectionstatechange():
            logger.info(
                f"Publisher ICE connection state changed to {self.iceConnectionState}"
            )

        @self.on("connectionstatechange")
        def on_connectionstatechange():
            logger.info(f"Publisher connection state changed to {self.connectionState}")
            if self.connectionState == "connected":
                self._connected_event.set()

    async def handle_answer(self, response):
        """Handles the SDP answer received from the SFU for the publisher connection."""

        logger.info(f"Publisher received answer {response.sdp}")

        remote_description = aiortc.RTCSessionDescription(
            type="answer", sdp=response.sdp
        )

        await self.setRemoteDescription(remote_description)
        logger.info(
            f"Publisher remote description set successfully. {self.localDescription}"
        )

    async def wait_for_connected(self, timeout: float = 15.0):
        # If already connected, return immediately
        if self.connectionState == "connected":
            logger.info("Publisher already connected, no need to wait")
            return

        logger.info(f"Waiting for publisher connection with {timeout}s timeout")
        try:
            # Wait for the connected event with timeout
            await asyncio.wait_for(self._connected_event.wait(), timeout=timeout)
            logger.info("Publisher successfully connected")
        except asyncio.TimeoutError:
            logger.error(f"Publisher connection timed out after {timeout}s")
            raise TimeoutError(f"Connection timed out after {timeout} seconds")

    async def restartIce(self):
        """Restart ICE connection for reconnection scenarios."""
        logger.info("Restarting ICE connection for publisher")
        try:
            # Create new offer to restart ICE
            offer = await self.createOffer()
            await self.setLocalDescription(offer)
            logger.debug("Publisher ICE restart initiated")
        except Exception as e:
            logger.error("Failed to restart publisher ICE", exc_info=e)
            raise


class SubscriberPeerConnection(aiortc.RTCPeerConnection, AsyncIOEventEmitter):
    def __init__(
        self,
        connection,
        configuration: Optional[aiortc.RTCConfiguration] = None,
    ) -> None:
        if configuration is None:
            configuration = aiortc.RTCConfiguration(
                iceServers=[aiortc.RTCIceServer(urls="stun:stun.l.google.com:19302")]
            )
        logger.info(
            f"creating subscriber peer connection with configuration: {configuration}"
        )
        super().__init__(configuration)
        self.connection = connection

        self.track_map = {}  # track_id -> (MediaRelay, original_track)

        @self.on("track")
        async def on_track(track: aiortc.mediastreams.MediaStreamTrack):
            logger.info(f"Track received: {track.id} : {track.kind}")

            # Try to get user from track ID first (original method)
            user = self.connection.participants_state.get_user_from_track_id(track.id)

            # If that fails and it's an audio track, try to get the next expected audio user
            if user is None and track.kind == "audio":
                user = (
                    self.connection._subscription_manager.get_next_expected_audio_user()
                )

            relay = MediaRelay()
            self.track_map[track.id] = (relay, track)

            if track.kind == "audio":
                # Add a new subscriber for AudioTrackHandler
                handler = AudioTrackHandler(
                    relay.subscribe(track), lambda pcm: self.emit("audio", pcm, user)
                )
                asyncio.create_task(handler.start())

            self.emit("track_added", relay.subscribe(track), user)

        @self.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            logger.info(f"ICE gathering state changed to {self.iceGatheringState}")
            if self.iceGatheringState == "complete":
                logger.info("All ICE candidates have been gathered.")

    def add_track_subscriber(
        self, track_id: str
    ) -> Optional[aiortc.mediastreams.MediaStreamTrack]:
        """Add a new subscriber to an existing track's MediaRelay."""
        track_data = self.track_map.get(track_id)

        if track_data:
            relay, original_track = track_data
            return relay.subscribe(original_track, buffered=False)
        return None

    def handle_track_ended(self, track: aiortc.mediastreams.MediaStreamTrack) -> None:
        logger.info(f"track ended: {track.id}")

        # Clean up stored references when track ends
        if track.id in self.track_map:
            del self.track_map[track.id]

    async def restartIce(self):
        """Restart ICE connection for reconnection scenarios."""
        logger.info("Restarting ICE connection for subscriber")
        try:
            # For subscriber, we typically wait for new offer from SFU
            # This method serves as a placeholder for ICE restart coordination
            logger.debug("Subscriber ICE restart initiated")
        except Exception as e:
            logger.error("Failed to restart subscriber ICE", exc_info=e)
            raise
