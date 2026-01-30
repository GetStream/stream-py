import json
import asyncio
import logging
import uuid
from typing import Optional, Dict, Any

import aioice
import aiortc

from getstream.common import telemetry
from getstream.utils import StreamAsyncIOEventEmitter
from getstream.video.rtc.coordinator.ws import StreamAPIWS
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.twirp_client_wrapper import SfuRpcError, SignalClient, Context

from getstream.video.async_call import Call
from getstream.video.rtc.connection_utils import (
    ConnectionState,
    SfuConnectionError,
    ConnectionOptions,
    connect_websocket,
    join_call,
    watch_call,
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
from getstream.video.rtc.models import JoinCallResponse
from getstream.video.rtc.tracer import Tracer
from getstream.video.rtc.stats_reporter import SfuStatsReporter

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

        self.recording_manager = self._recording_manager
        self.participants_state = self._participants_state
        self.reconnector = self._reconnector

        self.twirp_signaling_client = None
        self.twirp_context: Optional[Context] = None
        self._coordinator_task: Optional[asyncio.Task] = None

        # Stats tracing: generation counter (increments on reconnect), tracer, and reporter
        self._sfu_client_tag: int = 0  # Generation counter, never resets during session
        self._sfu_hostname: Optional[str] = None  # Cached SFU hostname
        self.tracer: Tracer = Tracer()
        self.stats_reporter: Optional[SfuStatsReporter] = None

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

    def pc_id(self, pc_type: str) -> str:
        """Get PC ID for tracing.

        Args:
            pc_type: "pub" for publisher or "sub" for subscriber

        Returns:
            PC ID like "0-pub" or "0-sub"
        """
        return f"{self._sfu_client_tag}-{pc_type}"

    def sfu_id(self) -> Optional[str]:
        """Get SFU ID for tracing RPC calls and events.

        Returns:
            SFU ID like "0-sfu-hostname.stream.com" or None if not set
        """
        if self._sfu_hostname:
            # Format: "{tag}-{edge_name}" where edge_name already includes "sfu-" prefix
            return f"{self._sfu_client_tag}-{self._sfu_hostname}"
        return None

    def _extract_sfu_hostname(self) -> Optional[str]:
        """Extract SFU edge name from join response.

        Returns:
            The SFU edge name (e.g., "sfu-dpk-london-...") or None if not available
        """
        if self.join_response and self.join_response.credentials:
            # Use edge_name directly - it already has the correct format like "sfu-dpk-london-..."
            return self.join_response.credentials.server.edge_name
        return None

    async def _on_ice_trickle(self, event):
        """Handle ICE trickle from SFU."""
        logger.debug(f"Received ICE trickle for peer type {event.peer_type}")

        with telemetry.start_as_current_span("rtc.on_ice_trickle") as span:
            try:
                ice_candidate = json.loads(event.ice_candidate)

                candidate_sdp = ice_candidate.get("candidate")
                span.set_attribute("candidate_sdp", candidate_sdp)
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

        with telemetry.start_as_current_span("rtc.on_subscriber_offer") as span:
            await self.subscriber_negotiation_lock.acquire()

            try:
                # Fix any invalid msid-semantic format in the SDP
                fixed_sdp = fix_sdp_msid_semantic(event.sdp)
                # Fix any invalid rtcp-fb lines
                fixed_sdp = fix_sdp_rtcp_fb(fixed_sdp)
                span.set_attribute("sdp", fixed_sdp)
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
                span.set_attribute("remote_description.sdp", fixed_sdp)

                with telemetry.start_as_current_span(
                    "rtc.on_subscriber_offer.set_remote_description"
                ):
                    await self.subscriber_pc.setRemoteDescription(remote_description)

                # Create the answer based on the remote offer (which includes our candidates)
                with telemetry.start_as_current_span(
                    "rtc.on_subscriber_offer.create_answer"
                ) as span:
                    answer = await self.subscriber_pc.createAnswer()
                    span.set_attribute("answer.sdp", answer.sdp)

                # Set the local description. aiortc will manage the SDP content.
                with telemetry.start_as_current_span(
                    "rtc.on_subscriber_offer.set_local_description"
                ) as span:
                    await self.subscriber_pc.setLocalDescription(answer)

                logger.debug(
                    f"""Sending answer with local description:
                {self.subscriber_pc.localDescription.sdp}"""
                )

                try:
                    if self.twirp_signaling_client is None:
                        raise ValueError("twirp_signaling_client is not initialized")
                    await self.twirp_signaling_client.SendAnswer(
                        ctx=self.twirp_context,
                        request=signal_pb2.SendAnswerRequest(
                            peer_type=models_pb2.PEER_TYPE_SUBSCRIBER,
                            sdp=self.subscriber_pc.localDescription.sdp,
                            session_id=self.session_id,
                        ),
                        server_path_prefix="",  # Note: Our wrapper doesn't need this, underlying client handles prefix
                    )
                    logger.debug("Subscriber answer sent successfully.")
                except SfuRpcError as e:
                    logger.error(f"Failed to send subscriber answer: {e}")
                    # Decide how to handle: maybe close connection, notify user, etc.
                    # For now, just log the error.
                except Exception as e:
                    logger.error(f"Unexpected error sending subscriber answer: {e}")
            finally:
                self.subscriber_negotiation_lock.release()

    async def _connect_coordinator_ws(self):
        """
        Connects to the coordinator websocket and subscribes to events.
        """

        with telemetry.start_as_current_span(
            "coordinator-setup",
        ):
            with telemetry.start_as_current_span(
                "coordinator-ws-connect",
            ):
                self._coordinator_ws_client = StreamAPIWS(
                    call=self.call,
                    user_details={"id": self.user_id},
                )
                self._coordinator_ws_client.on_wildcard("*", _log_event)
                await self._coordinator_ws_client.connect()

            with telemetry.start_as_current_span(
                "watch-call",
            ):
                if self.user_id is None:
                    raise ValueError("user_id is required for watching a call")
                if self._coordinator_ws_client._client_id is None:
                    raise ValueError("coordinator ws client_id is not set")
                await watch_call(
                    self.call, self.user_id, self._coordinator_ws_client._client_id
                )

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
        # with telemetry.start_as_current_span(
        #     "location-discovery",
        # ) as span:
        #     if not region:
        #         try:
        #             region = HTTPHintLocationDiscovery(logger=logger).discover()
        #         except Exception as e:
        #             logger.warning(f"Failed to discover location: {e}")
        #             location = "FRA"
        #     logger.debug(f"Using location: {region}")
        #     location = region
        #     span.set_attribute("location", location)

        # Step 2: Join call via coordinator
        with telemetry.start_as_current_span(
            "coordinator-join-call",
        ) as span:
            if not (ws_url or token):
                if self.user_id is None:
                    raise ValueError("user_id is required for joining a call")
                join_response = await join_call(
                    self.call,
                    self.user_id,
                    "auto",
                    self.create,
                    self.local_sfu,
                    **self.kwargs,
                )
                ws_url = join_response.data.credentials.server.ws_endpoint
                token = join_response.data.credentials.token
                self.join_response = join_response.data
                # Extract and cache SFU hostname for tracing
                self._sfu_hostname = self._extract_sfu_hostname()
                logger.debug(f"coordinator join response: {join_response.data}")
                span.set_attribute(
                    "credentials", join_response.data.credentials.to_json()
                )

        # Use provided session_id or current one
        current_session_id = session_id or self.session_id

        await self._peer_manager.setup_subscriber()

        # Step 3: Connect to WebSocket
        if not token or not ws_url:
            raise ValueError("token and ws_url are required for WebSocket connection")
        try:
            with telemetry.start_as_current_span(
                "sfu-signaling-ws-connect",
            ) as span:
                self._ws_client, sfu_event = await connect_websocket(
                    token=token,
                    ws_url=ws_url,
                    session_id=current_session_id,
                    options=self._connection_options,
                    tracer=self.tracer,
                    sfu_id_fn=self.sfu_id,
                )

                self._ws_client.on_wildcard("*", _log_event)
                self._ws_client.on_event("ice_trickle", self._on_ice_trickle)

            # Connect track subscription events to subscription manager
            self._ws_client.on_event(
                "participant_joined", self.participants_state._on_participant_joined
            )
            self._ws_client.on_event(
                "participant_left", self.participants_state._on_participant_left
            )
            self._ws_client.on_event(
                "track_published", self._subscription_manager.handle_track_published
            )
            self._ws_client.on_event(
                "track_unpublished", self._subscription_manager.handle_track_unpublished
            )

            # Connect subscriber offer event to handle SDP negotiation
            self._ws_client.on_event("subscriber_offer", self._on_subscriber_offer)

            # Re-emit the events so they can be subscribed to on the ConnectionManager
            self._ws_client.on_wildcard("*", self.emit)

            if hasattr(sfu_event, "join_response"):
                logger.debug(f"sfu join response: {sfu_event.join_response}")
                # Populate participants state with existing participants
                if hasattr(sfu_event.join_response, "call_state"):
                    for participant in sfu_event.join_response.call_state.participants:
                        self._participants_state._add_participant(participant)
                # Update reconnection config
                if hasattr(sfu_event.join_response, "fast_reconnect_deadline_seconds"):
                    self._reconnector._fast_reconnect_deadline_seconds = (
                        sfu_event.join_response.fast_reconnect_deadline_seconds
                    )
            else:
                logger.exception(f"No join response from WebSocket: {sfu_event}")

            logger.debug(f"WebSocket connected successfully to {ws_url}")
        except Exception as e:
            logger.exception(f"Failed to connect WebSocket to {ws_url}: {e}")
            raise SfuConnectionError(f"WebSocket connection failed: {e}") from e

        # Step 5: Create SFU signaling client with tracer
        if self.join_response is None:
            raise ValueError("join_response is not set")
        twirp_server_url = self.join_response.credentials.server.url
        self.twirp_signaling_client = SignalClient(
            address=twirp_server_url,
            tracer=self.tracer,
            sfu_id_fn=self.sfu_id,
        )
        self.twirp_context = Context(headers={"authorization": token})

        # Start stats reporter
        self.stats_reporter = SfuStatsReporter(self)
        self.stats_reporter.start()

        # Mark as connected
        self.running = True
        self.connection_state = ConnectionState.JOINED
        self._stop_event.clear()

        logger.info("Successfully connected to SFU")

    @telemetry.with_span("connect")
    async def connect(self):
        """
        Connect to SFU.

        This method automatically handles retry logic for transient errors
        like "server is full" and network issues.
        """
        logger.info("Connecting to SFU")
        # Fire-and-forget the coordinator WS connection so we don't block here
        if self._coordinator_task is None or self._coordinator_task.done():
            self._coordinator_task = asyncio.create_task(
                self._connect_coordinator_ws(), name="coordinator-ws-connect"
            )

            def _on_coordinator_task_done(task: asyncio.Task):
                try:
                    task.result()
                except asyncio.CancelledError:
                    pass
                except Exception:
                    logger.exception("Coordinator WS task failed")

            self._coordinator_task.add_done_callback(_on_coordinator_task_done)
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

    @telemetry.with_span("leave")
    async def leave(self):
        """Gracefully leave the call and close connections."""
        logger.info("Leaving the call")
        self.running = False
        self._stop_event.set()

        # Flush and stop stats reporter before cleaning up connections
        if self.stats_reporter:
            self.stats_reporter.flush()
            await self.stats_reporter.stop()
            self.stats_reporter = None

        await self._recording_manager.cleanup()
        await self._network_monitor.stop_monitoring()
        await self._peer_manager.close()
        if self._ws_client:
            self._ws_client.close()
            self._ws_client = None
        if self._coordinator_task and not self._coordinator_task.done():
            self._coordinator_task.cancel()
            try:
                await self._coordinator_task
            except asyncio.CancelledError:
                pass
            finally:
                self._coordinator_task = None

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
        with telemetry.start_as_current_span("rtc.add_tracks"):
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

    async def republish_tracks(self) -> None:
        """
        Use the participants info from the SFU to re-emit the "track_published"
        events for the already published tracks.

        It's needed because SFU does not send the events for the already present tracks when the
        agent joins after the user.
        """

        if not self._ws_client:
            return None

        participants = self.participants_state.get_participants()

        for participant in participants:
            # Skip the tracks belonging to this connection
            if participant.session_id == self.session_id:
                continue

            for track_type_int in participant.published_tracks:
                event = events_pb2.TrackPublished(
                    user_id=participant.user_id,
                    session_id=participant.session_id,
                    participant=participant,
                    type=track_type_int,
                )
                try:
                    # Update track subscriptions first
                    await self._subscription_manager.handle_track_published(event)
                    # Emit the event downstream
                    self.emit("track_published", event)
                except Exception:
                    logger.exception(
                        f"Failed to emit track_published event "
                        f"for the already published "
                        f"track {participant.user_id}:{participant.session_id}:{track_type_int}"
                    )

        return None
