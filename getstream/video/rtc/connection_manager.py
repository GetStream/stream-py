import json
import uuid

import asyncio
import logging
from typing import Optional

import aiortc

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
from getstream.video.rtc.twirp_client_wrapper import SignalClient, SfuRpcError
from getstream.video.rtc.signaling import WebSocketClient, SignalingError
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2

from twirp import context

from getstream.video.rtc.coordinator import join_call_coordinator_request

from getstream.video.rtc.track_util import (
    BufferedMediaTrack,
    detect_video_properties,
    patch_sdp_offer,
    add_ice_candidates_to_sdp,
)

from getstream.video.rtc.pc import (
    PublisherPeerConnection,
    SubscriberPeerConnection,
)

from pyee.asyncio import AsyncIOEventEmitter

logger = logging.getLogger(__name__)


class ConnectionError(Exception):
    """Exception raised when connection to the call fails."""

    pass


class ParticipantsState(AsyncIOEventEmitter):
    def __init__(self):
        super().__init__()
        self._participants = {}
        self._track_lookup_prefixes = {}

    def get_user_from_track_id(self, track_id: str) -> Optional[models_pb2.Participant]:
        prefix = track_id.split(":")[0]
        return self._participants.get(self._participants.get(prefix))

    @staticmethod
    def participant_id(participant: models_pb2.Participant):
        return participant.session_id, participant.user_id

    async def _on_participant_joined(self, event: events_pb2.ParticipantJoined):
        self._track_lookup_prefixes[event.participant.track_lookup_prefix] = (
            event.participant.user_id
        )
        self._participants[ParticipantsState.participant_id(event.participant)] = (
            event.participant
        )
        self.emit("participant_joined", event.participant)

    async def _on_participant_left(self, event: events_pb2.ParticipantLeft):
        del self._track_lookup_prefixes[event.participant.track_lookup_prefix]
        del self._participants[ParticipantsState.participant_id(event.participant)]
        self.emit("participant_left", event.participant)


class ConnectionManager(AsyncIOEventEmitter):
    def __init__(self, call: Call, user_id: str = None, create: bool = True, **kwargs):
        super().__init__()

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
        self.subscriber_pc: Optional[SubscriberPeerConnection] = None
        self.twirp_signaling_client: SignalClient
        self.twirp_context: context.Context

        # Add publisher peer connection attribute
        self.publisher_pc: Optional[PublisherPeerConnection] = None

        # this is used to associate participants to the track prefix that is used on webrtc track SSRCs
        self._track_user_prefixes = {}

        # set to true if you want to connect to a local SFU
        self.local_sfu = False
        self.publisher_negotiation_lock = asyncio.Lock()
        self.subscriber_negotiation_lock = asyncio.Lock()

        self.participants_state = ParticipantsState()

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

            self.subscriber_pc = SubscriberPeerConnection(connection=self)

            @self.subscriber_pc.on("audio")
            async def on_audio(pcm_data, user):
                self.emit("audio", pcm_data, user)

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

        self.ws_client.on_event(
            "participant_joined", self.participants_state._on_participant_joined
        )
        self.ws_client.on_event("ice_trickle", self._on_ice_trickle)
        self.ws_client.on_event("subscriber_offer", self._on_subscriber_offer)
        # Mark as running and clear stop event
        self.running = True
        self._stop_event.clear()

    async def wait(self):
        """
        Wait until the connection is over.

        This is useful for tests and examples where you want to wait for the
        connection to end rather than just sleeping for a fixed time.

        Returns when the connection is over (either naturally ended or
        explicitly stopped with leave()).
        """
        await self._stop_event.wait()

    async def leave(self):
        """Gracefully leave the call and close connections."""
        logger.info("Leaving the call")
        self.running = False
        self._stop_event.set()  # Signal the iterator to stop

        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None
        if self.subscriber_pc is not None:
            await self.subscriber_pc.close()
            self.subscriber_pc = None
        if self.publisher_pc:
            await self.publisher_pc.close()
            self.publisher_pc = None

        # Add any other cleanup needed
        logger.info("Call left and connections closed")

    async def _on_subscriber_offer(self, event: events_pb2.SubscriberOffer):
        logger.info("Subscriber offer received")

        await self.subscriber_negotiation_lock.acquire()

        try:
            logger.info(
                "Subscriber offer received, waiting for ICE gathering to be complete"
            )
            # Wait for at least one ICE candidate to be received/gathered locally
            # This avoids sending an answer before we have any candidates to include.
            # Note: In a production scenario, you might want a more sophisticated
            # mechanism to ensure *all* relevant candidates are gathered, possibly
            # involving the 'icegatheringstatechange' event being 'complete'.
            await self.subscriber_pc._received_ice_event.wait()

            patched_sdp = add_ice_candidates_to_sdp(
                event.sdp, self.subscriber_pc._ice_candidates
            )

            # The SDP offer from the SFU might already contain candidates (trickled)
            # or have a different structure. We set it as the remote description.
            # The aiortc library handles merging and interpretation.
            remote_description = aiortc.RTCSessionDescription(
                type="offer", sdp=patched_sdp
            )
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
        finally:
            self.subscriber_negotiation_lock.release()

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

    async def prepare_video_track_info(
        self, video: aiortc.mediastreams.MediaStreamTrack
    ) -> tuple[TrackInfo, aiortc.mediastreams.MediaStreamTrack]:
        """
        Prepare video track info by detecting its properties.

        Args:
            video: A video MediaStreamTrack

        Returns:
            A tuple of (TrackInfo, buffered_video_track)
        """
        buffered_video = None

        try:
            # Wrap the video track to buffer peeked frames
            buffered_video = BufferedMediaTrack(video)

            # Detect video properties - with timeout to avoid hanging
            video_props = await asyncio.wait_for(
                detect_video_properties(buffered_video), timeout=3.0
            )

            video_info = TrackInfo(
                track_id=buffered_video.id,
                track_type=TRACK_TYPE_VIDEO,
                layers=[
                    VideoLayer(
                        rid="f",
                        video_dimension=VideoDimension(
                            width=video_props["width"],
                            height=video_props["height"],
                        ),
                        bitrate=video_props["bitrate"],
                        fps=video_props["fps"],
                    ),
                ],
            )

            # Return both the track info and the buffered track
            return video_info, buffered_video

        except asyncio.TimeoutError:
            logger.error("Timeout detecting video properties")
            # Fall back to default properties
            if buffered_video:
                video_info = TrackInfo(
                    track_id=buffered_video.id,
                    track_type=TRACK_TYPE_VIDEO,
                    layers=[
                        VideoLayer(
                            rid="f",
                            video_dimension=VideoDimension(
                                width=1280,
                                height=720,
                            ),
                            bitrate=1500,
                            fps=30,
                        ),
                    ],
                )
                return video_info, buffered_video
            raise
        except Exception as e:
            logger.error(f"Error preparing video track: {e}")
            # Clean up on error
            if buffered_video:
                try:
                    buffered_video.stop()
                except Exception as e:
                    logger.error(f"Error stopping buffered video: {e}")
            # Re-raise the exception
            raise

    async def add_tracks(
        self,
        audio: Optional[aiortc.mediastreams.MediaStreamTrack] = None,
        video: Optional[aiortc.mediastreams.MediaStreamTrack] = None,
    ):
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
            video_info, buffered_video = await self.prepare_video_track_info(video)
            track_infos.append(video_info)
            video = buffered_video

        try:
            await self.publisher_negotiation_lock.acquire()

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
                    server_path_prefix="",
                )
                logger.info("Publisher offer sent successfully.")
                await self.publisher_pc.handle_answer(response)
            except SfuRpcError as e:
                logger.error(f"Failed to set publisher: {e}")
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                raise ConnectionError(f"Failed to set publisher: {e}") from e
            except Exception as e:
                logger.error(f"Failed during publisher setup: {e}")
                if self.publisher_pc:
                    await self.publisher_pc.close()
                    self.publisher_pc = None
                raise ConnectionError(
                    f"Unexpected error during publisher setup: {e}"
                ) from e
            # TODO: use proper syncronization here!
            await asyncio.sleep(1.2)
        finally:
            logger.info("Released publisher negotiation lock")
            self.publisher_negotiation_lock.release()

    # Keep addTrack for backward compatibility
    async def addTrack(
        self,
        track: aiortc.mediastreams.MediaStreamTrack,
        track_info: Optional[TrackInfo] = None,
    ):
        """
        Add a single track to the publisher peer connection.

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.

        Args:
            track: The MediaStreamTrack to add
            track_info: Optional TrackInfo object. If not provided, it will be generated
                       automatically for video tracks.
        """
        if not self.running:
            logger.error("Connection manager not running. Call join() first.")
            return

        logger.info(f"adding track {track.id}")

        # If track is video and no track_info provided, generate it
        if track.kind == "video" and track_info is None:
            try:
                track_info, track = await self.prepare_video_track_info(track)
            except Exception as e:
                logger.error(f"Failed to automatically detect video properties: {e}")
                # Create a default track info if auto-detection fails
                track_info = TrackInfo(
                    track_id=track.id,
                    track_type=TRACK_TYPE_VIDEO,
                    layers=[
                        VideoLayer(
                            rid="f",
                            video_dimension=VideoDimension(
                                width=1280,
                                height=720,
                            ),
                            bitrate=1500,
                            fps=30,
                        ),
                    ],
                )
        # For audio tracks with no track_info, create a default one
        elif track.kind == "audio" and track_info is None:
            track_info = TrackInfo(
                track_id=track.id,
                track_type=TRACK_TYPE_AUDIO,
            )

        # Ensure we have a track_info at this point
        if track_info is None:
            logger.error("No track_info provided and couldn't create one automatically")
            return

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

        Args:
            track: An audio MediaStreamTrack to publish

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.
        """
        if track.kind != "audio":
            raise ValueError("Expected an audio track")

        await self.add_tracks(audio=track)

    async def add_video_track(self, track: aiortc.mediastreams.MediaStreamTrack):
        """
        Add a video track to the publisher peer connection.

        Args:
            track: A video MediaStreamTrack to publish

        Note: This method is kept for backward compatibility.
        For better performance, use addTracks to add multiple tracks at once.
        """
        if track.kind != "video":
            raise ValueError("Expected a video track")

        await self.add_tracks(video=track)
