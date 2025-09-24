"""
Data models for the RTC module
"""

from dataclasses import field as dc_field, dataclass
from typing import List, Optional, Dict, Any
from dataclasses_json import config as dc_config, DataClassJsonMixin

from getstream.models import CallRequest, CallResponse, MemberResponse


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
