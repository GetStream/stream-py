# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.pagination_params_request import PaginationParamsRequest
from getstream.chat.models.message_pagination_params_request import (
    MessagePaginationParamsRequest,
)
from getstream.chat.models.channel_request import ChannelRequest


@dataclass_json
@dataclass
class ChannelGetOrCreateRequest:
    client_id: Optional[str] = field(
        metadata=config(field_name="client_id"), default=None
    )
    data: Optional[ChannelRequest] = field(
        metadata=config(field_name="data"), default=None
    )
    messages: Optional[MessagePaginationParamsRequest] = field(
        metadata=config(field_name="messages"), default=None
    )
    state: Optional[bool] = field(metadata=config(field_name="state"), default=None)
    watch: Optional[bool] = field(metadata=config(field_name="watch"), default=None)
    watchers: Optional[PaginationParamsRequest] = field(
        metadata=config(field_name="watchers"), default=None
    )
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
    )
    hide_for_creator: Optional[bool] = field(
        metadata=config(field_name="hide_for_creator"), default=None
    )
    members: Optional[PaginationParamsRequest] = field(
        metadata=config(field_name="members"), default=None
    )
    presence: Optional[bool] = field(
        metadata=config(field_name="presence"), default=None
    )
