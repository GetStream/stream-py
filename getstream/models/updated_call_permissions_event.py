from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from datetime import datetime
from getstream.models.own_capability import OwnCapability
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class UpdatedCallPermissionsEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
