from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_request import UserRequest


@dataclass_json
@dataclass
class CreateDeviceRequest:
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    push_provider: Optional[str] = field(
        metadata=config(field_name="push_provider"), default=None
    )
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