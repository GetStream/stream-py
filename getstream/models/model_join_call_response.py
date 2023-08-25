from dataclasses import dataclass
from typing import List, Optional
from .model_call_response import CallResponse

from .model_call_notification_event import MemberResponse, UserResponse
from .model_credentials import Credentials
from .model_own_capability import OwnCapability


@dataclass
class JoinCallResponse:
    blocked_users: List[UserResponse]
    call: CallResponse
    created: bool
    credentials: Credentials
    duration: str
    members: List[MemberResponse]
    membership: Optional[MemberResponse]
    own_capabilities: List[OwnCapability]
