# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.sort_param_request import SortParamRequest
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class QueryChannelsRequest:
    sort: List[SortParamRequest] = field(metadata=config(field_name="sort"))
    client_id: Optional[str] = field(
        metadata=config(field_name="client_id"), default=None
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    message_limit: Optional[int] = field(
        metadata=config(field_name="message_limit"), default=None
    )
    presence: Optional[bool] = field(
        metadata=config(field_name="presence"), default=None
    )
    state: Optional[bool] = field(metadata=config(field_name="state"), default=None)
    watch: Optional[bool] = field(metadata=config(field_name="watch"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    connection_id: Optional[str] = field(
        metadata=config(field_name="connection_id"), default=None
    )
    filter_conditions: Optional[Dict[str, object]] = field(
        metadata=config(field_name="filter_conditions"), default=None
    )
    member_limit: Optional[int] = field(
        metadata=config(field_name="member_limit"), default=None
    )
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
