import logging

from getstream import Stream
from getstream.models import CallRequest, CallResponse, MemberResponse
from getstream.stream_response import StreamResponse
from getstream.utils import build_body_dict, retry
from getstream.video.rtc.connection_manager import ConnectionManager
from getstream.video.call import Call
from dataclasses import dataclass
from dataclasses import field as dc_field
from dataclasses_json import DataClassJsonMixin
from dataclasses_json import config as dc_config
from typing import Optional, List
from getstream.video.rtc.location_discovery import (
    HTTPHintLocationDiscovery,
    HEADER_CLOUDFRONT_POP,
    FALLBACK_LOCATION_NAME,
    STREAM_PROD_URL,
)

# Create a logger for the rtc module
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
    ice_servers: dict = dc_field(metadata=dc_config(field_name="ice_servers"))


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
) -> StreamResponse[JoinCallResponse]:
    # here we need to do a few things: create a token and then create a new client with it
    token = call.client.stream.create_token(user_id=user_id)

    client = Stream(
        api_key=call.client.stream.api_key,
        api_secret=call.client.stream.api_secret,
        base_url=call.client.stream.base_url,
    )

    # TODO: have a cleaner way to do this
    client.token = token
    client.headers["Authorization"] = token
    client.client.headers["Authorization"] = token

    path_params = {
        "type": call.call_type,
        "id": call.id,
    }

    json = build_body_dict(
        location="FRA",
        create=create,
        notify=notify,
        ring=ring,
        video=video,
        data=data,
    )

    return client.post(
        "/api/v2/video/call/{type}/{id}/join",
        JoinCallResponse,
        path_params=path_params,
        json=json,
    )


async def discover_location():
    """
    Discover the closest location based on CloudFront pop headers.

    Returns:
        str: The 3-character location code (e.g. "IAD")
    """
    discovery = HTTPHintLocationDiscovery(logger=logger)
    # Even though discover is synchronous, we keep this function async for future compatibility
    return discovery.discover()


async def join(
    call: Call, user_id: str = None, create=True, **kwargs
) -> ConnectionManager:
    """
    Connects to a call with webRTC, this method returns a connection manager object which can be used to send and receive events
    """

    # TODO: when we have the full flow and a good idea about all moving parts, we should extract a call manager class
    # that handles automatic re-connection based on retries and ws events

    logger.info("discovering location")
    with retry.Retry(max_retries=5, backoff_strategy=lambda _: 0.1):
        location = await discover_location()
    logger.info(f"discovered location: {location}")

    logger.info("join call - coordinator request")
    with retry.Retry(max_retries=5):
        join_call_response = await join_call_coordinator_request(
            call, user_id, create=create, **kwargs
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
