import asyncio
import logging
import uuid
import functools
import re
from typing import Optional, Dict, Any

from getstream_rtc_core import (
    IceServer,
    RtcError,
    RtcSession,
    SfuCredentials,
    StatsOptions,
)

from getstream.common import telemetry
from getstream.utils import StreamAsyncIOEventEmitter
from getstream.video.rtc.coordinator.ws import StreamAPIWS
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.twirp_client_wrapper import SignalClient, Context

from getstream.video.async_call import Call
from getstream.video.rtc.connection_utils import (
    ConnectionState,
    SfuConnectionError,
    SfuJoinError,
    ConnectionOptions,
    join_call,
    watch_call,
)
from getstream.video.rtc.coordinator.backoff import exp_backoff
from getstream.video.rtc.network_monitor import NetworkMonitor
from getstream.video.rtc.recording import RecordingManager
from getstream.video.rtc.participants import ParticipantsState
from getstream.video.rtc.tracks import SubscriptionConfig, SubscriptionManager
from getstream.video.rtc.reconnection import ReconnectionManager, ReconnectionStrategy
from getstream.video.rtc.peer_connection import PeerConnectionManager, _WsStub
from getstream.video.rtc.models import JoinCallResponse
from getstream.video.rtc.tracer import Tracer
from getstream.video.rtc.stats_reporter import SfuStatsReporter
from getstream.video.rtc.sfu_bridge import dispatch_rust_event, participant_from_dict

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
        max_join_retries: int = 3,
        drain_video_frames: bool = True,
        **kwargs: Any,
    ):
        """
        Args:
            drain_video_frames: When True, attaches a MediaBlackhole to each
                incoming video track so unconsumed frames are drained
                automatically. This prevents unbounded queue growth in
                RTCRtpReceiver when no subscriber is consuming the track.
                The drain is stopped once a real subscriber is added via
                add_track_subscriber.
        """
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
        if max_join_retries < 0:
            raise ValueError("max_join_retries must be >= 0")
        self._max_join_retries: int = max_join_retries

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
        self._peer_manager: PeerConnectionManager = PeerConnectionManager(
            self, drain_video_frames=drain_video_frames
        )

        self.recording_manager = self._recording_manager
        self.participants_state = self._participants_state
        self.reconnector = self._reconnector

        self.twirp_signaling_client = None
        self.twirp_context: Optional[Context] = None
        self._coordinator_task: Optional[asyncio.Task] = None
        self._rtc_session: Optional[RtcSession] = None
        self._rtc_event_task: Optional[asyncio.Task] = None

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
        """ICE trickle is handled inside the Rust session."""
        logger.debug("Ignoring Python ICE trickle; Rust owns ICE")

    async def _on_subscriber_offer(self, event: events_pb2.SubscriberOffer):
        """Subscriber SDP is negotiated inside the Rust session."""
        logger.debug("Ignoring Python subscriber offer; Rust owns signaling")

    async def _on_signaling_connection_lost(self, reason: str) -> None:
        """Reconnect when the signaling WebSocket drops unexpectedly.

        The WebSocketClient itself only logs the error and stops; it has
        no reconnect of its own. This handler bridges that gap by routing
        the loss into the existing `ReconnectionManager`, so a transient
        TCP reset or a missed health check no longer means a dead session.
        """
        if not self.running:
            return
        logger.warning(f"Signaling WS lost; triggering reconnect: {reason}")
        try:
            await self._reconnector.reconnect(
                strategy=ReconnectionStrategy.FAST,
                reason=f"signaling ws lost: {reason}",
            )
        except Exception:
            logger.exception("Reconnect after signaling WS loss failed")

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
                stream = self.call.client.stream
                self._coordinator_ws_client = StreamAPIWS(
                    call=self.call,
                    user_details={"id": self.user_id},
                    user_token=None if stream.has_api_secret else stream.token,
                )
                self._coordinator_ws_client.on_wildcard("*", _log_event)
                self._coordinator_ws_client.on(
                    "custom", functools.partial(self.emit, "custom")
                )
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
        migrating_from_list: Optional[list] = None,
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
                last_failed = migrating_from_list[-1] if migrating_from_list else None
                join_response = await join_call(
                    self.call,
                    self.user_id,
                    "auto",
                    self.create,
                    self.local_sfu,
                    migrating_from=last_failed,
                    migrating_from_list=migrating_from_list,
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

        if self.join_response is None:
            raise ValueError("join_response is not set")
        credentials = self.join_response.credentials
        if not credentials.token or not credentials.server.ws_endpoint:
            raise ValueError("token and ws_url are required for WebSocket connection")

        try:
            with telemetry.start_as_current_span("sfu-rtc-session-join"):
                session = await self._join_rtc_session()
                rust_session_id = await session.session_id()
                if rust_session_id:
                    self.session_id = rust_session_id
                elif current_session_id:
                    self.session_id = current_session_id

                self._rtc_session = session
                self._peer_manager.attach_session(session)
                self._ws_client = _WsStub(edge_name=credentials.server.edge_name)
                self._rtc_event_task = asyncio.create_task(
                    self._pump_rtc_events(session), name="rtc-event-pump"
                )

            logger.debug(
                f"Rust RTC session joined via {credentials.server.ws_endpoint}"
            )
        except SfuJoinError:
            raise
        except RtcError as e:
            logger.exception(f"Failed to join SFU session: {e}")
            raise self._rtc_error_to_sfu_error(e) from e
        except Exception as e:
            logger.exception(
                f"Failed to connect WebSocket to {credentials.server.ws_endpoint}: {e}"
            )
            raise SfuConnectionError(f"WebSocket connection failed: {e}") from e

        # Step 5: Create SFU signaling client with tracer
        twirp_server_url = credentials.server.url
        self.twirp_signaling_client = SignalClient(
            address=twirp_server_url,
            tracer=self.tracer,
            sfu_id_fn=self.sfu_id,
        )
        self.twirp_context = Context(headers={"authorization": credentials.token})

        # Start stats reporter
        self.stats_reporter = SfuStatsReporter(self)
        self.stats_reporter.start()

        # Mark as connected
        self.running = True
        self.connection_state = ConnectionState.JOINED
        self._stop_event.clear()
        self._seed_roster_from_session()

        logger.info("Successfully connected to SFU")

    async def _join_rtc_session(self) -> RtcSession:
        if self.join_response is None or self.user_id is None:
            raise ValueError("join_response and user_id are required")
        stream = self.call.client.stream
        user_token = (
            stream.create_token(user_id=self.user_id)
            if stream.has_api_secret
            else stream.token
        )
        credentials = self.join_response.credentials
        ice_servers = []
        for server in credentials.ice_servers:
            urls = server.get("urls") or []
            if isinstance(urls, str):
                urls = [urls]
            ice_servers.append(
                IceServer(
                    urls=list(urls),
                    username=server.get("username"),
                    password=server.get("password") or server.get("credential"),
                )
            )
        stats = self.join_response.stats_options or {}
        own_capabilities = [
            str(capability)
            for capability in (self.join_response.own_capabilities or [])
        ]
        return await RtcSession.join(
            stream.api_key,
            user_token,
            self.call.call_type,
            self.call.id,
            self.user_id,
            SfuCredentials(
                edge_name=credentials.server.edge_name,
                url=credentials.server.url,
                ws_endpoint=credentials.server.ws_endpoint,
                token=credentials.token,
                ice_servers=ice_servers,
            ),
            stats_options=StatsOptions(
                reporting_interval_ms=int(stats.get("reporting_interval_ms") or 0),
                enable_rtc_stats=bool(stats.get("enable_rtc_stats")),
            ),
            own_capabilities=own_capabilities,
        )

    def _rtc_error_to_sfu_error(self, error: RtcError) -> Exception:
        message = str(error)
        match = re.search(r"code (\d+)", message)
        code = int(match.group(1)) if match else 0
        if code in {700, 600, 301} or "should_retry" in message:
            return SfuJoinError(message, error_code=code, should_retry=True)
        return SfuConnectionError(f"WebSocket connection failed: {message}")

    def _seed_roster_from_session(self) -> None:
        """Copy the Rust join roster into ParticipantsState (JS/Swift parity)."""
        session = self._rtc_session
        if session is None:
            return
        for data in session.participants():
            participant = participant_from_dict(data)
            if participant.session_id == self.session_id:
                continue
            if not participant.track_lookup_prefix:
                participant.track_lookup_prefix = (
                    participant.session_id or participant.user_id
                )
            if not participant.track_lookup_prefix:
                continue
            self.participants_state._add_participant(participant)

    async def _pump_rtc_events(self, session: RtcSession) -> None:
        try:
            async for event in session.events():
                try:
                    await dispatch_rust_event(self, event)
                except asyncio.CancelledError:
                    raise
                except Exception:
                    logger.exception("Failed to dispatch RTC event")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.debug("RTC event pump stopped", exc_info=True)

    @telemetry.with_span("connect")
    async def connect(self):
        """
        Connect to SFU.

        This method automatically handles retry logic for transient errors
        like "server is full" by requesting a different SFU from the
        coordinator.
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

        await self._connect_with_sfu_reassignment()

    async def _connect_with_sfu_reassignment(self) -> None:
        """Try connecting to SFU, reassigning to a different one on failure."""
        failed_sfus: list[str] = []

        # First attempt without delay
        attempt = 0
        try:
            await self._connect_internal()
            return
        except SfuJoinError as e:
            self._handle_join_failure(e, attempt, failed_sfus)
            if self._max_join_retries == 0:
                raise

        # Retries with exponential backoff, requesting a different SFU
        async for delay in exp_backoff(max_retries=self._max_join_retries, base=0.5):
            attempt += 1
            logger.info(f"Retrying in {delay}s with different SFU...")
            await asyncio.sleep(delay)
            try:
                await self._connect_internal(
                    migrating_from_list=failed_sfus if failed_sfus else None,
                )
                return
            except SfuJoinError as e:
                self._handle_join_failure(e, attempt, failed_sfus)
                if attempt >= self._max_join_retries:
                    raise

    def _handle_join_failure(
        self, error: SfuJoinError, attempt: int, failed_sfus: list[str]
    ) -> None:
        """Track a failed SFU and clean up partial connection state."""
        if self.join_response and self.join_response.credentials:
            edge = self.join_response.credentials.server.edge_name
            if edge and edge not in failed_sfus:
                failed_sfus.append(edge)
        logger.warning(
            f"SFU join failed (attempt {attempt + 1}/{1 + self._max_join_retries}, "
            f"code={error.error_code}). Failed SFUs: {failed_sfus}"
        )
        if self._ws_client:
            self._ws_client.close()
            self._ws_client = None
        session = self._rtc_session
        self._rtc_session = None
        if session is not None:
            asyncio.create_task(session.leave())
        self.connection_state = ConnectionState.IDLE

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
        if self._rtc_event_task and not self._rtc_event_task.done():
            self._rtc_event_task.cancel()
            try:
                await self._rtc_event_task
            except asyncio.CancelledError:
                pass
            self._rtc_event_task = None
        session = self._rtc_session
        self._rtc_session = None
        if session is not None:
            try:
                await session.leave()
            except Exception:
                logger.debug("Error leaving RTC session", exc_info=True)
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
