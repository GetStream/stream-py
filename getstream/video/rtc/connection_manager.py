import asyncio
import json
import logging
import uuid
from typing import Optional, Dict, Any

import aioice
import aiortc
from twirp.context import Context

from getstream.utils import StreamAsyncIOEventEmitter
from getstream.video.rtc.coordinator.ws import StreamAPIWS
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.twirp_client_wrapper import SfuRpcError, SignalClient

from getstream.video.call import Call
from getstream.video.rtc.connection_utils import (
    ConnectionState,
    SfuConnectionError,
    ConnectionOptions,
    connect_websocket,
    join_call,
)
from getstream.video.rtc.track_util import (
    fix_sdp_msid_semantic,
    fix_sdp_rtcp_fb,
    parse_track_stream_mapping,
)
from getstream.video.rtc.network_monitor import NetworkMonitor
from getstream.video.rtc.recording import RecordingManager
from getstream.video.rtc.participants import ParticipantsState
from getstream.video.rtc.tracks import SubscriptionConfig, SubscriptionManager
from getstream.video.rtc.reconnection import ReconnectionManager
from getstream.video.rtc.peer_connection import PeerConnectionManager
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery
from getstream.video.rtc.models import JoinCallResponse

logger = logging.getLogger(__name__)


async def _log_event(event_type: str, data: Any):
    logger.debug(f"Received event {event_type}: {data}")


class ConnectionManager(StreamAsyncIOEventEmitter):
    """Main connection manager facade for video streaming."""

    def __init__(
        self,
        call: Call,
        user_id: Optional[str] = None,
        create: bool = True,
        subscription_config: Optional[SubscriptionConfig] = None,
        **kwargs: Any,
    ):
        super().__init__()

        # Public attributes
        self.call: Call = call
        self.user_id: Optional[str] = user_id
        self.create: bool = create
        self.kwargs: Dict[str, Any] = kwargs
        self.running: bool = False
        self.session_id: str = str(uuid.uuid4())
        self.join_response: Optional[JoinCallResponse] = None
        self.local_sfu: bool = False  # Local SFU flag for development

        # Private attributes
        self._connection_state: ConnectionState = ConnectionState.IDLE
        self._stop_event: asyncio.Event = asyncio.Event()
        self._connection_options: ConnectionOptions = ConnectionOptions()
        self._ws_client = None
        self._coordinator_ws_client = None

        # Initialize private managers
        self._participants_state: ParticipantsState = ParticipantsState()
        self._recording_manager: RecordingManager = RecordingManager()
        self._network_monitor: NetworkMonitor = NetworkMonitor(self)
        self._reconnector: ReconnectionManager = ReconnectionManager(self)
        self._subscription_manager: SubscriptionManager = SubscriptionManager(
            self, subscription_config
        )
        self._peer_manager: PeerConnectionManager = PeerConnectionManager(self)

        self.recording_manager = self._recording_manager  # type: ignore
        self.participants_state = self._participants_state  # type: ignore
        self.reconnector = self._reconnector  # type: ignore

        self.twirp_signaling_client = None
        self.twirp_context: Optional[Context] = None

    @property
    def connection_state(self) -> ConnectionState:
        """Get the current connection state."""
        return self._connection_state

    @connection_state.setter
    def connection_state(self, state: ConnectionState):
        """Set the connection state and emit state change event."""
        if state != self._connection_state:
            old_state = self._connection_state
            self._connection_state = state
            # Schedule the emit as a background task since property setters cannot be async
            self.emit("connection.state_changed", {"old": old_state, "new": state})

    async def _on_ice_trickle(self, event):
        """Handle ICE trickle from SFU."""
        logger.debug(f"Received ICE trickle for peer type {event.peer_type}")

        try:
            ice_candidate = json.loads(event.ice_candidate)
            candidate_sdp = ice_candidate.get("candidate")
            if not candidate_sdp:
                return

            candidate = aiortc.rtcicetransport.candidate_from_aioice(
                aioice.Candidate.from_sdp(candidate_sdp)
            )
            candidate.sdpMid = ice_candidate.get("sdpMid")
            candidate.sdpMLineIndex = ice_candidate.get("sdpMLineIndex")

            if (
                event.peer_type == models_pb2.PEER_TYPE_SUBSCRIBER
                and self.subscriber_pc
            ):
                await self.subscriber_pc.addIceCandidate(candidate)
            elif self.publisher_pc:
                await self.publisher_pc.addIceCandidate(candidate)
        except Exception as e:
            logger.debug(f"Error handling ICE trickle: {e}")

    async def _on_subscriber_offer(self, event: events_pb2.SubscriberOffer):
        logger.info("Subscriber offer received")

        await self.subscriber_negotiation_lock.acquire()

        try:
            # Fix any invalid msid-semantic format in the SDP
            fixed_sdp = fix_sdp_msid_semantic(event.sdp)
            # Fix any invalid rtcp-fb lines
            fixed_sdp = fix_sdp_rtcp_fb(fixed_sdp)
            # Parse SDP to create track_id to stream_id mapping
            self.participants_state.set_track_stream_mapping(
                parse_track_stream_mapping(fixed_sdp)
            )
            # The SDP offer from the SFU might already contain candidates (trickled)
            # or have a different structure. We set it as the remote description.
            # The aiortc library handles merging and interpretation.
            remote_description = aiortc.RTCSessionDescription(
                type="offer", sdp=fixed_sdp
            )
            logger.debug(f"""Setting remote description with SDP:
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

    async def _connect_internal(
        self,
        region: Optional[str] = None,
        ws_url: Optional[str] = None,
        token: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """
        Internal connection method that handles the core connection logic.

        Args:
            region: Optional region to connect to
            ws_url: Optional WebSocket URL to connect to
            token: Optional authentication token
            session_id: Optional session ID

        Raises:
            SfuConnectionError: If connection fails
        """
        self.connection_state = ConnectionState.JOINING

        # Step 1: Determine region
        if not region:
            try:
                region = HTTPHintLocationDiscovery(logger=logger).discover()
            except Exception as e:
                logger.warning(f"Failed to discover location: {e}")
                location = "FRA"
        logger.debug(f"Using location: {region}")
        location = region

        # Step 2: Create coordinator websocket
        self._coordinator_ws_client = StreamAPIWS(
            call=self.call,
            user_details={"id": self.user_id},
        )
        self._coordinator_ws_client.on_wildcard("*", _log_event)
        await self._coordinator_ws_client.connect()

        # Step 3: Join call via coordinator
        if not (ws_url or token):
            join_response = await join_call(
                self.call,
                self.user_id,
                location,
                self.create,
                self.local_sfu,
                self._coordinator_ws_client._client_id,
                **self.kwargs,
            )
            ws_url = join_response.data.credentials.server.ws_endpoint
            token = join_response.data.credentials.token
            self.join_response = join_response
            logger.debug(f"coordinator join response: {join_response.data}")

        # Use provided session_id or current one
        current_session_id = session_id or self.session_id

        await self._peer_manager.setup_subscriber()

        # Step 4: Connect to WebSocket
        try:
            self._ws_client, sfu_event = await connect_websocket(
                token=token,
                ws_url=ws_url,
                session_id=current_session_id,
                options=self._connection_options,
            )

            self._ws_client.on_wildcard("*", _log_event)
            self._ws_client.on_event("ice_trickle", self._on_ice_trickle)

            # Connect track subscription events to subscription manager
            self._ws_client.on_event(
                "track_published", self._subscription_manager.handle_track_published
            )
            self._ws_client.on_event(
                "track_unpublished", self._subscription_manager.handle_track_unpublished
            )

            # Connect subscriber offer event to handle SDP negotiation
            self._ws_client.on_event("subscriber_offer", self._on_subscriber_offer)

            if hasattr(sfu_event, "join_response"):
                logger.debug(f"sfu join response: {sfu_event.join_response}")
                # Populate participants state with existing participants
                if hasattr(sfu_event.join_response, "call_state"):
                    for participant in sfu_event.join_response.call_state.participants:
                        self._participants_state.add_participant(participant)
                # Update reconnection config
                if hasattr(sfu_event.join_response, "fast_reconnect_deadline_seconds"):
                    self._reconnector._fast_reconnect_deadline_seconds = (
                        sfu_event.join_response.fast_reconnect_deadline_seconds
                    )
            else:
                logger.warning(f"No join response from WebSocket: {sfu_event}")

            logger.debug(f"WebSocket connected successfully to {ws_url}")
        except Exception as e:
            logger.error(f"Failed to connect WebSocket to {ws_url}: {e}")
            raise SfuConnectionError(f"WebSocket connection failed: {e}")

        # Step 5: Create SFU signaling client
        twirp_server_url = self.join_response.data.credentials.server.url
        self.twirp_signaling_client = SignalClient(address=twirp_server_url)
        self.twirp_context = Context(headers={"authorization": token})
        # Mark as connected
        self.running = True
        self.connection_state = ConnectionState.JOINED
        self._stop_event.clear()

        logger.info("Successfully connected to SFU")

    async def connect(self):
        """
        Connect to SFU.

        This method automatically handles retry logic for transient errors
        like "server is full" and network issues.
        """
        logger.info("Connecting to SFU")
        await self._connect_internal()

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
        self._stop_event.set()

        await self._recording_manager.cleanup()
        await self._network_monitor.stop_monitoring()
        await self._peer_manager.close()
        if self._ws_client:
            self._ws_client.close()
            self._ws_client = None
        if self._coordinator_ws_client:
            await self._coordinator_ws_client.disconnect()
            self._coordinator_ws_client = None

        self.connection_state = ConnectionState.LEFT

        logger.info("Call left and connections closed")

    async def __aenter__(self):
        """Async context manager entry."""
        # Register network event handlers
        self._network_monitor.register_event_handlers()

        # Connect with retry
        await self.connect()

        # Start network monitoring
        await self._network_monitor.start_monitoring()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.leave()

    async def add_tracks(self, audio=None, video=None):
        """Add multiple audio and video tracks in a single negotiation."""
        await self._peer_manager.add_tracks(audio, video)

    async def start_recording(
        self, recording_types, user_ids=None, output_dir="recordings"
    ):
        """Start recording."""
        logger.info("Starting recording")
        await self._recording_manager.start_recording(
            recording_types, user_ids, output_dir
        )

    async def stop_recording(self, recording_types=None, user_ids=None):
        """Stop recording."""
        logger.info("Stopping recording")
        await self._recording_manager.stop_recording(recording_types, user_ids)

    @property
    def is_recording(self) -> bool:
        """Check if recording is active."""
        return self._recording_manager.is_recording

    def get_recording_status(self) -> dict:
        """Get current recording status."""
        return self._recording_manager.get_recording_status()

    # WebSocket client helper
    @property
    def ws_client(self):
        return self._ws_client

    @ws_client.setter
    def ws_client(self, value):
        self._ws_client = value

    # Publisher / Subscriber peer-connection shortcuts
    @property
    def publisher_pc(self):
        return self._peer_manager.publisher_pc

    @publisher_pc.setter
    def publisher_pc(self, value):
        self._peer_manager.publisher_pc = value

    @property
    def subscriber_pc(self):
        return self._peer_manager.subscriber_pc

    @subscriber_pc.setter
    def subscriber_pc(self, value):
        self._peer_manager.subscriber_pc = value

    # Negotiation locks

    @property
    def publisher_negotiation_lock(self):
        return self._peer_manager.publisher_negotiation_lock

    @property
    def subscriber_negotiation_lock(self):
        return self._peer_manager.subscriber_negotiation_lock

    async def _cleanup_connections(
        self, ws_client=None, publisher_pc=None, subscriber_pc=None
    ):
        """Close provided connections safely; used by ReconnectionManager."""
        try:
            # Close peer connections (async)
            tasks = []
            if publisher_pc:
                tasks.append(publisher_pc.close())
            if subscriber_pc:
                tasks.append(subscriber_pc.close())

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

            # Close WebSocket client (sync)
            if ws_client:
                try:
                    ws_client.close()
                except Exception:
                    logger.debug("Error closing old WebSocket client", exc_info=True)
        except Exception:
            logger.debug("Error during _cleanup_connections", exc_info=True)

    async def _restore_published_tracks(self):
        """Delegate restoration of previously published tracks to the peer manager."""
        try:
            await self._peer_manager.restore_published_tracks()
        except Exception as e:
            logger.error("Failed to restore published tracks", exc_info=e)
