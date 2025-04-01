import json

import aiortc
import uuid

import asyncio
import logging
from typing import AsyncIterator, Optional, List

from getstream.video.call import Call
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_twirp import (
    SignalServerClient,
)
from getstream.video.rtc.signaling import WebSocketClient, SignalingError
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2

from twirp import context

# Import join_call_coordinator_request from coordinator module instead of __init__
from getstream.video.rtc.coordinator import join_call_coordinator_request
from aiortc.contrib.media import MediaRecorder

logger = logging.getLogger("getstream.video.rtc.connection_manager")


class ConnectionError(Exception):
    """Exception raised when connection to the call fails."""

    pass


class SubscriberPeerConnection(aiortc.RTCPeerConnection):
    def __init__(
        self,
        manager: "ConnectionManager",
        configuration: Optional[aiortc.RTCConfiguration] = None,
    ) -> None:
        logger.info(
            f"creating subscriber peer connection with configuration: {configuration}"
        )
        super().__init__(configuration)
        self.manager = manager
        self.pending_ice_candidates: List[aiortc.RTCIceCandidate] = []

        @self.on("track")
        def on_track(track: aiortc.mediastreams.MediaStreamTrack):
            logger.info("Track received: %s", track)
            self.manager.recorder.addTrack(track)
            self.manager.recorder.start()

        @self.on("icegatheringstatechange")
        def on_icegatheringstatechange():
            logger.info(f"ICE gathering state changed to {self.iceGatheringState}")
            if self.iceGatheringState == "complete":
                print("All ICE candidates have been gathered.")

    async def handle_remote_ice_candidate(
        self, candidate: aiortc.RTCIceCandidate
    ) -> None:
        await self.addIceCandidate(candidate)
        # we cannot do this because aiortc does not support ice trickle
        # if self.remoteDescription is None:
        #     self.pending_ice_candidates.append(candidate)
        # else:
        #     self.addIceCandidate(candidate)


class ConnectionManager:
    def __init__(self, call: Call, user_id: str = None, create: bool = True, **kwargs):
        self.call = call
        self.user_id = user_id
        self.create = create
        self.kwargs = kwargs
        self.running = False
        self.join_response = None
        self.connection_task = None
        # Add a stop event to signal when to stop iteration
        self._stop_event = asyncio.Event()
        # WebSocket client for SFU communication
        self.ws_client = None
        self.session_id = str(uuid.uuid4())
        self.subscriber_pc: SubscriberPeerConnection
        self.twirp_signaling_client: SignalServerClient
        self.twirp_context: context.Context
        self.recorder = MediaRecorder("/Users/tommaso/Desktop/test.mp3")
        self.local_sfu = True

    async def _full_connect(self):
        """Perform location discovery and join call via coordinator.

        This method handles the full connection process:
        1. Discovering the optimal location
        2. Joining the call via the coordinator API
        3. Establishing WebSocket connection to the SFU

        Raises:
            ConnectionError: If there's an issue joining the call or connecting to the SFU
        """
        # Discover location
        logger.info("Discovering location")
        try:
            discovery = HTTPHintLocationDiscovery(logger=logger)
            location = discovery.discover()
            logger.info(f"Discovered location: {location}")
        except Exception as e:
            logger.error(f"Failed to discover location: {e}")
            # Default to a reasonable location if discovery fails
            location = "FRA"
            logger.info(f"Using default location: {location}")

        # Join call via coordinator
        logger.info("Performing join call request on coordinator API")
        try:
            self.join_response = await join_call_coordinator_request(
                self.call,
                self.user_id,
                create=self.create,
                location=location,
                **self.kwargs,
            )
            logger.info(
                f"Received credentials to connect to SFU {self.join_response.data.credentials.server.url}"
            )
            if self.local_sfu:
                self.join_response.data.credentials.server.url = (
                    "http://127.0.0.1:3031/twirp"
                )
                logger.info(
                    f"adjusted sfu url to {self.join_response.data.credentials.server.url}"
                )

        except Exception as e:
            logger.error(f"Failed to join call: {e}")
            raise ConnectionError(f"Failed to join call: {e}")

        # Connect to SFU via WebSocket
        logger.info("Connecting to SFU via WebSocket")

        try:
            # Create JoinRequest for WebSocket connection
            join_request = self._create_join_request()

            # Get WebSocket URL from the coordinator response
            ws_url = self.join_response.data.credentials.server.ws_endpoint
            if self.local_sfu:
                ws_url = "ws://127.0.0.1:3031/ws"
                logger.info(f"adjusted sfu ws url to {ws_url}")

            # Create WebSocket client
            self.ws_client = WebSocketClient(ws_url, join_request)

            # Connect to the WebSocket server and wait for the first message
            logger.info(f"Establishing WebSocket connection to {ws_url}")
            sfu_event = await self.ws_client.connect()

            pc_configuration = aiortc.RTCConfiguration(
                iceServers=[
                    aiortc.RTCIceServer(
                        urls=ice["urls"],
                        username=ice["username"],
                        credential=ice["password"],
                    )
                    for ice in self.join_response.data.credentials.ice_servers
                ]
            )

            if self.local_sfu:
                for i, ice in enumerate(pc_configuration.iceServers):
                    patched_urls = []
                    for url in ice.urls:
                        parts = url.split(":")
                        patched_urls.append(
                            f"{parts[0]}:192.168.64.1:{':'.join(parts[2:])}"
                        )
                    pc_configuration.iceServers[i].urls = patched_urls

            self.subscriber_pc = SubscriberPeerConnection(
                manager=self, configuration=pc_configuration
            )

            self.twirp_signaling_client = SignalServerClient(
                address=self.join_response.data.credentials.server.url
            )
            self.twirp_context = context.Context(
                headers={"authorization": join_request.token}
            )
            logger.info("WebSocket connection established successfully")
            logger.debug(f"Received join response: {sfu_event.join_response}")
        except SignalingError as e:
            logger.error(f"Failed to connect to SFU: {e}")
            # Close the WebSocket if it was created
            if self.ws_client:
                self.ws_client.close()
                self.ws_client = None
            raise ConnectionError(f"Failed to connect to SFU: {e}")
        except Exception as e:
            logger.error(f"Unexpected error connecting to SFU: {e}")
            # Close the WebSocket if it was created
            if self.ws_client:
                self.ws_client.close()
                self.ws_client = None
            raise ConnectionError(f"Unexpected error connecting to SFU: {e}")

        # self.ws_client.on_event("ice_trickle", self._on_ice_trickle)
        self.ws_client.on_event("subscriber_offer", self._on_subscriber_offer)
        # Mark as running and clear stop event
        self.running = True
        self._stop_event.clear()

    # TODO: synchronize access to this method
    async def _on_subscriber_offer(self, event: events_pb2.SubscriberOffer):
        logger.info(
            "Subscriber offer received, waiting for ICE gathering to be complete"
        )

        await self.subscriber_pc.setRemoteDescription(
            aiortc.RTCSessionDescription(type="offer", sdp=event.sdp)
        )
        for candidate in self.subscriber_pc.pending_ice_candidates:
            await self.subscriber_pc.addIceCandidate(candidate)
        self.subscriber_pc.pending_ice_candidates.clear()
        await self.subscriber_pc.setLocalDescription(
            await self.subscriber_pc.createAnswer()
        )
        await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self.twirp_signaling_client.SendAnswer(
                ctx=self.twirp_context,
                request=signal_pb2.SendAnswerRequest(
                    peer_type=models_pb2.PEER_TYPE_SUBSCRIBER,
                    sdp=self.subscriber_pc.localDescription.sdp,
                    session_id=self.session_id,
                ),
                server_path_prefix="",
            ),
        )
        logger.info(
            f"subscriber pc local description is {self.subscriber_pc.localDescription.sdp}"
        )

    async def _on_ice_trickle(self, event: events_pb2.ICETrickle):
        logger.info(
            f"received ICE trickle for peer type {models_pb2.PEER_TYPE_SUBSCRIBER}"
        )
        candidate_sdp = json.loads(event.ice_candidate)["candidate"]
        candidate = aiortc.sdp.candidate_from_sdp(candidate_sdp)

        if candidate.sdpMid is None:
            candidate.sdpMid = ""

        if candidate.sdpMLineIndex is None:
            candidate.sdpMLineIndex = ""

        if event.peer_type == models_pb2.PEER_TYPE_SUBSCRIBER:
            await self.subscriber_pc.handle_remote_ice_candidate(candidate)
        else:
            pass

    def _create_join_request(self) -> events_pb2.JoinRequest:
        """Create a JoinRequest protobuf message for the WebSocket connection.

        Returns:
            A JoinRequest protobuf message configured with data from the coordinator response
        """
        # Get credentials from the coordinator response
        credentials = self.join_response.data.credentials

        # Create a JoinRequest
        join_request = events_pb2.JoinRequest()
        join_request.token = credentials.token
        join_request.session_id = self.session_id
        return join_request

    async def __aenter__(self):
        """Async context manager entry that performs location discovery and joins call."""
        await self._full_connect()

        # Return self to be used as an async iterator
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit that leaves the call."""
        await self.leave()

    async def __anext__(self):
        """Async iterator implementation to yield events."""
        if not self.running:
            raise StopAsyncIteration

        # Check if stop was requested before waiting
        if self._stop_event.is_set():
            self.running = False
            raise StopAsyncIteration

        # Use wait_for with a short timeout to frequently check self.running
        try:
            # Wait for 100ms, but allow interruption via the stop event
            await asyncio.wait_for(self._stop_event.wait(), 0.1)
            # If we reach here, the event was set
            self.running = False
            raise StopAsyncIteration
        except asyncio.TimeoutError:
            # Timeout means the event wasn't set, so we continue
            return "helloworld"

    def __aiter__(self) -> AsyncIterator:
        """Return self as an async iterator."""
        return self

    async def leave(self):
        """Leave the call and stop yielding events."""
        if not self.running:
            return

        logger.info("Leaving call")
        self.running = False

        # Signal the __anext__ method to stop
        self._stop_event.set()

        # Close the WebSocket connection if it exists
        if self.ws_client:
            logger.info("Closing WebSocket connection")
            self.ws_client.close()
            self.ws_client = None

        logger.info("Successfully left call")
