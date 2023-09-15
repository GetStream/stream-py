from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_response import CallResponse
from member_response import MemberResponse
from member_response import MemberResponse
from own_capability import OwnCapability
from user_response import UserResponse


@dataclass_json
@dataclass
class GetOrCreateCallResponse:
    created: bool = field(metadata=config(field_name="created"))
    duration: str = field(metadata=config(field_name="duration"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    own_capabilities: list[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    blocked_users: list[UserResponse] = field(
        metadata=config(field_name="blocked_users")
    )
    call: CallResponse = field(metadata=config(field_name="call"))
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
