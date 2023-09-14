from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_response import CallResponse
from user_response import UserResponse


@dataclass_json
@dataclass
class CallEndedEvent:
    created_at: str = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    user: Optional[UserResponse] = field(
        metadata=config(field_name="user"), default=None
    )
