# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class BanRequest:
    target_user_id: str = field(metadata=config(field_name="target_user_id"))
    banned_by_id: Optional[str] = field(
        metadata=config(field_name="banned_by_id"), default=None
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    user: Optional[UserObjectRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    banned_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="banned_by"), default=None
    )
    ip_ban: Optional[bool] = field(metadata=config(field_name="ip_ban"), default=None)
    reason: Optional[str] = field(metadata=config(field_name="reason"), default=None)
    shadow: Optional[bool] = field(metadata=config(field_name="shadow"), default=None)
    timeout: Optional[int] = field(metadata=config(field_name="timeout"), default=None)
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
