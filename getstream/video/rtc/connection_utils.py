import asyncio
import logging
from enum import Enum
from typing import Any, Tuple

import aiortc
from getstream.video.rtc.pb.stream.video.sfu.event import events_pb2
from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TrackInfo,
    TRACK_TYPE_VIDEO,
    TRACK_TYPE_AUDIO,
    VideoLayer,
    VideoDimension,
)
from getstream.video.rtc.track_util import BufferedMediaTrack, detect_video_properties

logger = logging.getLogger(__name__)

# Public API - only these functions should be used outside this module
__all__ = [
    'ConnectionState',
    'SfuConnectionError',
    'is_retryable',
    'create_join_request', 
    'prepare_video_track_info',
    'create_audio_track_info', 
    'get_websocket_url',
]

# Error patterns that indicate retryable conditions
RETRYABLE_ERROR_PATTERNS = [
    "server is full",
    "server overloaded", 
    "capacity exceeded",
    "try again later",
    "service unavailable",
    "connection timeout",
    "network error",
    "temporary failure",
    "connection refused",
    "connection reset"
]


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


def is_retryable(retry_state: Any) -> bool:
    """Check if an error should be retried.
    
    Args:
        retry_state: The retry state object from tenacity
        
    Returns:
        True if the error should be retried, False otherwise
    """
    # Extract the actual exception from the retry state
    if hasattr(retry_state, 'outcome') and retry_state.outcome.failed:
        error = retry_state.outcome.exception()
    else:
        return False
    
    # Import here to avoid circular imports
    from getstream.video.rtc.signaling import SignalingError
    
    if not isinstance(error, (SignalingError, SfuConnectionError)):
        return False
    
    error_message = str(error).lower()
    return any(pattern in error_message for pattern in RETRYABLE_ERROR_PATTERNS)


def create_join_request(join_response, session_id: str) -> events_pb2.JoinRequest:
    """Create a JoinRequest protobuf message for the WebSocket connection.

    Args:
        join_response: The response from the coordinator join call
        session_id: The session ID for this connection

    Returns:
        A JoinRequest protobuf message configured with data from the coordinator response
    """
    # Get credentials from the coordinator response
    credentials = join_response.data.credentials

    # Create a JoinRequest
    join_request = events_pb2.JoinRequest()
    join_request.token = credentials.token
    join_request.session_id = session_id
    return join_request

async def prepare_video_track_info(
    video: aiortc.mediastreams.MediaStreamTrack
) -> Tuple[TrackInfo, aiortc.mediastreams.MediaStreamTrack]:
    """
    Prepare video track info by detecting its properties.

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
    """
    Create track info for an audio track.

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
    """
    Get the WebSocket URL from join response.

    Args:
        join_response: The response from the coordinator join call
        local_sfu: Whether to use local SFU URL for development

    Returns:
        The WebSocket URL to connect to
    """
    if local_sfu:
        return "ws://127.0.0.1:3031/ws"
    return join_response.data.credentials.server.ws_endpoint
