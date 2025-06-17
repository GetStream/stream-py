import asyncio
import json
import logging
import time
import uuid
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import aioice
import aiortc
from aiortc.contrib.media import MediaRelay
from pyee.asyncio import AsyncIOEventEmitter
from tenacity import before_sleep_log, retry, stop_after_attempt, wait_random_exponential
from twirp import context

from getstream.video.call import Call
from getstream.video.rtc.connection_utils import (
    ConnectionState,
    SfuConnectionError, 
    create_audio_track_info,
    is_retryable,
    prepare_video_track_info, 
)
from getstream.video.rtc.coordinator import join_call_coordinator_request
from getstream.video.rtc.location_discovery import HTTPHintLocationDiscovery
from getstream.video.rtc.network_monitor import NetworkMonitor
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import TrackInfo
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.pc import PublisherPeerConnection, SubscriberPeerConnection
from getstream.video.rtc.recording import RecordingManager, RecordingType
from getstream.video.rtc.signaling import SignalingError, WebSocketClient
from getstream.video.rtc.track_util import fix_sdp_msid_semantic, parse_track_stream_mapping
from getstream.video.rtc.twirp_client_wrapper import SignalClient, SfuRpcError

logger = logging.getLogger(__name__)


@dataclass
class _ReconnectionStrategy:
    """Reconnection strategy configuration."""
    
    UNSPECIFIED = "unspecified"
    DISCONNECT = "disconnect"
    FAST = "fast"
    REJOIN = "rejoin"
    MIGRATE = "migrate"


# Internal retry configuration - not exposed to users
_DEFAULT_MAX_ATTEMPTS = 5
_DEFAULT_MIN_WAIT = 1.0
_DEFAULT_MAX_WAIT = 30.0
_DISCONNECTION_TIMEOUT_SECONDS = 60


@dataclass
class _ConnectionOptions:
    """Options for the connection process."""
    join_response: Optional[Any] = None
    region: Optional[str] = None
    fast_reconnect: bool = False
    migrating_from: Optional[str] = None
    previous_session_id: Optional[str] = None


@dataclass
class _ReconnectionInfo:
    """Manages reconnection-related information and state."""
    published_tracks: OrderedDict[str, Dict[str, Any]] = None
    strategy: str = _ReconnectionStrategy.UNSPECIFIED
    reason: str = ""
    attempts: int = 0
    last_offline_timestamp: float = 0.0
    
    def __post_init__(self):
        if self.published_tracks is None:
            self.published_tracks = OrderedDict()
    
    def reset_state(self):
        """Reset reconnection state after successful connection."""
        self.strategy = _ReconnectionStrategy.UNSPECIFIED
        self.reason = ""
        self.attempts = 0
    
    def add_published_track(self, track_id: str, track: Any, track_info: Any, media_relay: MediaRelay = None):
        """Add a published track maintaining order."""
        self.published_tracks[track_id] = {
            'track': track,
            'info': track_info,
            'track_type': track.kind,
            'media_relay': media_relay
        }
    
    def remove_published_track(self, track_id: str):
        """Remove a published track."""
        if track_id in self.published_tracks:
            del self.published_tracks[track_id]
    
    def get_published_track_count(self) -> int:
        """Get total number of published tracks."""
        return len(self.published_tracks)


class ParticipantsState(AsyncIOEventEmitter):
    def __init__(self):
        super().__init__()
        self._participant_by_prefix = {}
        self._track_stream_mapping = {}

    def get_user_from_track_id(self, track_id: str) -> Optional[models_pb2.Participant]:
        stream_id = self._track_stream_mapping.get(track_id)
        if stream_id:
            prefix = stream_id.split(":")[0]
            return self._participant_by_prefix.get(prefix)
        return None

    def get_stream_id_from_track_id(self, track_id: str) -> Optional[str]:
        return self._track_stream_mapping.get(track_id)

    def set_track_stream_mapping(self, mapping: dict):
        logger.debug(f"Setting track stream mapping: {mapping}")
        self._track_stream_mapping = mapping

    def add_participant(self, participant: models_pb2.Participant):
        self._participant_by_prefix[participant.track_lookup_prefix] = participant

    def remove_participant(self, participant: models_pb2.Participant):
        if participant.track_lookup_prefix in self._participant_by_prefix:
            del self._participant_by_prefix[participant.track_lookup_prefix]

    async def _on_participant_joined(self, event: events_pb2.ParticipantJoined):
        self.add_participant(event.participant)
        self.emit("participant_joined", event.participant)

    async def _on_participant_left(self, event: events_pb2.ParticipantLeft):
        self.remove_participant(event.participant)
        self.emit("participant_left", event.participant)


class ConnectionManager(AsyncIOEventEmitter):
    def __init__(
        self,
        call: Call,
        user_id: str = None,
        create: bool = True,
        **kwargs,
    ):
        super().__init__()

        self.call = call
        self.user_id = user_id
        self.create = create
        self.kwargs = kwargs
        self.running = False
        
        self.session_id = str(uuid.uuid4())
        self._connection_state = ConnectionState.IDLE
        self._stop_event = asyncio.Event()
        
        self._connection_options = _ConnectionOptions()
        self.join_response = None
        self.ws_client = None
        self.twirp_signaling_client = None
        self.twirp_context = None
        self.subscriber_pc: Optional[SubscriberPeerConnection] = None
        self.publisher_pc: Optional[PublisherPeerConnection] = None
        
        self.participants_state = ParticipantsState()
        self.recording_manager = RecordingManager()
        self._network_monitor = NetworkMonitor()
        self.publisher_negotiation_lock = asyncio.Lock()
        self.subscriber_negotiation_lock = asyncio.Lock()
        self._reconnection_info = _ReconnectionInfo()
        self._reconnect_lock = asyncio.Lock()
        self._network_available_event: Optional[asyncio.Event] = None

        self._fast_reconnect_deadline_seconds = 10
        
        # Local SFU flag for development
        self.local_sfu = False

    @property
    def connection_state(self) -> ConnectionState:
        """Get the current connection state."""
        return self._connection_state
    
    @connection_state.setter
    def connection_state(self, value: ConnectionState):
        """Set the connection state."""
        if value != self._connection_state:
            logger.debug(f"Connection state changed from {self._connection_state.value} to {value.value}")
            self._connection_state = value

    @staticmethod
    def _discover_location() -> str:
        """Discover the optimal location for connection."""
        try:
            discovery = HTTPHintLocationDiscovery(logger=logger)
            location = discovery.discover()
            logger.info(f"Discovered location: {location}")
            return location
        except Exception as e:
            logger.warning(f"Failed to discover location: {e}, using default FRA")
            return "FRA"

    @staticmethod
    async def _join_call_coordinator(
        call,
        user_id: str,
        location: str,
        create: bool,
        local_sfu: bool,
        **kwargs,
    ):
        """Join call via coordinator API."""
        try:
            join_response = await join_call_coordinator_request(
                call, user_id, location=location, 
                create=create, **kwargs
            )
            if local_sfu:
                join_response.data.credentials.server.url = "http://127.0.0.1:3031/twirp"

            logger.debug(f"Received SFU credentials: {join_response.data.credentials.server.url}")
                
            return join_response
            
        except Exception as e:
            logger.error(f"Failed to join call via coordinator: {e}")
            raise SfuConnectionError(f"Failed to join call: {e}")

    @staticmethod
    async def _connect_websocket(
        token: str,
        ws_url: str,
        session_id: str,
        connection_options: Optional[_ConnectionOptions] = None,
    ):
        """Connect to SFU via WebSocket."""
        try:
            # Create JoinRequest for WebSocket connection
            join_request = events_pb2.JoinRequest()
            join_request.token = token
            join_request.session_id = session_id
            
            # Apply reconnect options if provided
            if connection_options:
                if connection_options.fast_reconnect:
                    join_request.fast_reconnect = True
                if connection_options.migrating_from:
                    join_request.reconnect_details.migrating_from = connection_options.migrating_from
                if connection_options.previous_session_id:
                    join_request.reconnect_details.previous_session_id = connection_options.previous_session_id

            # Create WebSocket client
            ws_client = WebSocketClient(ws_url, join_request, asyncio.get_running_loop())

            # Connect to the WebSocket server and wait for the first message
            logger.info(f"Establishing WebSocket connection to {ws_url}")
            sfu_event = await ws_client.connect()
            
            logger.debug("WebSocket connection established successfully")
            return ws_client, sfu_event
            
        except SignalingError as e:
            logger.error(f"Failed to connect to SFU WebSocket: {e}")
            # Clean up websocket client on error (if it exists)
            if 'ws_client' in locals():
                ws_client.close()
            raise  # Re-raise SignalingError for retry logic
        except Exception as e:
            logger.error(f"Unexpected error connecting to SFU: {e}")
            # Clean up websocket client on error (if it exists)
            if 'ws_client' in locals():
                ws_client.close()
            raise SfuConnectionError(f"Unexpected error connecting to SFU: {e}")

    @staticmethod
    def _setup_signaling_client(token: str, server_url: str):
        """Setup signaling client for SFU communication."""
        try:
            # Setup signaling client
            twirp_client = SignalClient(address=server_url)
            # Prepare context headers with authentication
            headers = {"authorization": token}
            twirp_context = context.Context(headers=headers)
            
            logger.info("Signaling client setup completed")
            return twirp_client, twirp_context
            
        except Exception as e:
            logger.error(f"Failed to setup signaling client: {e}")
            raise SfuConnectionError(f"Failed to setup signaling client: {e}")

    async def _connect_internal(
        self,
        region: Optional[str] = None,
        ws_url: Optional[str] = None,
        token: Optional[str] = None,
        ws_client: Optional[WebSocketClient] = None,
        session_id: Optional[str] = None,
        signaling_client: Optional[SignalClient] = None,
        signaling_context: Optional[context.Context] = None,
    ) -> None:
        """
        Internal connection method that handles the core connection logic.
        
        Args:
            region: Optional region to connect to
            ws_url: Optional WebSocket URL to connect to
            token: Optional authentication token
            ws_client: Optional existing WebSocket client
            session_id: Optional session ID
            signaling_client: Optional existing signaling client
            signaling_context: Optional existing signaling context
            
        Raises:
            SfuConnectionError: If connection fails
        """        
        # Validate that signaling_client and signaling_context are provided together
        if (signaling_client is None) != (signaling_context is None):
            raise ValueError("signaling_client and signaling_context must be provided together or both be None")
        
        self.connection_state = ConnectionState.JOINING
        
        # Step 1: Determine region
        location = region
        if not location:
            if self._connection_options.region:
                location = self._connection_options.region
                logger.info(f"Using provided region: {location}")
            else:
                location = self._discover_location()
        
        # Step 2: Get join response
        if self._connection_options.join_response:
            join_response = self._connection_options.join_response
            logger.info("Using provided join_response, skipping coordinator call")
        else:
            join_response = await self._join_call_coordinator(
                self.call, self.user_id, location, self.create, self.local_sfu, **self.kwargs
            )

        # Step 3: Setup WebSocket connection
        if not token:
            token = join_response.data.credentials.token
        if not ws_url:
            if self.local_sfu:
                ws_url = "ws://127.0.0.1:3031/ws"
                logger.info(f"Adjusted SFU ws url to {ws_url}")
                join_response.data.credentials.server.ws_endpoint = ws_url
            else:
                ws_url = join_response.data.credentials.server.ws_endpoint
        
        # Use provided session_id or current one
        current_session_id = session_id or self.session_id
        
        # Connect to WebSocket if not provided
        if not ws_client:
            try:
                self.ws_client, sfu_event = await self._connect_websocket(token, ws_url, current_session_id, self._connection_options)
                
                # Populate participants state with existing participants
                if hasattr(sfu_event, "join_response"):
                    if hasattr(sfu_event.join_response, "call_state"):
                        for participant in sfu_event.join_response.call_state.participants:
                            self.participants_state.add_participant(participant)
                    if hasattr(sfu_event.join_response, "fast_reconnect_deadline_seconds"):
                        self._fast_reconnect_deadline_seconds = sfu_event.join_response.fast_reconnect_deadline_seconds
                        
                logger.debug(f"WebSocket connected successfully to {ws_url}")
            except Exception as e:
                logger.error(f"Failed to connect WebSocket to {ws_url}: {e}")
                raise SfuConnectionError(f"WebSocket connection failed: {e}")
        else:
            self.ws_client = ws_client
            logger.debug("Using provided WebSocket client")
        
        # Register event handlers (only if not already registered)
        if not hasattr(self.ws_client, '_handlers_registered'):
            self._register_websocket_event_handlers()
            self.ws_client._handlers_registered = True
        
        # Set the join_response for use by other components
        self.join_response = join_response
        # Update connection options for future use
        self._connection_options.join_response = join_response
        self._connection_options.region = location
        self._connection_options.previous_session_id = current_session_id
        
        # Step 4: Setup signaling client
        if not signaling_client or not signaling_context:
            server_url = join_response.data.credentials.server.url
            self.twirp_signaling_client, self.twirp_context = self._setup_signaling_client(token, server_url)
        else:
            self.twirp_signaling_client = signaling_client
            self.twirp_context = signaling_context
        
        # Setup subscriber peer connection (only if not already exists or is closed)
        if not self.subscriber_pc or self.subscriber_pc.connectionState in ["closed", "failed"]:
            self.subscriber_pc = SubscriberPeerConnection(connection=self)
            
            @self.subscriber_pc.on("audio")
            async def on_audio(pcm_data, user):
                user_id = getattr(user, 'user_id', getattr(user, 'id', str(user) if user else "unknown_user"))
                self.emit("audio", pcm_data, user)
                self.recording_manager.record_audio_data(pcm_data, user_id)
            
            logger.debug("Created new subscriber peer connection")
        else:
            logger.debug("Reusing existing subscriber peer connection")
        
        # Mark as connected
        self.running = True
        self.connection_state = ConnectionState.JOINED
        self._stop_event.clear()
        
        logger.info("Successfully connected to SFU")

    async def _cleanup_connections(
        self,
        ws_client: WebSocketClient,
        publisher_pc: PublisherPeerConnection,
        subscriber_pc: SubscriberPeerConnection,
    ):
        cleanup_tasks = []
        
        # Close WebSocket client (synchronous)
        if ws_client:
            try:
                ws_client.close()
            except Exception as e:
                logger.debug(f"Error closing WebSocket client: {e}")
        
        # Close peer connections (asynchronous)
        if publisher_pc:
            cleanup_tasks.append(publisher_pc.close())
        if subscriber_pc:
            cleanup_tasks.append(subscriber_pc.close())
        
        # Run peer connection cleanup concurrently
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logger.debug(f"Error during peer connection cleanup: {e}")

    @retry(
        stop=stop_after_attempt(_DEFAULT_MAX_ATTEMPTS),
        wait=wait_random_exponential(multiplier=_DEFAULT_MIN_WAIT, max=_DEFAULT_MAX_WAIT),
        retry=is_retryable,
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True
    )
    async def connect(self):
        """
        Connect to SFU.
        
        This method automatically handles retry logic for transient errors
        like "server is full" and network issues.
        """
        logger.info("Connecting to SFU")
        await self._connect_internal()

    def _register_websocket_event_handlers(self):
        """Register all WebSocket event handlers on the WebSocket client."""
        if not self.ws_client:
            logger.warning("Cannot register event handlers: WebSocket client is None")
            return
            
        self.ws_client.on_event(
            "participant_joined", self.participants_state._on_participant_joined
        )
        self.ws_client.on_event("ice_trickle", self._on_ice_trickle)
        self.ws_client.on_event("subscriber_offer", self._on_subscriber_offer)
        self.ws_client.on_event("participant_left", self._on_participant_left)
        
        # Convert lambda functions to async functions
        async def handle_error_event(event):
            logger.warning(f"Received SFU error event: {event}")
            self.emit('sfu_error', {
                'reconnect_strategy': getattr(event, 'reconnect_strategy', _ReconnectionStrategy.UNSPECIFIED),
                'message': getattr(event, 'message', 'SFU Error'),
                'event': event
            })
        
        async def handle_go_away_event(event):
            logger.info(f"Received go away event: {event}")
            self.emit('go_away', {'event': event})
        
        async def handle_wildcard_debug_event(event):
            logger.debug(
                f"WebSocket event - Type: {getattr(event, 'type', type(event).__name__)}, Event: {event}"
            )
        
        self.ws_client.on_event("error", handle_error_event)
        self.ws_client.on_event("go_away", handle_go_away_event)
        self.ws_client.on_event("*", handle_wildcard_debug_event)
        
        logger.debug("WebSocket event handlers registered")

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

        await self.recording_manager.cleanup()

        # Close all connections
        cleanup_tasks = []
        
        if self.ws_client:
            self.ws_client.close()
            self.ws_client = None
            
        if self.subscriber_pc:
            cleanup_tasks.append(self.subscriber_pc.close())
            self.subscriber_pc = None
        if self.publisher_pc:
            cleanup_tasks.append(self.publisher_pc.close())
            self.publisher_pc = None
            
        # Run peer connection cleanup concurrently
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

        await self._network_monitor.stop_monitoring()
        self.connection_state = ConnectionState.LEFT
        
        logger.info("Call left and connections closed")

    async def __aenter__(self):
        """Async context manager entry."""
        # Register reconnection handlers directly
        self._register_reconnection_handlers()
        
        # Register network change handlers from NetworkMonitor
        @self._network_monitor.on('network_changed')
        def on_network_changed(event_data):
            self._on_network_changed(event_data)
        
        @self._network_monitor.on('network_online') 
        def on_network_online(event_data):
            logger.debug("Network came online")
            
        @self._network_monitor.on('network_offline')
        def on_network_offline(event_data): 
            logger.debug("Network went offline")
        
        # Connect with retry
        await self.connect()
        
        # Start network monitoring
        await self._network_monitor.start_monitoring()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.leave()

    def _on_network_changed(self, event_data: dict):
        """Handle network change events with debug logging."""
        online = event_data.get('online', True)
        status = "online" if online else "offline"
        logger.debug(f"Network status changed to {status}")
        
        # Emit the event for other components that might be listening
        self.emit('network_changed', event_data)

    # Track Management Methods
    async def add_tracks(self, audio: Optional[aiortc.mediastreams.MediaStreamTrack] = None,
                        video: Optional[aiortc.mediastreams.MediaStreamTrack] = None):
        """Add multiple audio and video tracks in a single negotiation."""
        if not self.running:
            logger.error("Connection manager not running. Call connect() first.")
            return

        if not audio and not video:
            logger.warning("No tracks provided to add_tracks")
            return

        # Store original tracks for reconnection
        original_audio = audio
        original_video = video

        track_infos = []
        relayed_audio = None
        relayed_video = None
        audio_relay = None
        video_relay = None
        
        if audio:
            # Create individual MediaRelay for this audio track
            audio_relay = MediaRelay()
            relayed_audio = audio_relay.subscribe(audio)
            track_infos.append(create_audio_track_info(relayed_audio))
        if video:
            # Create individual MediaRelay for this video track
            video_relay = MediaRelay()
            relayed_video = video_relay.subscribe(video)
            video_info, relayed_video = await prepare_video_track_info(relayed_video)
            track_infos.append(video_info)

        async with self.publisher_negotiation_lock:
            logger.info(f"Adding tracks: {len(track_infos)} tracks")

            if self.publisher_pc is None:
                self.publisher_pc = PublisherPeerConnection(manager=self)

            if relayed_audio:
                self.publisher_pc.addTrack(relayed_audio)
                logger.info(f"Added relayed audio track {relayed_audio.id}")
            if relayed_video:
                self.publisher_pc.addTrack(relayed_video)
                logger.info(f"Added relayed video track {relayed_video.id}")

            offer = await self.publisher_pc.createOffer()
            await self.publisher_pc.setLocalDescription(offer)

            try:
                response = await self.twirp_signaling_client.SetPublisher(
                    ctx=self.twirp_context,
                    request=signal_pb2.SetPublisherRequest(
                        session_id=self.session_id,
                        sdp=self.publisher_pc.localDescription.sdp,
                        tracks=track_infos,
                    ),
                    server_path_prefix="",
                )
                await self.publisher_pc.handle_answer(response)
                await self.publisher_pc.wait_for_connected()
            except SfuRpcError as e:
                logger.error(f"Failed to set publisher: {e}")
                # await self.publisher_pc.close()
                # self.publisher_pc = None
                raise SfuConnectionError(f"Failed to set publisher: {e}")

        # Register ORIGINAL tracks and their MediaRelay instances for reconnection
        track_info_index = 0
        if original_audio:
            # Store original track info with its MediaRelay for reconnection
            self._reconnection_info.add_published_track(original_audio.id, original_audio, track_infos[track_info_index], audio_relay)
            track_info_index += 1
        if original_video:
            # Store original track info with its MediaRelay for reconnection
            self._reconnection_info.add_published_track(original_video.id, original_video, track_infos[track_info_index], video_relay)

    async def addTrack(self, track: aiortc.mediastreams.MediaStreamTrack, track_info: Optional[TrackInfo] = None):
        """Add a single track (backward compatibility)."""
        if track.kind == "video":
            await self.add_tracks(video=track)
        else:
            await self.add_tracks(audio=track)

    async def start_recording(self, recording_types: List[RecordingType], 
                            user_ids: Optional[List[str]] = None, output_dir: str = "recordings"):
        logger.info("Starting recording")
        await self.recording_manager.start_recording(recording_types, user_ids, output_dir)

    async def stop_recording(self, recording_types: Optional[List[RecordingType]] = None,
                           user_ids: Optional[List[str]] = None):
        logger.info("Stopping recording")
        await self.recording_manager.stop_recording(recording_types, user_ids)

    @property
    def is_recording(self) -> bool:
        return self.recording_manager.is_recording

    def get_recording_status(self) -> dict:
        return self.recording_manager.get_recording_status()
    
    async def _reconnect(self, strategy: str, reason: str):
        """
        Main reconnection orchestrator.
        
        Args:
            strategy: The reconnection strategy to use
            reason: Human-readable reason for the reconnection
        """
        async with self._reconnect_lock:
            # Check if already in a reconnection state
            if self.connection_state in [
                ConnectionState.RECONNECTING,
                ConnectionState.MIGRATING,
                ConnectionState.RECONNECTING_FAILED
            ]:
                logger.debug(
                    "Reconnection already in progress", 
                    extra={"current_state": self.connection_state.value}
                )
                return

            reconnect_start_time = time.time()
            self._reconnection_info.strategy = strategy
            self._reconnection_info.reason = reason
            
            logger.info(
                "Starting reconnection", 
                extra={"strategy": strategy, "reason": reason}
            )

            try:
                await self._execute_reconnection_loop(reconnect_start_time)
            except Exception as e:
                logger.error("Reconnection orchestrator failed", exc_info=e)
                self.connection_state = ConnectionState.RECONNECTING_FAILED
                self.emit('reconnection_failed', {'reason': str(e)})

    async def _execute_reconnection_loop(self, reconnect_start_time: float):
        """Execute the main reconnection retry loop."""
        while True:
            # Check disconnection timeout
            timeout = _DISCONNECTION_TIMEOUT_SECONDS
            if 0 < timeout < (time.time() - reconnect_start_time):
                logger.warning("Stopping reconnection attempts after reaching disconnection timeout")
                self.connection_state = ConnectionState.RECONNECTING_FAILED
                self.emit('reconnection_failed', {'reason': "Disconnection timeout exceeded"})
                return

            # Increment attempts (except for FAST strategy)
            if self._reconnection_info.strategy != _ReconnectionStrategy.FAST:
                self._reconnection_info.attempts += 1

            try:
                # Wait for network availability
                if self._network_available_event:
                    logger.debug("Waiting for network availability")
                    await self._network_available_event.wait()

                logger.info(f"Executing reconnection with strategy {self._reconnection_info.strategy}")

                # Execute strategy-specific reconnection
                await self._execute_reconnection_strategy()
                
                # If we reach here, reconnection was successful
                duration = time.time() - reconnect_start_time
                self.emit('reconnection_success', {
                    'strategy': self._reconnection_info.strategy,
                    'duration': duration
                })
                # Reset reconnection state after successful connection
                self._reconnection_info.reset_state()
                self._network_available_event = None
                logger.debug("Reconnection state reset")
                break

            except Exception as error:
                if self.connection_state == ConnectionState.OFFLINE:
                    logger.debug("Can't reconnect while offline, stopping attempts")
                    break

                logger.warning(
                    f"Reconnection failed, attempting with REJOIN: {error}",
                    exc_info=error
                )
                await asyncio.sleep(0.5)  # Brief delay before retry
                self._reconnection_info.strategy = _ReconnectionStrategy.REJOIN

            # Check if we should exit the loop
            if self.connection_state in [
                ConnectionState.JOINED,
                ConnectionState.RECONNECTING_FAILED,
                ConnectionState.LEFT
            ]:
                break

        logger.info("Reconnection flow finished")

    async def _execute_reconnection_strategy(self):
        """Execute the strategy-specific reconnection logic."""
        strategy = self._reconnection_info.strategy
        
        if strategy == _ReconnectionStrategy.FAST:
            await self._reconnect_fast()
        elif strategy == _ReconnectionStrategy.REJOIN:
            await self._reconnect_rejoin()
        elif strategy == _ReconnectionStrategy.MIGRATE:
            await self._reconnect_migrate()
        elif strategy == _ReconnectionStrategy.DISCONNECT:
            await self.leave()
            return
        else:
            logger.debug(f"No-op strategy {strategy}")

    async def _reconnect_fast(self):
        """Fast reconnection strategy - minimal disruption."""
        logger.info("Executing FAST reconnection strategy")
        self.connection_state = ConnectionState.RECONNECTING
        
        try:
            if self.ws_client and self.ws_client.running:
                # Simple ICE restart if WebSocket is healthy
                if self.publisher_pc:
                    await self.publisher_pc.restartIce()
                logger.info("ICE restart completed for healthy WebSocket")
            else:
                # Full reconnection needed
                self._connection_options.fast_reconnect = True
                previous_ws_client = self.ws_client
                
                # Use _connect_internal with existing connection info
                await self._connect_internal(
                    region=self._connection_options.region,
                    token=self.join_response.data.credentials.token if self.join_response else None,
                    session_id=self.session_id
                )
                
                # Clean up old WebSocket after successful connection
                if previous_ws_client:
                    previous_ws_client.close()
                
                # Restore published tracks with stored MediaRelay instances
                await self._restore_published_tracks()
            
            self.connection_state = ConnectionState.JOINED
            logger.info("FAST reconnection completed successfully")
        except Exception as e:
            logger.error("FAST reconnection failed", exc_info=e)
            self.connection_state = ConnectionState.RECONNECTING_FAILED
            raise

    async def _reconnect_rejoin(self):
        """Rejoin reconnection strategy - full reconnection."""
        logger.info("Executing REJOIN reconnection strategy")
        self.connection_state = ConnectionState.RECONNECTING
        
        # Store references to old connections for cleanup
        old_publisher = self.publisher_pc
        old_subscriber = self.subscriber_pc
        old_ws_client = self.ws_client
        
        # Clear the old connections so new ones can be created
        self.publisher_pc = None
        self.subscriber_pc = None
        self.ws_client = None
        
        try:
            # Close old connections efficiently
            await self._cleanup_connections(old_ws_client, old_publisher, old_subscriber)
            
            # Use _connect_internal for fresh connection
            await self._connect_internal()
            
            # Restore published tracks after successful reconnection
            await self._restore_published_tracks()
            
            logger.info("REJOIN reconnection completed successfully")
        except Exception as error:
            logger.error("REJOIN reconnection failed", exc_info=error)
            # Ensure connection state is properly set on failure
            self.connection_state = ConnectionState.RECONNECTING_FAILED
            raise

    async def _reconnect_migrate(self):
        """Migration reconnection strategy - server-coordinated."""
        logger.info("Executing MIGRATE reconnection strategy")
        
        current_ws_client = self.ws_client
        current_publisher = self.publisher_pc
        current_subscriber = self.subscriber_pc

        self.connection_state = ConnectionState.MIGRATING

        if current_publisher and hasattr(current_publisher, 'removeListener'):
            current_publisher.removeListener('connectionstatechange')
        if current_subscriber and hasattr(current_subscriber, 'removeListener'):
            current_subscriber.removeListener('connectionstatechange')

        try:
            migrating_from = getattr(current_ws_client, 'edge_name', None)
            
            # Set migration options for connection
            if hasattr(self, '_connection_options'):
                self._connection_options.fast_reconnect = False
                self._connection_options.migrating_from = migrating_from
                self._connection_options.previous_session_id = self.session_id if migrating_from else None

            # Use _connect_internal for migration
            await self._connect_internal(
                region=self._connection_options.region,
                session_id=self.session_id
            )
            
            await self._restore_published_tracks()

            self.connection_state = ConnectionState.JOINED
            logger.info("MIGRATE reconnection completed successfully")

        finally:
            # Clean up old connections
            await self._cleanup_connections(current_ws_client, current_publisher, current_subscriber)

    async def _restore_published_tracks(self):
        """Restore published tracks using their stored MediaRelay instances."""
        track_ids = list(self._reconnection_info.published_tracks.keys())
        logger.info(f"Restoring {len(track_ids)} published tracks with MediaRelay - Track IDs: {track_ids}")
        
        # Collect all tracks to restore
        audio_tracks = []
        video_tracks = []
        
        for track_id, track_info in self._reconnection_info.published_tracks.items():
            original_track = track_info['track']  # Original track
            
            # Group tracks by type
            if original_track.kind == 'audio':
                audio_tracks.append(original_track)
            elif original_track.kind == 'video':
                video_tracks.append(original_track)
        
        # Restore tracks using the add_tracks method
        # This ensures proper MediaRelay usage and peer connection management
        try:
            # Restore first audio and video track together if available
            if audio_tracks or video_tracks:
                await self.add_tracks(
                    audio=audio_tracks[0] if audio_tracks else None,
                    video=video_tracks[0] if video_tracks else None
                )
                logger.info("Restored primary audio/video tracks")
            
            # Restore additional audio tracks individually
            for i, track in enumerate(audio_tracks[1:], 1):
                await self.add_tracks(audio=track)
                logger.info(f"Restored additional audio track {i}: {track.id}")
            
            # Restore additional video tracks individually  
            for i, track in enumerate(video_tracks[1:], 1):
                await self.add_tracks(video=track)
                logger.info(f"Restored additional video track {i}: {track.id}")
                
            logger.info(f"Successfully restored all {len(track_ids)} tracks using stored MediaRelay instances")
            
        except Exception as e:
            logger.error("Failed to restore published tracks", exc_info=e)
            raise

    def _register_reconnection_handlers(self):
        """Register event handlers for reconnection triggers."""
        
        @self.on('network_changed')
        async def handle_network_change(event_data):
            logger.info(f"Received network change: {event_data}")
            online = event_data.get('online', True)

            if not online:
                logger.debug("Going offline")
                if self.connection_state not in [ConnectionState.JOINED]:
                    return

                self._reconnection_info.last_offline_timestamp = time.time()
                network_event = asyncio.Event()
                self._network_available_event = network_event
                self.connection_state = ConnectionState.OFFLINE
            else:
                logger.debug("Going online")

                if self._reconnection_info.last_offline_timestamp:
                    offline_duration = time.time() - self._reconnection_info.last_offline_timestamp
                    strategy = (_ReconnectionStrategy.FAST
                              if offline_duration <= self._fast_reconnect_deadline_seconds
                              else _ReconnectionStrategy.REJOIN)
                else:
                    strategy = _ReconnectionStrategy.REJOIN

                if self._network_available_event:
                    self._network_available_event.set()
                    self._network_available_event = None

                asyncio.create_task(
                    self._reconnect(strategy, "Going online")
                )
        
        @self.on('go_away')
        async def handle_go_away(event_data):
            asyncio.create_task(
                self._reconnect(_ReconnectionStrategy.MIGRATE, "Server requested migration")
            )
            
        @self.on('sfu_error')
        async def handle_sfu_error(event_data):
            strategy = event_data.get('reconnect_strategy', _ReconnectionStrategy.UNSPECIFIED)
            if strategy == _ReconnectionStrategy.UNSPECIFIED:
                return
            elif strategy == _ReconnectionStrategy.DISCONNECT:
                await self.leave()
            else:
                asyncio.create_task(
                    self._reconnect(strategy, event_data.get('message', 'SFU Error'))
                )
        
        logger.debug("Reconnection event handlers registered")

    async def _on_subscriber_offer(self, event):
        """Handle subscriber offer from SFU."""
        logger.debug("Subscriber offer received")

        async with self.subscriber_negotiation_lock:
            try:
                fixed_sdp = fix_sdp_msid_semantic(event.sdp)
                self.participants_state.set_track_stream_mapping(parse_track_stream_mapping(fixed_sdp))
                
                remote_description = aiortc.RTCSessionDescription(type="offer", sdp=fixed_sdp)
                await self.subscriber_pc.setRemoteDescription(remote_description)
                
                answer = await self.subscriber_pc.createAnswer()
                await self.subscriber_pc.setLocalDescription(answer)
                
                try:
                    await self.twirp_signaling_client.SendAnswer(
                        ctx=self.twirp_context,
                        request=signal_pb2.SendAnswerRequest(
                            peer_type=models_pb2.PEER_TYPE_SUBSCRIBER,
                            sdp=self.subscriber_pc.localDescription.sdp,
                            session_id=self.session_id,
                        ),
                        server_path_prefix="",
                    )
                    logger.debug("Subscriber answer sent successfully")
                except SfuRpcError as e:
                    if e.message != "participant not found":
                        logger.error(f"Failed to send subscriber answer: {e}")
            except Exception as e:
                logger.error(f"Error handling subscriber offer: {e}")

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

            if event.peer_type == models_pb2.PEER_TYPE_SUBSCRIBER and self.subscriber_pc:
                await self.subscriber_pc.addIceCandidate(candidate)
            elif self.publisher_pc:
                await self.publisher_pc.addIceCandidate(candidate)
        except Exception as e:
            logger.debug(f"Error handling ICE trickle: {e}")

    async def _on_participant_left(self, event):
        """Handle participant leaving."""
        try:
            await self.participants_state._on_participant_left(event)
            if hasattr(event, 'participant') and hasattr(event.participant, 'user_id'):
                await self.recording_manager.on_user_left(event.participant.user_id)
        except Exception as e:
            logger.error(f"Error handling participant left: {e}")

