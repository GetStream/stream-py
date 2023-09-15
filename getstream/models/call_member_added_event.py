from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from member_response import MemberResponse
from call_response import CallResponse


@dataclass_json
@dataclass
class CallMemberAddedEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    type: str = field(metadata=config(field_name="type"))
    call: CallResponse = field(metadata=config(field_name="call"))
