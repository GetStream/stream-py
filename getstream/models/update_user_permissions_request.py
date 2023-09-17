from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class UpdateUserPermissionsRequest:
    user_id: str = field(metadata=config(field_name="user_id"))
    grant_permissions: Optional[list[str]] = field(
        metadata=config(field_name="grant_permissions"), default=None
    )
    revoke_permissions: Optional[list[str]] = field(
        metadata=config(field_name="revoke_permissions"), default=None
    )
