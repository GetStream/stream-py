"""
Coordinator API functions for Stream Video RTC.
"""

import logging
from typing import Optional

from getstream.base import StreamResponse
from getstream.models import CallRequest
from getstream.video.call import Call
from getstream.utils import build_body_dict

# Import the types we need from __init__ without creating circular imports
from getstream.video.rtc.models import JoinCallResponse

logger = logging.getLogger("getstream.video.rtc.coordinator")


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
