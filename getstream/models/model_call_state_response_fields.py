from dataclasses import dataclass
from typing import List, Optional

from .model_call_response import CallResponse
from .model_call_notification_event import MemberResponse, UserResponse
from .model_own_capability import OwnCapability


@dataclass
class CallStateResponseFields:
    blocked_users: List[UserResponse]
    call: CallResponse
    members: List[MemberResponse]
    membership: Optional[MemberResponse]
    own_capabilities: List[OwnCapability]
