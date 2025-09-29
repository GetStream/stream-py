"""
Connection utilities for video streaming.

This module provides core connection-related functionality including:
- Connection state management
- Connection options
- Call coordination
- Track info preparation
- WebSocket URL handling
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple

import aiortc
from aiortc.rtcrtpsender import RTCRtpSender

from getstream.base import StreamResponse
from getstream.models import CallRequest
from getstream.utils import build_body_dict, build_query_param
from getstream.video.async_call import Call
from getstream.video.rtc.models import JoinCallResponse
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TRACK_TYPE_AUDIO,
    TRACK_TYPE_VIDEO,
    TrackInfo,
    VideoDimension,
    VideoLayer,
)
from getstream.video.rtc.signaling import SignalingError, WebSocketClient
from getstream.video.rtc.track_util import BufferedMediaTrack, detect_video_properties

logger = logging.getLogger(__name__)

# Public API - only these should be used outside this module
__all__ = [
    "ConnectionState",
    "SfuConnectionError",
    "ConnectionOptions",
    "join_call",
    "join_call_coordinator_request",
    "create_join_request",
    "prepare_video_track_info",
    "create_audio_track_info",
    "get_websocket_url",
    "connect_websocket",
]

# Private constants - internal use only
_RETRYABLE_ERROR_PATTERNS = [
    "server is full",
    "server overloaded",
    "capacity exceeded",
    "try again later",
    "service unavailable",
    "connection timeout",
    "network error",
    "temporary failure",
    "connection refused",
    "connection reset",
]


# Public classes and exceptions
class ConnectionState(Enum):
    """Enumeration of possible connection states."""

    IDLE = "idle"
    JOINING = "joining"
    JOINED = "joined"
    RINGING = "ringing"
    RECONNECTING = "reconnecting"
    MIGRATING = "migrating"
    OFFLINE = "offline"
    RECONNECTING_FAILED = "reconnecting_failed"
    LEFT = "left"


class SfuConnectionError(Exception):
    """Exception raised when SFU connection fails."""

    pass


@dataclass
class ConnectionOptions:
    """Options for the connection process."""

    join_response: Optional[Any] = None
    region: Optional[str] = None
    fast_reconnect: bool = False
    migrating_from: Optional[str] = None
    previous_session_id: Optional[str] = None


async def join_call(
    call,
    user_id: str,
    location: str,
    create: bool,
    local_sfu: bool,
    connection_id: str,
    **kwargs,
):
    """Join call via coordinator API."""
    try:
        join_response = await join_call_coordinator_request(
            call,
            user_id,
            location=location,
            create=create,
            connection_id=connection_id,
            **kwargs,
        )
        if local_sfu:
            join_response.data.credentials.server.url = "http://127.0.0.1:3031/twirp"
            join_response.data.credentials.server.ws_endpoint = "ws://127.0.0.1:3031/ws"

        logger.debug(
            f"Received SFU credentials: {join_response.data.credentials.server}"
        )

        return join_response

    except Exception as e:
        logger.error(f"Failed to join call via coordinator: {e}")
        raise SfuConnectionError(f"Failed to join call: {e}")


async def join_call_coordinator_request(
    call: Call,
    user_id: str,
    create: bool = False,
    data: Optional[CallRequest] = None,
    ring: Optional[bool] = None,
    notify: Optional[bool] = None,
    video: Optional[bool] = None,
    location: Optional[str] = None,
    connection_id: Optional[str] = None,
) -> StreamResponse[JoinCallResponse]:
    """Make a request to join a call via the coordinator.

    Args:
        call: The call to join
        user_id: The user ID to join the call with
        create: Whether to create the call if it doesn't exist
        data: Additional call data if creating
        ring: Whether to ring other users
        notify: Whether to notify other users
        video: Whether to enable video
        location: The preferred location

    Returns:
        A response containing the call information and credentials
    """
    # Create a token for this user
    token = call.client.stream.create_token(user_id=user_id)

    # create a new client with this token
    client = call.client.stream.__class__(
        api_key=call.client.stream.api_key,
        api_secret=call.client.stream.api_secret,
        base_url=call.client.stream.base_url,
    )

    # set up authentication
    client.token = token
    client.headers["authorization"] = token
    client.client.headers["authorization"] = token

    # Prepare path parameters for the request
    path_params = {
        "type": call.call_type,
        "id": call.id,
    }

    # Build the request body
    json_body = build_body_dict(
        location=location or "FRA",  # Default to Frankfurt if not specified
        create=create,
        notify=notify,
        ring=ring,
        video=video,
        data=data,
    )
    query_params = build_query_param(connection_id=connection_id)

    # Make the POST request to join the call
    return await client.post(
        "/api/v2/video/call/{type}/{id}/join",
        JoinCallResponse,
        path_params=path_params,
        query_params=query_params,
        json=json_body,
    )


async def create_join_request(token: str, session_id: str) -> events_pb2.JoinRequest:
    """Create a JoinRequest protobuf message for the WebSocket connection.

    Args:
        token: The token for the user
        session_id: The session ID for this connection

    Returns:
        A JoinRequest protobuf message configured with data
    """

    # Create a JoinRequest
    join_request = events_pb2.JoinRequest()
    join_request.token = token
    join_request.session_id = session_id

    # Create generic SDPs for send and recv
    temp_pub_pc = aiortc.RTCPeerConnection()
    temp_sub_pc = aiortc.RTCPeerConnection()
    temp_pub_pc.addTransceiver(direction="sendonly", trackOrKind="video")
    temp_pub_pc.addTransceiver(direction="sendonly", trackOrKind="audio")
    temp_sub_pc.addTransceiver(direction="recvonly", trackOrKind="video")
    temp_sub_pc.addTransceiver(direction="recvonly", trackOrKind="audio")

    # Prefer non-VP8 codecs by excluding VP8 from codec preferences for video
    video_codecs_excluding_vp8 = [
        c
        for c in RTCRtpSender.getCapabilities("video").codecs
        if c.name.lower() != "vp8"
    ]
    if video_codecs_excluding_vp8:
        for transceiver in temp_pub_pc.getTransceivers():
            if transceiver.kind == "video":
                transceiver.setCodecPreferences(video_codecs_excluding_vp8)
        for transceiver in temp_sub_pc.getTransceivers():
            if transceiver.kind == "video":
                transceiver.setCodecPreferences(video_codecs_excluding_vp8)

    pub_offer = await temp_pub_pc.createOffer()
    sub_offer = await temp_sub_pc.createOffer()
    join_request.publisher_sdp = pub_offer.sdp
    join_request.subscriber_sdp = sub_offer.sdp

    for transceiver in temp_pub_pc.getTransceivers():
        await transceiver.stop()
    for transceiver in temp_sub_pc.getTransceivers():
        await transceiver.stop()

    await temp_pub_pc.close()
    await temp_sub_pc.close()

    return join_request


async def prepare_video_track_info(
    video: aiortc.mediastreams.MediaStreamTrack,
) -> Tuple[TrackInfo, aiortc.mediastreams.MediaStreamTrack]:
    """Prepare video track info by detecting its properties.

    Args:
        video: A video MediaStreamTrack

    Returns:
        A tuple of (TrackInfo, buffered_video_track)

    Raises:
        Exception: If video property detection fails
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


def create_audio_track_info(audio: aiortc.mediastreams.MediaStreamTrack) -> TrackInfo:
    """Create track info for an audio track.

    Args:
        audio: An audio MediaStreamTrack

    Returns:
        A TrackInfo object for the audio track
    """
    return TrackInfo(
        track_id=audio.id,
        track_type=TRACK_TYPE_AUDIO,
    )


def get_websocket_url(join_response, local_sfu: bool = False) -> str:
    """Get the WebSocket URL from join response.

    Args:
        join_response: The response from the coordinator join call
        local_sfu: Whether to use local SFU URL for development

    Returns:
        The WebSocket URL to connect to
    """
    if local_sfu:
        return "ws://127.0.0.1:3031/ws"
    return join_response.data.credentials.server.ws_endpoint


async def connect_websocket(
    token: str,
    ws_url: str,
    session_id: str,
    options: ConnectionOptions,
) -> Tuple[WebSocketClient, events_pb2.SfuEvent]:
    """
    Connect to the WebSocket server.

    Args:
        token: Authentication token
        ws_url: WebSocket URL to connect to
        session_id: Session ID for this connection
        options: Connection options

    Returns:
        Tuple of (WebSocket client, initial SFU event)

    Raises:
        SignalingError: If connection fails
    """
    logger.info(f"Connecting to WebSocket at {ws_url}")

    try:
        # Create JoinRequest for WebSocket connection
        join_request = await create_join_request(token, session_id)

        # Apply reconnect options if provided
        if options.fast_reconnect:
            join_request.fast_reconnect = True
        if options.migrating_from:
            join_request.reconnect_details.migrating_from = options.migrating_from
        if options.previous_session_id:
            join_request.reconnect_details.previous_session_id = (
                options.previous_session_id
            )

        # Create and connect WebSocket client
        ws_client = WebSocketClient(ws_url, join_request, asyncio.get_running_loop())
        sfu_event = await ws_client.connect()

        logger.debug("WebSocket connection established")
        return ws_client, sfu_event

    except Exception as e:
        logger.error(f"Failed to connect WebSocket to {ws_url}: {e}")
        raise SignalingError(f"WebSocket connection failed: {e}")


# Private functions
def _is_retryable(retry_state: Any) -> bool:
    """Check if an error should be retried.

    Args:
        retry_state: The retry state object from tenacity

    Returns:
        True if the error should be retried, False otherwise
    """
    # Extract the actual exception from the retry state
    if hasattr(retry_state, "outcome") and retry_state.outcome.failed:
        error = retry_state.outcome.exception()
    else:
        return False

    # Import here to avoid circular imports
    from getstream.video.rtc.signaling import SignalingError

    if not isinstance(error, (SignalingError, SfuConnectionError)):
        return False

    error_message = str(error).lower()
    return any(pattern in error_message for pattern in _RETRYABLE_ERROR_PATTERNS)
