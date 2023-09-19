from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_response import MemberResponse
from getstream.models.own_capability import OwnCapability
from getstream.models.user_response import UserResponse
from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class GetOrCreateCallResponse:
    duration: str = field(metadata=config(field_name="duration"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    blocked_users: List[UserResponse] = field(
        metadata=config(field_name="blocked_users")
    )
    call: CallResponse = field(metadata=config(field_name="call"))
    created: bool = field(metadata=config(field_name="created"))
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
