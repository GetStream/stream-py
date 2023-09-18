from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_response import UserResponse
from call_response import CallResponse
from member_response import MemberResponse
from own_capability import OwnCapability


@dataclass_json
@dataclass
class CallStateResponseFields:
    blocked_users: list[UserResponse] = field(
        metadata=config(field_name="blocked_users")
    )
    call: CallResponse = field(metadata=config(field_name="call"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    own_capabilities: list[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
