from dataclasses import dataclass
from typing import Optional, List, Dict

from datetime import datetime
from .model_call_settings_request import CallSettingsRequest

from .model_member_request import MemberRequest
from .model_user_request import UserRequest


@dataclass
class CallRequest:
    created_by: Optional[UserRequest] = None
    created_by_id: Optional[str] = None
    custom: Optional[Dict[str, object]] = None
    members: Optional[List[MemberRequest]] = None
    settings_override: Optional[CallSettingsRequest] = None
    starts_at: Optional[datetime] = None
    team: Optional[str] = None
