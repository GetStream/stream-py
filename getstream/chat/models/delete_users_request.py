# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class DeleteUsersRequest:
    user_ids: List[str] = field(metadata=config(field_name="user_ids"))
    conversations: Optional[str] = field(
        metadata=config(field_name="conversations"), default=None
    )
    messages: Optional[str] = field(
        metadata=config(field_name="messages"), default=None
    )
    new_channel_owner_id: Optional[str] = field(
        metadata=config(field_name="new_channel_owner_id"), default=None
    )
    user: Optional[str] = field(metadata=config(field_name="user"), default=None)
