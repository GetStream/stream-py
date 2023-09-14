from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from user_response import UserResponse
from call_response import CallResponse
from member_response import MemberResponse


@dataclass_json
@dataclass
class CallNotificationEvent:
    created_at: str = field(metadata=config(field_name="created_at"))
    members: list[MemberResponse] = field(metadata=config(field_name="members"))
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
