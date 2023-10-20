# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class UpdateUserPermissionsRequest:
    user_id: str = field(metadata=config(field_name="user_id"))
    grant_permissions: Optional[List[str]] = field(
        metadata=config(field_name="grant_permissions"), default=None
    )
    revoke_permissions: Optional[List[str]] = field(
        metadata=config(field_name="revoke_permissions"), default=None
    )
