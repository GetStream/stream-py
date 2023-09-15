from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_response import UserResponse
from own_capability import OwnCapability


@dataclass_json
@dataclass
class UpdatedCallPermissionsEvent:
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    own_capabilities: list[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
