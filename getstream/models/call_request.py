from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from member_request import MemberRequest
from call_settings_request import CallSettingsRequest
from user_request import UserRequest


@dataclass_json
@dataclass
class CallRequest:
    created_by: Optional[UserRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    created_by_id: Optional[str] = field(
        metadata=config(field_name="created_by_id"), default=None
    )
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    members: Optional[list[MemberRequest]] = field(
        metadata=config(field_name="members"), default=None
    )
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
    starts_at: Optional[str] = field(
        metadata=config(field_name="starts_at"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
