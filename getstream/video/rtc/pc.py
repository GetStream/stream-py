import asyncio
import logging
from typing import Any, Optional

import aiortc
from aiortc.contrib.media import MediaRelay

from getstream.common import telemetry
from getstream.video.rtc.track_util import AudioTrackHandler
from pyee.asyncio import AsyncIOEventEmitter
from aiortc.rtcrtpsender import RTCRtpSender
from aiortc.rtcrtpparameters import RTCRtpCodecCapability


logger = logging.getLogger(__name__)


def parse_track_id(id: str) -> tuple[str, str]:
    """
    Parse the webRTC media track and returns a tuple including: the id of the participant, the type of track
    """
    participant_id, track_type, _ = id.split(":")
    return participant_id, track_type


def publish_codec_preferences() -> list[RTCRtpCodecCapability]:
    return [
        c
        for c in RTCRtpSender.getCapabilities("video").codecs
        if c.name.lower() != "vp8"
    ]


def subscribe_codec_preferences() -> list[RTCRtpCodecCapability]:
    return RTCRtpSender.getCapabilities("video").codecs


class PublisherPeerConnection(aiortc.RTCPeerConnection):
    def __init__(
        self,
        manager: Any,
        configuration: aiortc.RTCConfiguration,
    ) -> None:
        logger.info(
            f"Creating publisher peer connection with configuration: {configuration}"
        )
        super().__init__(configuration)
        self.manager = manager
        self._connected_event = asyncio.Event()

        for transceiver in self.getTransceivers():
            if transceiver.kind == "video":
                transceiver.setCodecPreferences(publish_codec_preferences())

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

        logger.debug(f"Publisher received answer {response.sdp}")

        remote_description = aiortc.RTCSessionDescription(
            type="answer", sdp=response.sdp
        )

        with telemetry.start_as_current_span("publisher.pc.handle_answer") as span:
            span.set_attribute("remoteDescription", remote_description.sdp)
            await self.setRemoteDescription(remote_description)
            logger.debug(
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
        configuration: aiortc.RTCConfiguration,
    ) -> None:
        logger.info(
            f"creating subscriber peer connection with configuration: {configuration}"
        )
        super().__init__(configuration)
        self.connection = connection

        self.track_map = {}  # track_id -> (MediaRelay, original_track)
        self.video_frame_trackers = {}  # track_id -> VideoFrameTracker

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
            tracked_track = track

            # For video tracks, wrap with VideoFrameTracker to capture frame metrics
            if track.kind == "video":
                from getstream.video.rtc.track_util import VideoFrameTracker

                tracked_track = VideoFrameTracker(track)
                self.video_frame_trackers[track.id] = tracked_track

            self.track_map[track.id] = (relay, tracked_track)

            if track.kind == "audio":
                from getstream.video.rtc import PcmData

                # Add a new subscriber for AudioTrackHandler and attach the participant to the pcm object
                def _emit_pcm(pcm: PcmData):
                    pcm.participant = user
                    self.emit("audio", pcm)

                handler = AudioTrackHandler(relay.subscribe(tracked_track), _emit_pcm)
                asyncio.create_task(handler.start())

            self.emit("track_added", relay.subscribe(tracked_track), user)

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
        if track.id in self.video_frame_trackers:
            del self.video_frame_trackers[track.id]

    def get_video_frame_tracker(self) -> Optional[Any]:
        """Get a video frame tracker for stats collection.

        Note: Returns the first tracker by insertion order. When multiple video
        tracks exist simultaneously (e.g., webcam + screenshare), this may not
        match the track being actively consumed. Performance stats calculation
        in StatsTracer mitigates this by selecting the highest-resolution track.
        """
        if self.video_frame_trackers:
            return next(iter(self.video_frame_trackers.values()))
        return None

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
