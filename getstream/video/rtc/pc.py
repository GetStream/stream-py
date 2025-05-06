import asyncio
import logging
from collections import defaultdict
from typing import Optional, Any

import aiortc

from getstream.video.rtc.track_util import add_ice_candidates_to_sdp, AudioTrackHandler
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
        self._received_ice_event = asyncio.Event()
        self._ice_candidates = []

        @self.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            logger.info(
                f"Publisher ICE gathering state changed to {self.iceGatheringState}"
            )
            if self.iceGatheringState == "complete":
                logger.info("Publisher: All ICE candidates have been gathered.")
                # Optionally send a final ICE candidate message or null candidate if required by SFU

    async def handle_answer(self, response):
        """Handles the SDP answer received from the SFU for the publisher connection."""

        logger.info(
            f"Publisher received answer {response.sdp}, now waiting for ICE candidates."
        )
        await self._received_ice_event.wait()

        # patch SDP to include the ICE candidates that were collected in the meantime
        patched_sdp = add_ice_candidates_to_sdp(response.sdp, self._ice_candidates)

        remote_description = aiortc.RTCSessionDescription(
            type="answer", sdp=patched_sdp
        )

        await self.setRemoteDescription(remote_description)
        logger.info(
            f"Publisher remote description set successfully. {self.localDescription}"
        )

    async def handle_remote_ice_candidate(self, candidate: str) -> None:
        self._ice_candidates.append(candidate)
        # this is just here to test things
        await asyncio.sleep(0.2)
        self._received_ice_event.set()


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

        # this event is set when the first ice event is received from the SFU
        # we need this setup because aiortc does not support ice trickling
        # our SFU atm assumes that clients support ice trickling and does not include candidates
        self._received_ice_event = asyncio.Event()

        # the list of ice candidates received via signaling
        self._ice_candidates = []

        # the list of tracks
        self.tracks = defaultdict(lambda: defaultdict(list))

        @self.on("track")
        async def on_track(track: aiortc.mediastreams.MediaStreamTrack):
            logger.info(f"Track received: f{track.id}")
            user = self.connection.participants_state.get_user_from_track_id(track.id)

            if track.kind == "audio":
                handler = AudioTrackHandler(
                    track, lambda pcm: self.emit("audio", pcm, user)
                )
                asyncio.ensure_future(handler.start())

        @self.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            logger.info(f"ICE gathering state changed to {self.iceGatheringState}")
            if self.iceGatheringState == "complete":
                logger.info("All ICE candidates have been gathered.")

    async def handle_remote_ice_candidate(self, candidate: str) -> None:
        self._ice_candidates.append(candidate)
        self._received_ice_event.set()

    def handle_track_ended(self, track: aiortc.mediastreams.MediaStreamTrack) -> None:
        logger.info(f"track ended: f{track.id}")
