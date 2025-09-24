import logging
from typing import Optional

from getstream.video.call import Call
from getstream.video.rtc.location_discovery import (
    HTTPHintLocationDiscovery,
    HEADER_CLOUDFRONT_POP,
    FALLBACK_LOCATION_NAME,
    STREAM_PROD_URL,
)
from getstream.video.rtc.models import (
    JoinCallRequest,
    JoinCallResponse,
    ServerCredentials,
    Credentials,
)
from getstream.video.rtc.connection_utils import join_call_coordinator_request
from getstream.video.rtc.connection_manager import ConnectionManager

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
]
