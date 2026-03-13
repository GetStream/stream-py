import logging
import os
from typing import Optional

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


def _patch_aiortc_video_bitrates() -> None:
    """
    Patch aiortc codec bitrate defaults to enable higher bitrates
    for acceptable video quality in Stream calls.
    """

    try:
        import aiortc.codecs.h264 as _h264_codec
        import aiortc.codecs.vpx as _vpx_codec

        _vpx_codec.DEFAULT_BITRATE = 2_500_000  # type: ignore[assignment]  # 2.5 Mbps (was 500 kbps)
        _vpx_codec.MIN_BITRATE = 1_500_000  # type: ignore[assignment]  # 1.5 Mbps (was 250 kbps)
        _vpx_codec.MAX_BITRATE = 3_000_000  # type: ignore[assignment]  # 3 Mbps (was 1.5 Mbps)

        _h264_codec.DEFAULT_BITRATE = 2_500_000  # type: ignore[assignment]  # 2.5 Mbps (was 1 Mbps)
        _h264_codec.MIN_BITRATE = 1_500_000  # type: ignore[assignment]  # 1.5 Mbps (was 500 kbps)
    except Exception:
        # Log a warning in case the patches failed to apply
        logger.warning(
            "Failed to patch aiortc codecs bitrates for vpx and h264, falling back to defaults."
        )
        logger.debug("Detailed traceback:", exc_info=True)


PATCH_AIORTC_BITRATES = os.getenv("STREAM_PATCH_AIORTC_BITRATES", "").lower().strip()
if PATCH_AIORTC_BITRATES not in ("0", "false", "no", "off"):
    # Patch aiortc video codecs bitrates only if it's not disabled via env.
    # `STREAM_PATCH_AIORTC_BITRATES=0|off|no|false` disables it.
    _patch_aiortc_video_bitrates()


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
    call: Call, user_id: Optional[str] = None, create=True, **kwargs
) -> ConnectionManager:
    """
    Join a call. This method will:
    - discover the best location
    - join the call (or create it if needed)
    - setup the peer connection
    - connect to the SFU

    Args:
        call: The call to join
        user_id: The user id to join with
        create: Whether to create the call if it doesn't exist
        **kwargs: Additional arguments to pass to the join call request

    Returns:
        A ConnectionManager object that can be used as a context manager
    """
    # Return ConnectionManager instance that handles everything internally
    # when used as an async context manager and async iterator
    return ConnectionManager(call=call, user_id=user_id, create=create, **kwargs)


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
]
