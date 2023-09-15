from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from member_response import MemberResponse
from member_response import MemberResponse
from own_capability import OwnCapability
from user_response import UserResponse
from call_response import CallResponse


@dataclass_json
@dataclass
class GetCallResponse:
    own_capabilities: list[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    blocked_users: list[UserResponse] = field(
        metadata=config(field_name="blocked_users")
    )
    call: CallResponse = field(metadata=config(field_name="call"))
    duration: str = field(metadata=config(field_name="duration"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
