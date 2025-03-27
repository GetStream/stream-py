import logging
from dataclasses_json import config as dc_config, DataClassJsonMixin
from dataclasses import field as dc_field, dataclass
from typing import List, Optional, Dict, Any

from getstream.base import StreamResponse
from getstream.models import CallRequest, CallResponse, MemberResponse
from getstream.video.call import Call
from getstream.utils import build_body_dict
from getstream.video.rtc.location_discovery import (
    HTTPHintLocationDiscovery,
    HEADER_CLOUDFRONT_POP,
    FALLBACK_LOCATION_NAME,
    STREAM_PROD_URL,
)

logger = logging.getLogger("getstream.video.rtc")

try:
    import aiortc
except ImportError:
    # before throwing, suggest the user to install the `webrtc` optional dependency
    raise ImportError(
        "The `webrtc` optional dependency is required to use the `getstream.video.rtc` module. "
        "Please install it using the following command: `pip install getstream[webrtc]`"
    )


logger.debug(f"loaded aiortc {aiortc.__version__} correctly")


@dataclass
class JoinCallRequest(DataClassJsonMixin):
    create: Optional[bool] = dc_field(
        default=False, metadata=dc_config(field_name="create")
    )
    data: "Optional[CallRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )
    ring: Optional[bool] = dc_field(default=None, metadata=dc_config(field_name="ring"))
    notify: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="notify")
    )
    video: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="video")
    )
    location: str = dc_field(default="", metadata=dc_config(field_name="location"))


@dataclass
class ServerCredentials(DataClassJsonMixin):
    edge_name: str = dc_field(metadata=dc_config(field_name="edge_name"))
    url: str = dc_field(metadata=dc_config(field_name="url"))
    ws_endpoint: str = dc_field(metadata=dc_config(field_name="ws_endpoint"))


@dataclass
class Credentials(DataClassJsonMixin):
    server: ServerCredentials = dc_field(metadata=dc_config(field_name="server"))
    token: str = dc_field(metadata=dc_config(field_name="token"))
    ice_servers: List[Dict[str, Any]] = dc_field(
        metadata=dc_config(field_name="ice_servers")
    )


@dataclass
class JoinCallResponse(DataClassJsonMixin):
    call: CallResponse = dc_field(metadata=dc_config(field_name="call"))
    members: List[MemberResponse] = dc_field(metadata=dc_config(field_name="members"))
    credentials: Credentials = dc_field(metadata=dc_config(field_name="credentials"))
    stats_options: dict = dc_field(metadata=dc_config(field_name="stats_options"))


async def join_call_coordinator_request(
    call: Call,
    user_id: str,
    create: bool = False,
    data: Optional[CallRequest] = None,
    ring: Optional[bool] = None,
    notify: Optional[bool] = None,
    video: Optional[bool] = None,
    location: Optional[str] = None,
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

    # Create a new client with this token
    client = call.client.stream.__class__(
        api_key=call.client.stream.api_key,
        api_secret=call.client.stream.api_secret,
        base_url=call.client.stream.base_url,
    )

    # Set up authentication
    client.token = token
    client.headers["Authorization"] = token
    client.client.headers["Authorization"] = token

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

    # Make the POST request to join the call
    return client.post(
        "/api/v2/video/call/{type}/{id}/join",
        JoinCallResponse,
        path_params=path_params,
        json=json_body,
    )


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


class ConnectionManager:
    def __init__(self, call: Call):
        self.call = call

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


async def join(
    call: Call, user_id: str = None, create=True, **kwargs
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
    logger.info("discovering location")
    try:
        location = await discover_location()
        logger.info(f"discovered location: {location}")
    except Exception as e:
        logger.error(f"Failed to discover location: {e}")
        # Default to a reasonable location if discovery fails
        location = "FRA"
        logger.info(f"using default location: {location}")

    logger.info("performing join call request on coordinator API")
    join_call_response = await join_call_coordinator_request(
        call, user_id, create=create, location=location, **kwargs
    )
    logger.info(
        f"received credentials to connect to sfu {join_call_response.data.credentials.server.url}"
    )

    # step 2: setup peer connections
    # step 3: create the ws connection to the SFU
    # step 4: send the JoinRequest to the SFU
    # step 5: return the ConnectionManager object
    return ConnectionManager(call=call)


__all__ = [
    "HTTPHintLocationDiscovery",
    "HEADER_CLOUDFRONT_POP",
    "FALLBACK_LOCATION_NAME",
    "STREAM_PROD_URL",
    "join",
    "ConnectionManager",
]
