from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.member_response import MemberResponse
from getstream.models.own_capability import OwnCapability
from getstream.models.user_response import UserResponse
from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class CallStateResponseFields:
    call: CallResponse = field(metadata=config(field_name="call"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
