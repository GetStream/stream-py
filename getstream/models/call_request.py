from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from getstream.models.user_request import UserRequest
from getstream.models.member_request import MemberRequest
from getstream.models.call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class CallRequest:
    created_by: Optional[UserRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    created_by_id: Optional[str] = field(
        metadata=config(field_name="created_by_id"), default=None
    )
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    members: Optional[List[MemberRequest]] = field(
        metadata=config(field_name="members"), default=None
    )
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
    starts_at: Optional[datetime] = field(
        metadata=config(field_name="starts_at"), default=None
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
