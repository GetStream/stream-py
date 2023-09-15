from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class CallParticipantResponse:
    role: str = field(metadata=config(field_name="role"))
    user: UserResponse = field(metadata=config(field_name="user"))
    user_session_id: str = field(metadata=config(field_name="user_session_id"))
    joined_at: str = field(metadata=config(field_name="joined_at"))
