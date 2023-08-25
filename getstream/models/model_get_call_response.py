from dataclasses import dataclass
from typing import List, Optional
from .model_call_response import CallResponse
from .model_member_response import MemberResponse
from .model_own_capability import OwnCapability

from .model_user_response import UserResponse



@dataclass
class GetCallResponse:
    blocked_users: List[UserResponse]
    call: CallResponse
    duration: str
    members: List[MemberResponse]
    membership: Optional[MemberResponse]
    own_capabilities: List[OwnCapability]
