from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class CreateGuestResponse:
    user: UserResponse = field(metadata=config(field_name="user"))
    access_token: str = field(metadata=config(field_name="access_token"))
    duration: str = field(metadata=config(field_name="duration"))
