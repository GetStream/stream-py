"""
Manages WebRTC publishing and subscribing via the Rust RTC session.
"""

import asyncio
import logging
from typing import Any, Optional

from getstream.video.rtc.media import (
    MediaStreamError,
    RemoteMediaTrack,
    av_audio_to_pcm_bytes,
    av_video_to_i420,
    pcm_bytes_to_pcmdata,
)
from getstream.video.rtc.track_util import PcmData

logger = logging.getLogger(__name__)


class _PeerStub:
    """Stand-in for the historic publisher/subscriber RTCPeerConnection."""

    def __init__(self, state: str = "connected") -> None:
        self.connectionState = state
        self.signalingState = "stable"
        self.iceConnectionState = "connected"
        self.iceGatheringState = "complete"
        self._closed = False

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.connectionState = "closed"
        self.signalingState = "closed"

    async def restartIce(self) -> None:
        logger.debug("ICE restart is owned by the Rust session")

    def removeListener(self, *args: Any, **kwargs: Any) -> None:
        return None

    def on(self, *args: Any, **kwargs: Any) -> None:
        return None


class _WsStub:
    """Stand-in for the historic Python SFU WebSocket client."""

    def __init__(self, edge_name: Optional[str] = None) -> None:
        self.running = True
        self.edge_name = edge_name
        self.closed = False

    def close(self) -> None:
        self.running = False
        self.closed = True

    def on_event(self, *args: Any, **kwargs: Any) -> None:
        return None

    def on_wildcard(self, *args: Any, **kwargs: Any) -> None:
        return None


class PeerConnectionManager:
    """Publishes duck-typed recv() tracks and pumps inbound Rust media."""

    def __init__(self, connection_manager, drain_video_frames: bool = True):
        self.connection_manager = connection_manager
        self._drain_video_frames = drain_video_frames
        self.publisher_pc: Optional[_PeerStub] = None
        self.subscriber_pc: Optional[_PeerStub] = None
        self.publisher_negotiation_lock = asyncio.Lock()
        self.subscriber_negotiation_lock = asyncio.Lock()
        self.publisher_stats = None
        self.subscriber_stats = None
        self._session = None
        self._tasks: set[asyncio.Task] = set()
        self._inbound_tracks: dict[str, RemoteMediaTrack] = {}

    def attach_session(self, session) -> None:
        self._session = session
        self.publisher_pc = _PeerStub("connected")
        self.subscriber_pc = _PeerStub("connected")
        self._spawn(self._pump_inbound_tracks(), name="rtc-inbound-tracks")

    def _spawn(self, coro, name: str) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def setup_subscriber(self):
        """Kept for reconnect callers; the Rust session owns the subscriber PC."""
        if self.subscriber_pc is None or self.subscriber_pc.connectionState in [
            "closed",
            "failed",
        ]:
            self.subscriber_pc = _PeerStub("new")

    async def add_tracks(self, audio=None, video=None):
        """Add multiple audio and video tracks in a single negotiation."""
        if not self.connection_manager.running:
            logger.error("Connection manager not running. Call connect() first.")
            return

        if not audio and not video:
            logger.warning("No tracks provided to add_tracks")
            return

        session = self._session
        if session is None:
            logger.error("RTC session is not attached")
            return

        from getstream_rtc_core import LocalAudioTrack, LocalVideoTrack

        async with self.publisher_negotiation_lock:
            if self.publisher_pc is None:
                self.publisher_pc = _PeerStub("connecting")

            if audio:
                local_audio = LocalAudioTrack.opus()
                await session.publish_audio(local_audio)
                self._spawn(
                    self._pump_outbound_audio(audio, local_audio),
                    name="rtc-publish-audio",
                )
                try:
                    track_id = audio.id
                except Exception:
                    track_id = str(id(audio))
                self.connection_manager.reconnector.reconnection_info.add_published_track(
                    track_id, audio, None, None
                )
                logger.info("Published local audio track")

            if video:
                local_video = LocalVideoTrack.vp8()
                await session.publish_video(local_video)
                self._spawn(
                    self._pump_outbound_video(video, local_video),
                    name="rtc-publish-video",
                )
                try:
                    track_id = video.id
                except Exception:
                    track_id = str(id(video))
                self.connection_manager.reconnector.reconnection_info.add_published_track(
                    track_id, video, None, None
                )
                logger.info("Published local video track")
                if self.connection_manager.stats_reporter:
                    self.connection_manager.stats_reporter.schedule_one(3000)

            if self.publisher_pc:
                self.publisher_pc.connectionState = "connected"

    async def _pump_outbound_audio(self, source, local_audio) -> None:
        while True:
            try:
                frame = await source.recv()
            except MediaStreamError:
                break
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("Outbound audio track ended", exc_info=True)
                break
            try:
                pcm_bytes, sample_rate, channels = av_audio_to_pcm_bytes(frame)
                await local_audio.write_pcm(
                    pcm_bytes, sample_rate=sample_rate, channels=channels
                )
            except Exception:
                logger.exception("Failed to write outbound PCM")

    async def _pump_outbound_video(self, source, local_video) -> None:
        while True:
            try:
                frame = await source.recv()
            except MediaStreamError:
                break
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("Outbound video track ended", exc_info=True)
                break
            try:
                data, width, height, duration_ms = av_video_to_i420(frame)
                await local_video.write_i420(
                    data, width, height, duration_ms=duration_ms
                )
            except Exception:
                logger.exception("Failed to write outbound I420")

    async def _pump_inbound_tracks(self) -> None:
        session = self._session
        if session is None:
            return
        while True:
            try:
                remote = await session.next_track()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.debug("Inbound track pump stopped", exc_info=True)
                break
            if remote is None:
                break
            user = self._user_for_remote(remote)
            wrapper = RemoteMediaTrack(remote, user=user)
            self._inbound_tracks[wrapper.id] = wrapper
            self._spawn(
                self._pump_remote_track(wrapper, user),
                name=f"rtc-remote-{wrapper.kind}",
            )
            try:
                await self.connection_manager.recording_manager.on_track_received(
                    wrapper.subscribe(), user
                )
            except Exception:
                logger.exception("recording_manager.on_track_received failed")
            self.connection_manager.emit(
                "track_added", wrapper.id, wrapper.kind, user
            )

    def _user_for_remote(self, remote) -> Any:
        prefix = remote.track_lookup_prefix or remote.session_id
        user = self.connection_manager.participants_state.get_user_from_track_id(
            f"{prefix}:audio:0"
        )
        if user is None:
            for participant in self.connection_manager.participants_state.get_participants():
                if participant.session_id == remote.session_id:
                    return participant
        if user is None and remote.track_type in ("audio", "screenshare_audio"):
            user = (
                self.connection_manager._subscription_manager.get_next_expected_audio_user()
            )
        return user

    async def _pump_remote_track(self, wrapper: RemoteMediaTrack, user) -> None:
        while True:
            decoded = await wrapper.next_decoded()
            if decoded is None:
                break
            if wrapper.kind != "audio":
                continue
            pcm: PcmData = pcm_bytes_to_pcmdata(
                bytes(decoded.samples),
                decoded.sample_rate,
                decoded.channels,
                participant=user,
            )
            self.connection_manager.emit("audio", pcm)

    async def restore_published_tracks(self):
        """Restore published tracks by republishing the original recv() sources."""
        published = self.connection_manager.reconnector.reconnection_info.published_tracks
        track_ids = list(published.keys())
        logger.info(f"Restoring {len(track_ids)} published tracks")

        audio_tracks = []
        video_tracks = []
        for track_info in published.values():
            original_track = track_info["track"]
            kind = None
            try:
                kind = original_track.kind
            except Exception:
                kind = None
            if kind == "audio":
                audio_tracks.append(original_track)
            elif kind == "video":
                video_tracks.append(original_track)

        try:
            if audio_tracks or video_tracks:
                await self.add_tracks(
                    audio=audio_tracks[0] if audio_tracks else None,
                    video=video_tracks[0] if video_tracks else None,
                )
            for i, track in enumerate(audio_tracks[1:], 1):
                await self.add_tracks(audio=track)
                logger.info(f"Restored additional audio track {i}")
            for i, track in enumerate(video_tracks[1:], 1):
                await self.add_tracks(video=track)
                logger.info(f"Restored additional video track {i}")
        except Exception as e:
            logger.error("Failed to restore published tracks", exc_info=e)
            raise

    async def close(self):
        """Close all peer connections and background pumps."""
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        self._inbound_tracks.clear()

        cleanup_tasks = []
        if self.publisher_pc:
            cleanup_tasks.append(self.publisher_pc.close())
            self.publisher_pc = None
        if self.subscriber_pc:
            cleanup_tasks.append(self.subscriber_pc.close())
            self.subscriber_pc = None
        self.publisher_stats = None
        self.subscriber_stats = None
        self._session = None
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)

    async def cleanup_connections(self, publisher_pc=None, subscriber_pc=None):
        """Clean up specific peer connections."""
        cleanup_tasks = []
        if publisher_pc:
            cleanup_tasks.append(publisher_pc.close())
        if subscriber_pc:
            cleanup_tasks.append(subscriber_pc.close())
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
