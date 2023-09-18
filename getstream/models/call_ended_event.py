from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from getstream.models.call_response import CallResponse
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class CallEndedEvent:
    type: str = field(metadata=config(field_name="type"))
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    user: Optional[UserResponse] = field(
        metadata=config(field_name="user"), default=None
    )
