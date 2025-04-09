import functools
from collections import defaultdict

import json
import re  # Add import for regex

import aiortc
import uuid

import asyncio
import logging
from typing import AsyncIterator, Optional, List

from getstream.video.call import Call
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TrackInfo,
    TRACK_TYPE_VIDEO,
    TRACK_TYPE_AUDIO,
    VideoLayer,
    VideoDimension,
)
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_pb2 import (
    SetPublisherResponse,
)
from getstream.video.rtc.twirp_client_wrapper import SignalClient, SfuRpcError
from getstream.video.rtc.signaling import WebSocketClient, SignalingError
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2

from twirp import context

# Import join_call_coordinator_request from coordinator module instead of __init__
from getstream.video.rtc.coordinator import join_call_coordinator_request

logger = logging.getLogger("getstream.video.rtc.connection_manager")


def add_ice_candidates_to_sdp(sdp: str, candidates: List[str]) -> str:
    """
    Adds ICE candidates to each media section (m=) in an SDP offer.

    Args:
        sdp: The original SDP string.
        candidates: A list of ICE candidate strings (without the "a=candidate:" prefix).

    Returns:
        The modified SDP string with candidates added.
    """
    if not candidates:
        return sdp

    candidate_lines = [f"a=candidate:{c}" for c in candidates]
    candidate_lines.append("a=end-of-candidates")
    candidate_section = "\n".join(candidate_lines) + "\n"  # Ensure trailing newline

    # Split SDP into session part and media parts, keeping the delimiter
    parts = re.split("(\nm=)", sdp)
    if not parts or len(parts) <= 1:
        return sdp

    # The first part is always the session description
    modified_sdp_parts = [parts[0]]

    # Iterate through the pairs of (delimiter, media_section)
    for i in range(1, len(parts), 2):
        if i + 1 < len(parts):
            newline_and_m_separator = parts[i]  # This is '\nm='
            media_section_content = parts[i + 1]
            # Append the separator, the original media content (stripped), and the candidate section
            modified_sdp_parts.append(
                newline_and_m_separator
                + media_section_content.rstrip()
                + "\n"
                + candidate_section
            )
        # Handle potential trailing delimiter if split results in odd number of parts (shouldn't happen)
        # else:
        #    modified_sdp_parts.append(parts[i])

    return "".join(modified_sdp_parts)


def patch_sdp_offer(sdp: str) -> str:
    """
    Patches an SDP offer to ensure consistent ICE and DTLS parameters across all media sections.

    This function:
    1. Ensures all media descriptions have the same ice-ufrag, ice-pwd, and fingerprint values
       (using values from the first media section)
    2. Sets all media descriptions' ports to match the first media description's port
    3. Replaces all media descriptions' candidates with candidates from the first media description

    Args:
        sdp: The original SDP string.

    Returns:
        The modified SDP string with consistent parameters across all media sections.
    """
    # Parse the SDP
    session = aiortc.sdp.SessionDescription.parse(sdp)

    # If we have fewer than 2 media sections, nothing to patch
    if len(session.media) < 2:
        return sdp

    # Get the values from the first media section
    first_media = session.media[0]
    reference_port = first_media.port
    reference_ice = first_media.ice
    reference_fingerprints = first_media.dtls.fingerprints if first_media.dtls else []
    reference_candidates = first_media.ice_candidates

    # Apply to all other media sections
    for media in session.media[1:]:
        # Update port
        media.port = reference_port

        # Update ICE parameters
        if reference_ice:
            media.ice.usernameFragment = reference_ice.usernameFragment
            media.ice.password = reference_ice.password
            media.ice.iceLite = reference_ice.iceLite

        # Update DTLS fingerprints
        if media.dtls and reference_fingerprints:
            media.dtls.fingerprints = reference_fingerprints.copy()

        # Replace ICE candidates
        media.ice_candidates = reference_candidates.copy()
        if reference_candidates:
            media.ice_candidates_complete = True

    # Convert back to string
    return str(session)


class ConnectionError(Exception):
    """Exception raised when connection to the call fails."""

    pass


class PublisherPeerConnection(aiortc.RTCPeerConnection):
    def __init__(
        self,
        manager: "ConnectionManager",
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

    async def handle_answer(self, response: SetPublisherResponse):
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


def parse_track_id(id: str) -> tuple[str, str]:
    """
    Parse the webRTC media track and returns a tuple including: the id of the participant, the type of track

    """
    participant_id, track_type, _ = id.split(":")
    return participant_id, track_type


class SubscriberPeerConnection(aiortc.RTCPeerConnection):
    def __init__(
        self,
        manager: "ConnectionManager",
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
        self.manager = manager

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
            participant_id, track_type = parse_track_id(track.id)
            self.tracks[participant_id][track_type].append(track)
            track.on("ended", functools.partial(self.handle_track_ended, track))

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
        self.twirp_signaling_client: SignalClient
        self.twirp_context: context.Context

        # Add publisher peer connection attribute
        self.publisher_pc: Optional[PublisherPeerConnection] = None

        # this is used to associate participants to the track prefix that is used on webrtc track SSRCs
        self._track_user_prefixes = {}

        # set to true if you want to connect to a local SFU
        self.local_sfu = True
        self.publisher_negotiation_lock = asyncio.Lock()

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
            self.ws_client = WebSocketClient(
                ws_url, join_request, asyncio.get_running_loop()
            )

            # Connect to the WebSocket server and wait for the first message
            logger.info(f"Establishing WebSocket connection to {ws_url}")
            sfu_event = await self.ws_client.connect()

            self.subscriber_pc = SubscriberPeerConnection(manager=self)
            self.twirp_signaling_client = SignalClient(
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

        self.ws_client.on_event("ice_trickle", self._on_ice_trickle)
        self.ws_client.on_event("subscriber_offer", self._on_subscriber_offer)
        # Mark as running and clear stop event
        self.running = True
        self._stop_event.clear()

    # TODO: synchronize access to this method
    async def _on_subscriber_offer(self, event: events_pb2.SubscriberOffer):
        logger.info(
            "Subscriber offer received, waiting for ICE gathering to be complete"
        )

        # Wait for at least one ICE candidate to be received/gathered locally
        # This avoids sending an answer before we have any candidates to include.
        # Note: In a production scenario, you might want a more sophisticated
        # mechanism to ensure *all* relevant candidates are gathered, possibly
        # involving the 'icegatheringstatechange' event being 'complete'.
        await self.subscriber_pc._received_ice_event.wait()

        # Use the new robust function to add candidates
        patched_sdp = add_ice_candidates_to_sdp(
            event.sdp, self.subscriber_pc._ice_candidates
        )

        # The SDP offer from the SFU might already contain candidates (trickled)
        # or have a different structure. We set it as the remote description.
        # The aiortc library handles merging and interpretation.
        remote_description = aiortc.RTCSessionDescription(type="offer", sdp=patched_sdp)
        logger.debug(f"""Setting remote description with patched SDP:
{remote_description.sdp}""")
        await self.subscriber_pc.setRemoteDescription(remote_description)

        # Create the answer based on the remote offer (which includes our candidates)
        answer = await self.subscriber_pc.createAnswer()
        # Set the local description. aiortc will manage the SDP content.
        await self.subscriber_pc.setLocalDescription(answer)

        logger.info(
            f"""Sending answer with local description:
{self.subscriber_pc.localDescription.sdp}"""
        )
        # Use the wrapped client; errors will raise SfuRpcError
        try:
            await self.twirp_signaling_client.SendAnswer(
                ctx=self.twirp_context,
                request=signal_pb2.SendAnswerRequest(
                    peer_type=models_pb2.PEER_TYPE_SUBSCRIBER,
                    sdp=self.subscriber_pc.localDescription.sdp,
                    session_id=self.session_id,
                ),
                server_path_prefix="",  # Note: Our wrapper doesn't need this, underlying client handles prefix
            )
            logger.info("Subscriber answer sent successfully.")
        except SfuRpcError as e:
            logger.error(f"Failed to send subscriber answer: {e}")
            # Decide how to handle: maybe close connection, notify user, etc.
            # For now, just log the error.
        except Exception as e:
            logger.error(f"Unexpected error sending subscriber answer: {e}")

    async def _on_ice_trickle(self, event: events_pb2.ICETrickle):
        logger.info(
            f"received ICE trickle for peer type {models_pb2.PEER_TYPE_SUBSCRIBER}"
        )
        candidate_sdp = json.loads(event.ice_candidate)["candidate"]

        if event.peer_type == models_pb2.PEER_TYPE_SUBSCRIBER:
            await self.subscriber_pc.handle_remote_ice_candidate(candidate_sdp)
        else:
            # if we receive this and publisher_pc is not set, something is very wrong and we should crash
            # Check if publisher_pc exists before accessing it
            if self.publisher_pc:
                await self.publisher_pc.handle_remote_ice_candidate(candidate_sdp)
            else:
                logger.warning(
                    "Received ICE trickle for publisher, but publisher_pc is not initialized."
                )

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
        """Async iterator method to yield events from the WebSocket connection."""
        if not self.running or self._stop_event.is_set():
            raise StopAsyncIteration

        try:
            # Wait for the next event from the WebSocket client
            # Add a timeout to prevent indefinite blocking if stop_event is set
            event = await asyncio.wait_for(
                self.ws_client.event_queue.get(), timeout=0.1
            )
            self.ws_client.event_queue.task_done()
            return event
        except asyncio.TimeoutError:
            # If timeout occurs, check stop_event again and continue or raise StopAsyncIteration
            if not self.running or self._stop_event.is_set():
                raise StopAsyncIteration
            # If not stopping, continue waiting for the next event
            return await self.__anext__()  # Recursive call, ensure base case works
        except asyncio.CancelledError:
            logger.info("Async iterator cancelled.")
            raise StopAsyncIteration

    def __aiter__(self) -> AsyncIterator:
        """Return self as the async iterator."""
        return self

    async def leave(self):
        """Gracefully leave the call and close connections."""
        logger.info("Leaving the call")
        self.running = False
        self._stop_event.set()  # Signal the iterator to stop

        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None
        if self.subscriber_pc:
            await self.subscriber_pc.close()
            self.subscriber_pc = None
        if self.publisher_pc:
            await self.publisher_pc.close()
            self.publisher_pc = None

        # Add any other cleanup needed
        logger.info("Call left and connections closed")

    async def addTracks(self, audio=None, video=None):
        """
        Add multiple audio and video tracks in a single negotiation.

        Args:
            audio: An optional audio MediaStreamTrack to publish
            video: An optional video MediaStreamTrack to publish

        This method is more efficient than adding tracks individually as it
        performs a single offer/answer negotiation for all tracks.
        """
        if not self.running:
            logger.error("Connection manager not running. Call join() first.")
            return

        if not audio and not video:
            logger.warning("No tracks provided to addTracks")
            return

        track_infos = []

        # Prepare audio track info if provided
        if audio:
            audio_info = TrackInfo(
                track_id=audio.id,
                track_type=TRACK_TYPE_AUDIO,
            )
            track_infos.append(audio_info)

        # Prepare video track info if provided
        if video:
            video_info = TrackInfo(
                track_id=video.id,
                track_type=TRACK_TYPE_VIDEO,
                layers=[
                    VideoLayer(
                        rid="f",
                        video_dimension=VideoDimension(
                            width=1280,
                            height=720,
                        ),
                        bitrate=1250,
                        fps=24,
                    ),
                ],
            )
            track_infos.append(video_info)

        # Acquire lock for negotiation
        await self.publisher_negotiation_lock.acquire()

        try:
            logger.info(f"Adding tracks: {len(track_infos)} tracks")

            if self.publisher_pc is None:
                self.publisher_pc = PublisherPeerConnection(manager=self)

            # Add all tracks to the peer connection
            if audio:
                self.publisher_pc.addTrack(audio)
                logger.info(f"Added audio track {audio.id}")

            if video:
                self.publisher_pc.addTrack(video)
                logger.info(f"Added video track {video.id}")

            # Create and set local description
            logger.info("Creating publisher offer for multiple tracks")
            offer = await self.publisher_pc.createOffer()
            await self.publisher_pc.setLocalDescription(offer)

            logger.info(
                f"Sending publisher offer to SFU with {len(track_infos)} tracks"
            )

            try:
                # Patch the SDP offer to ensure consistent parameters
                patched_sdp = patch_sdp_offer(self.publisher_pc.localDescription.sdp)
                logger.info(
                    "Patched SDP offer for consistent parameters across media sections"
                )

                response = await self.twirp_signaling_client.SetPublisher(
                    ctx=self.twirp_context,
                    request=signal_pb2.SetPublisherRequest(
                        session_id=self.session_id, sdp=patched_sdp, tracks=track_infos
                    ),
                    server_path_prefix="",  # Note: Our wrapper doesn't need this, underlying client handles prefix
                )
                logger.info("Publisher offer sent successfully.")
                await self.publisher_pc.handle_answer(response)
            except SfuRpcError as e:
                logger.error(f"Failed to set publisher: {e}")
                # Decide how to handle: maybe close connection, notify user, etc.
                # Raising ConnectionError might be appropriate here
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                raise ConnectionError(f"Failed to set publisher: {e}") from e
            except Exception as e:
                logger.error(f"Failed during publisher setup: {e}")
                # Ensure cleanup
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                # Re-raise as ConnectionError or a more specific error if appropriate
                raise ConnectionError(
                    f"Unexpected error during publisher setup: {e}"
                ) from e
        finally:
            logger.info("Released publisher negotiation lock")
            self.publisher_negotiation_lock.release()

        # Wait for the connection to establish
        await asyncio.sleep(1)  # Initial wait for answer/ICE

        # Monitor readyState for provided tracks
        if audio or video:
            while self.publisher_pc and self.publisher_pc.connectionState != "failed":
                await asyncio.sleep(1)
                # Check if either track has ended
                if (audio and audio.readyState == "ended") or (
                    video and video.readyState == "ended"
                ):
                    logger.info("One or more media tracks have ended.")
                    break

    # Keep addTrack for backward compatibility
    async def addTrack(
        self, track: aiortc.mediastreams.MediaStreamTrack, track_info: TrackInfo
    ):
        """
        Add a single track to the publisher peer connection.

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.
        """
        if not self.running:
            logger.error("Connection manager not running. Call join() first.")
            return

        logger.info(f"adding track {track.id}")

        await self.publisher_negotiation_lock.acquire()

        try:
            logger.info(f"track {track.id} enter exclusive lock")
            if self.publisher_pc is None:
                self.publisher_pc = PublisherPeerConnection(manager=self)

            self.publisher_pc.addTrack(track)
            logger.info("Creating publisher offer")

            offer = await self.publisher_pc.createOffer()
            await self.publisher_pc.setLocalDescription(offer)

            logger.info(
                f"Sending publisher offer to SFU {self.publisher_pc.localDescription.sdp}"
            )

            try:
                # Patch the SDP offer to ensure consistent parameters
                patched_sdp = patch_sdp_offer(self.publisher_pc.localDescription.sdp)
                logger.info(
                    "Patched SDP offer for consistent parameters across media sections"
                )

                response = await self.twirp_signaling_client.SetPublisher(
                    ctx=self.twirp_context,
                    request=signal_pb2.SetPublisherRequest(
                        session_id=self.session_id, sdp=patched_sdp, tracks=[track_info]
                    ),
                    server_path_prefix="",  # Note: Our wrapper doesn't need this, underlying client handles prefix
                )
                logger.info("Publisher offer sent successfully.")
                await self.publisher_pc.handle_answer(response)
            except SfuRpcError as e:
                logger.error(f"Failed to set publisher: {e}")
                # Decide how to handle: maybe close connection, notify user, etc.
                # Raising ConnectionError might be appropriate here
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                raise ConnectionError(f"Failed to set publisher: {e}") from e
            except Exception as e:
                logger.error(f"Failed during publisher setup or file playback: {e}")
                # Ensure cleanup
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                # Re-raise as ConnectionError or a more specific error if appropriate
                raise ConnectionError(
                    f"Unexpected error during publisher setup/playback: {e}"
                ) from e
        finally:
            logger.info(f"track {track.id} release exclusive lock")
            self.publisher_negotiation_lock.release()

        # Wait for the connection to establish and media playing to finish
        # This is a simplified wait; real-world might need more robust handling
        # of player state or connection state changes.
        await asyncio.sleep(1)  # Initial wait for answer/ICE
        while self.publisher_pc and self.publisher_pc.connectionState != "failed":
            # Keep running while player is active or connection is ok
            # MediaPlayer doesn't have an explicit 'done' event we can easily await
            # We rely on the tracks ending or connection failing
            await asyncio.sleep(1)
            # Add checks here if player has specific state to monitor
            if track.readyState == "ended":
                logger.info("Media player tracks have ended.")
                break

    # Add convenience methods for backward compatibility that use the new addTracks method
    async def add_audio_track(self, track: aiortc.mediastreams.MediaStreamTrack):
        """
        Add an audio track to the publisher peer connection.

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.
        """
        await self.addTracks(audio=track)

    async def add_video_track(self, track: aiortc.mediastreams.MediaStreamTrack):
        """
        Add a video track to the publisher peer connection.

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.
        """
        await self.addTracks(video=track)
