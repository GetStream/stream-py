# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.user_request import UserRequest


@dataclass_json
@dataclass
class CreateDeviceRequest:
    push_provider_name: Optional[str] = field(
        metadata=config(field_name="push_provider_name"), default=None
    )
    user: Optional[UserRequest] = field(
        metadata=config(field_name="user"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
    voip_token: Optional[bool] = field(
        metadata=config(field_name="voip_token"), default=None
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    push_provider: Optional[str] = field(
        metadata=config(field_name="push_provider"), default=None
    )
