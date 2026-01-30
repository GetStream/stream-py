"""
Manages WebRTC peer connections for video streaming.
"""

import asyncio
import logging
from typing import Optional

import aiortc
import aiortc.sdp
from aiortc.contrib.media import MediaRelay

from getstream.common import telemetry
from getstream.video.rtc.connection_utils import (
    create_audio_track_info,
    prepare_video_track_info,
)
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc import signal_pb2
from getstream.video.rtc.track_util import patch_sdp_offer
from getstream.video.rtc.twirp_client_wrapper import SfuRpcError
from getstream.video.rtc.pc import PublisherPeerConnection, SubscriberPeerConnection
from getstream.video.rtc.stats_reporter import DEFAULT_STATS_INTERVAL_MS
from getstream.video.rtc.stats_tracer import StatsTracer

logger = logging.getLogger(__name__)


class PeerConnectionManager:
    """Manages WebRTC peer connections for publishing and subscribing."""

    def __init__(self, connection_manager):
        self.connection_manager = connection_manager
        self.publisher_pc: Optional[PublisherPeerConnection] = None
        self.subscriber_pc: Optional[SubscriberPeerConnection] = None
        self.publisher_negotiation_lock = asyncio.Lock()
        self.subscriber_negotiation_lock = asyncio.Lock()
        # Stats tracers for getStats() delta compression
        self.publisher_stats: Optional[StatsTracer] = None
        self.subscriber_stats: Optional[StatsTracer] = None

    async def setup_subscriber(self):
        """Setup subscriber peer connection."""
        if not self.subscriber_pc or self.subscriber_pc.connectionState in [
            "closed",
            "failed",
        ]:
            self.subscriber_pc = SubscriberPeerConnection(
                connection=self.connection_manager,
                configuration=self._build_rtc_configuration(),
            )

            # Trace create event
            tracer = self.connection_manager.tracer
            pc_id = self.connection_manager.pc_id("sub")
            tracer.trace("create", pc_id, self._get_connection_config())

            # Setup PC event tracing
            self._setup_pc_tracing(self.subscriber_pc, pc_id)

            # Create stats tracer
            self.subscriber_stats = StatsTracer(
                self.subscriber_pc, "subscriber", DEFAULT_STATS_INTERVAL_MS / 1000
            )

            @self.subscriber_pc.on("audio")
            async def on_audio(pcm_data):
                self.connection_manager.emit("audio", pcm_data)

            @self.subscriber_pc.on("track_added")
            async def on_track_added(track, user):
                """Handle track events from MediaRelay subscribers"""
                await self.connection_manager.recording_manager.on_track_received(
                    track, user
                )
                self.connection_manager.emit(
                    "track_added", track._source.id, track.kind, user
                )

            # Trace ontrack events for subscriber
            @self.subscriber_pc.on("track")
            def on_track_trace(track):
                tracer.trace("ontrack", pc_id, f"{track.kind}:{track.id}")

            logger.debug("Created new subscriber peer connection")
        else:
            logger.debug("Reusing existing subscriber peer connection")

    async def add_tracks(
        self,
        audio: Optional[aiortc.mediastreams.MediaStreamTrack] = None,
        video: Optional[aiortc.mediastreams.MediaStreamTrack] = None,
    ):
        """Add multiple audio and video tracks in a single negotiation."""
        if not self.connection_manager.running:
            logger.error("Connection manager not running. Call connect() first.")
            return

        if not audio and not video:
            logger.warning("No tracks provided to add_tracks")
            return

        relayed_audio = None
        relayed_video = None
        audio_info = None
        video_info = None
        relayed_audio = None
        relayed_video = None
        track_infos = []
        if audio:
            audio_relay = MediaRelay()
            relayed_audio = audio_relay.subscribe(audio)
            audio_info = create_audio_track_info(relayed_audio)
        if video:
            video_relay = MediaRelay()
            relayed_video = video_relay.subscribe(video)
            video_info, relayed_video = await prepare_video_track_info(relayed_video)

        async with self.publisher_negotiation_lock:
            logger.info(f"Adding tracks: {len(track_infos)} tracks")

            tracer = self.connection_manager.tracer
            pc_id = self.connection_manager.pc_id("pub")

            if self.publisher_pc is None:
                self.publisher_pc = PublisherPeerConnection(
                    manager=self.connection_manager,
                    configuration=self._build_rtc_configuration(),
                )

                # Trace create event
                tracer.trace("create", pc_id, self._get_connection_config())

                # Setup PC event tracing
                self._setup_pc_tracing(self.publisher_pc, pc_id)

                # Create stats tracer
                self.publisher_stats = StatsTracer(
                    self.publisher_pc, "publisher", DEFAULT_STATS_INTERVAL_MS / 1000
                )

            if audio and relayed_audio:
                self.publisher_pc.addTrack(relayed_audio)
                logger.info(f"Added relayed audio track {relayed_audio.id}")
            if video and relayed_video:
                self.publisher_pc.addTrack(relayed_video)
                logger.info(f"Added relayed video track {relayed_video.id}")
                # Set frame tracker for video stats (BufferedMediaTrack has frame tracking)
                if self.publisher_stats:
                    self.publisher_stats.set_frame_tracker(relayed_video)

            # Trace createOffer
            tracer.trace("createOffer", pc_id, [])
            with telemetry.start_as_current_span(
                "rtc.publisher_pc.create_offer"
            ) as span:
                try:
                    offer = await self.publisher_pc.createOffer()
                    tracer.trace(
                        "createOfferOnSuccess",
                        pc_id,
                        {"type": "offer", "sdp": offer.sdp},
                    )
                    span.set_attribute("sdp", offer.sdp)
                except Exception as e:
                    tracer.trace("createOfferOnFailure", pc_id, str(e))
                    raise

            # Trace setLocalDescription
            tracer.trace(
                "setLocalDescription", pc_id, [{"type": offer.type, "sdp": offer.sdp}]
            )
            with telemetry.start_as_current_span(
                "rtc.publisher_pc.set_local_description"
            ) as span:
                span.set_attribute("sdp", offer.sdp)
                try:
                    await self.publisher_pc.setLocalDescription(offer)
                    tracer.trace("setLocalDescriptionOnSuccess", pc_id, None)
                except Exception as e:
                    tracer.trace("setLocalDescriptionOnFailure", pc_id, str(e))
                    raise

            try:
                patched_sdp = patch_sdp_offer(self.publisher_pc.localDescription.sdp)
                parsed_sdp = aiortc.sdp.SessionDescription.parse(patched_sdp)
                curr_mid = 0
                for media in parsed_sdp.media:
                    if (
                        audio
                        and audio_info
                        and relayed_audio
                        and media.kind == "audio"
                        and relayed_audio.id == parsed_sdp.webrtc_track_id(media)
                    ):
                        audio_info.mid = str(curr_mid)
                        track_infos.append(audio_info)
                        curr_mid += 1
                    if (
                        video
                        and video_info
                        and relayed_video
                        and media.kind == "video"
                        and relayed_video.id == parsed_sdp.webrtc_track_id(media)
                    ):
                        video_info.mid = str(curr_mid)
                        track_infos.append(video_info)
                logger.debug(f"Patched SDP offer: {patched_sdp}")
                logger.debug(f"Tracks: {track_infos}")
                response = (
                    await self.connection_manager.twirp_signaling_client.SetPublisher(
                        ctx=self.connection_manager.twirp_context,
                        request=signal_pb2.SetPublisherRequest(
                            session_id=self.connection_manager.session_id,
                            sdp=patched_sdp,
                            tracks=track_infos,
                        ),
                        server_path_prefix="",
                    )
                )

                # Trace setRemoteDescription
                tracer.trace(
                    "setRemoteDescription",
                    pc_id,
                    [{"type": "answer", "sdp": response.sdp}],
                )
                try:
                    await self.publisher_pc.handle_answer(response)
                    tracer.trace("setRemoteDescriptionOnSuccess", pc_id, None)
                except Exception as e:
                    tracer.trace("setRemoteDescriptionOnFailure", pc_id, str(e))
                    raise
                with telemetry.start_as_current_span(
                    "rtc.publisher_pc.wait_for_connected"
                ):
                    await self.publisher_pc.wait_for_connected()
            except SfuRpcError as e:
                logger.error(f"Failed to set publisher: {e}")
                raise

        # Register ORIGINAL tracks and their MediaRelay instances for reconnection
        track_info_index = 0
        if audio:
            # Store original track info with its MediaRelay for reconnection
            self.connection_manager.reconnector.reconnection_info.add_published_track(
                audio.id,
                audio,
                track_infos[track_info_index],
                relayed_audio,
            )
            track_info_index += 1
        if video:
            # Store original track info with its MediaRelay for reconnection
            self.connection_manager.reconnector.reconnection_info.add_published_track(
                video.id,
                video,
                track_infos[track_info_index],
                relayed_video,
            )

            # Schedule one-off stats send after video track is published
            if self.connection_manager.stats_reporter:
                self.connection_manager.stats_reporter.schedule_one(3000)

    async def restore_published_tracks(self):
        """Restore published tracks using their stored MediaRelay instances."""
        track_ids = list(
            self.connection_manager.reconnector.reconnection_info.published_tracks.keys()
        )
        logger.info(
            f"Restoring {len(track_ids)} published tracks with MediaRelay - Track IDs: {track_ids}"
        )

        # Collect all tracks to restore
        audio_tracks = []
        video_tracks = []

        for (
            track_id,
            track_info,
        ) in self.connection_manager.reconnector.reconnection_info.published_tracks.items():
            original_track = track_info["track"]  # Original track

            # Group tracks by type
            if original_track.kind == "audio":
                audio_tracks.append(original_track)
            elif original_track.kind == "video":
                video_tracks.append(original_track)

        # Restore tracks using the add_tracks method
        # This ensures proper MediaRelay usage and peer connection management
        try:
            # Restore first audio and video track together if available
            if audio_tracks or video_tracks:
                await self.add_tracks(
                    audio=audio_tracks[0] if audio_tracks else None,
                    video=video_tracks[0] if video_tracks else None,
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

            logger.info(
                f"Successfully restored all {len(track_ids)} tracks using stored MediaRelay instances"
            )

        except Exception as e:
            logger.error("Failed to restore published tracks", exc_info=e)
            raise

    async def close(self):
        """Close all peer connections."""
        cleanup_tasks = []

        if self.publisher_pc:
            cleanup_tasks.append(self.publisher_pc.close())
            self.publisher_pc = None
        if self.subscriber_pc:
            cleanup_tasks.append(self.subscriber_pc.close())
            self.subscriber_pc = None

        # Clear stats tracers
        self.publisher_stats = None
        self.subscriber_stats = None

        # Run peer connection cleanup concurrently
        if cleanup_tasks:
            try:
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            except Exception as e:
                logger.debug(f"Error during peer connection cleanup: {e}")

    async def cleanup_connections(self, publisher_pc=None, subscriber_pc=None):
        """Clean up specific peer connections."""
        cleanup_tasks = []

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

    def _build_rtc_configuration(self) -> aiortc.RTCConfiguration:
        """Build RTCConfiguration from coordinator credentials.

        Returns:
            aiortc.RTCConfiguration with ICE servers from join response
        """
        credentials = self.connection_manager.join_response.credentials
        ice_servers = [
            aiortc.RTCIceServer(
                urls=server.get("urls"),
                username=server.get("username"),
                credential=server.get("password") or server.get("credential"),
            )
            for server in credentials.ice_servers
        ]
        return aiortc.RTCConfiguration(
            iceServers=ice_servers,
            bundlePolicy=aiortc.RTCBundlePolicy.MAX_BUNDLE,
        )

    def _get_connection_config(self) -> dict:
        """Get the connection configuration for tracing.

        Returns:
            Dict with ICE server configuration matching JS SDK format
        """
        credentials = self.connection_manager.join_response.credentials
        ice_servers = [
            {
                "urls": server.get("urls"),
                "username": server.get("username"),
                "credential": server.get("password") or server.get("credential"),
            }
            for server in credentials.ice_servers
        ]
        return {
            "url": credentials.server.edge_name,
            "bundlePolicy": "max-bundle",
            "iceServers": ice_servers,
        }

    def _setup_pc_tracing(self, pc, pc_id: str) -> None:
        """Attach event listeners that trace PC events.

        Args:
            pc: The RTCPeerConnection to trace
            pc_id: The PC ID for tracing (e.g., "0-pub", "0-sub")
        """
        tracer = self.connection_manager.tracer

        @pc.on("signalingstatechange")
        def on_signaling():
            tracer.trace("signalingstatechange", pc_id, pc.signalingState)

        @pc.on("iceconnectionstatechange")
        def on_ice_conn():
            tracer.trace("iceconnectionstatechange", pc_id, pc.iceConnectionState)

        @pc.on("icegatheringstatechange")
        def on_ice_gather():
            tracer.trace("icegatheringstatechange", pc_id, pc.iceGatheringState)

        @pc.on("connectionstatechange")
        def on_conn():
            tracer.trace("connectionstatechange", pc_id, pc.connectionState)

        @pc.on("icecandidate")
        def on_ice_candidate(candidate):
            # Trace ICE candidate (may be None when gathering is complete)
            tracer.trace("onicecandidate", pc_id, candidate)
