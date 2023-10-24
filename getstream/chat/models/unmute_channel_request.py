# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class UnmuteChannelRequest:
    channel_cid: str = field(metadata=config(field_name="channel_cid"))
    channel_cids: List[str] = field(metadata=config(field_name="channel_cids"))
    expiration: Optional[int] = field(
        metadata=config(field_name="expiration"), default=None
    )
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
