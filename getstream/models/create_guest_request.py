from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_request import UserRequest


@dataclass_json
@dataclass
class CreateGuestRequest:
    user: UserRequest = field(metadata=config(field_name="user"))
