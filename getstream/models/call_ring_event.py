from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_response import CallResponse
from member_response import MemberResponse
from user_response import UserResponse


@dataclass_json
@dataclass
class CallRingEvent:
    created_at: str = field(metadata=config(field_name="created_at"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
