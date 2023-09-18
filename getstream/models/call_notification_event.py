from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from datetime import datetime
from getstream.models.user_response import UserResponse
from getstream.models.call_response import CallResponse
from getstream.models.member_response import MemberResponse


@dataclass_json
@dataclass
class CallNotificationEvent:
    created_at: datetime = field(metadata=config(field_name="created_at"))
    members: List[MemberResponse] = field(metadata=config(field_name="members"))
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
