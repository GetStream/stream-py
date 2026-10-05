import logging
from typing import Optional

from getstream._rust import (
    AudioLevelChanged,
    CallEnded,
    CallEvent,
    CallGrantsUpdated,
    CallingState,
    ChangePublishOptions,
    ChangePublishQuality,
    ConnectionQualityChanged,
    DominantSpeakerChanged,
    Error,
    ICERestart,
    InboundStateNotification,
    ParticipantCountChanged,
    ParticipantJoined,
    ParticipantLeft,
    ParticipantUpdated,
    PinsChanged,
    RemoteParticipant,
    RemoteTrack,
    TrackPublished,
    TrackType,
    TrackUnpublished,
    VideoFrame,
    VideoFrameStream,
)
from getstream.video.async_call import Call
from getstream.video.rtc.audio_track import AudioStreamTrack
from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.rtc.connection_utils import join_call_coordinator_request
from getstream.video.rtc.g711 import (
    G711Encoding,
    G711Mapping,
)
from getstream.video.rtc.location_discovery import (
    FALLBACK_LOCATION_NAME,
    HEADER_CLOUDFRONT_POP,
    STREAM_PROD_URL,
    HTTPHintLocationDiscovery,
)
from getstream.video.rtc.models import (
    Credentials,
    JoinCallRequest,
    JoinCallResponse,
    ServerCredentials,
)
from getstream.video.rtc.track_util import (
    AudioFormat,
    PcmData,
    Resampler,
)
from getstream.video.rtc.tracks import SubscriptionConfig

logger = logging.getLogger(__name__)

try:
    import aiortc
except ImportError:
    # before throwing, suggest the user to install the `webrtc` optional dependency
    raise ImportError(
        "The `webrtc` optional dependency is required to use the `getstream.video.rtc` module. "
        "Please install it using the following command: `pip install getstream[webrtc]`"
    )

logger.debug(f"loaded aiortc {aiortc.__version__} correctly")


async def discover_location():
    """
    Discover the closest location based on CloudFront pop headers.

    Returns:
        str: The 3-character location code (e.g. "IAD")
    """
    logger.info("Discovering location")
    discovery = HTTPHintLocationDiscovery(logger=logger)
    # Even though discover is synchronous, we keep this function async for future compatibility
    return discovery.discover()


async def join(
    call: Call,
    user_id: Optional[str] = None,
    create=True,
    subscription_config: Optional[SubscriptionConfig] = None,
) -> ConnectionManager:
    """
    Make a ConnectionManager for a call. Entering it (or `connect()`) joins the
    call, or creates it if needed; the SDK chooses the SFU and connects.

    Args:
        call: The call to join
        user_id: The user id to join with
        create: Whether to create the call if it doesn't exist
        subscription_config: The remote tracks to subscribe to; without it,
            only remote audio is received

    Returns:
        A ConnectionManager object that can be used as a context manager
    """
    return ConnectionManager(
        call=call,
        user_id=user_id,
        create=create,
        subscription_config=subscription_config,
    )


__all__ = [
    "HTTPHintLocationDiscovery",
    "HEADER_CLOUDFRONT_POP",
    "FALLBACK_LOCATION_NAME",
    "STREAM_PROD_URL",
    "join",
    "ConnectionManager",
    "JoinCallRequest",
    "JoinCallResponse",
    "ServerCredentials",
    "Credentials",
    "join_call_coordinator_request",
    "discover_location",
    "PcmData",
    "Resampler",
    "AudioFormat",
    "G711Encoding",
    "G711Mapping",
    "AudioStreamTrack",
    "CallingState",
    "RemoteParticipant",
    "RemoteTrack",
    "TrackType",
    "VideoFrame",
    "VideoFrameStream",
    "CallEvent",
    "AudioLevelChanged",
    "CallEnded",
    "CallGrantsUpdated",
    "ChangePublishOptions",
    "ChangePublishQuality",
    "ConnectionQualityChanged",
    "DominantSpeakerChanged",
    "Error",
    "ICERestart",
    "InboundStateNotification",
    "ParticipantCountChanged",
    "ParticipantJoined",
    "ParticipantLeft",
    "ParticipantUpdated",
    "PinsChanged",
    "TrackPublished",
    "TrackUnpublished",
]
