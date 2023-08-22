from dataclasses import dataclass
from typing import List, Optional

from models.model_call_member_removed_event import CallResponse
from models.model_call_notification_event import MemberResponse, UserResponse
from models.model_own_capability import OwnCapability


@dataclass
class CallStateResponseFields:
    blocked_users: List[UserResponse]
    call: CallResponse
    members: List[MemberResponse]
    membership: Optional[MemberResponse]
    own_capabilities: List[OwnCapability]
