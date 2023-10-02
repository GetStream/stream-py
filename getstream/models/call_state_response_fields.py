from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.call_response import CallResponse
from getstream.models.member_response import MemberResponse
from getstream.models.own_capability import OwnCapability


@dataclass_json
@dataclass
class CallStateResponseFields:
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    call: CallResponse = field(metadata=config(field_name="call"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    membership: Optional[MemberResponse] = field(
        metadata=config(field_name="membership"), default=None
    )
