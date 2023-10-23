# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class DeactivateUsersRequest:
    user_ids: List[str] = field(metadata=config(field_name="user_ids"))
    created_by_id: Optional[str] = field(
        metadata=config(field_name="created_by_id"), default=None
    )
    mark_messages_deleted: Optional[bool] = field(
        metadata=config(field_name="mark_messages_deleted"), default=None
    )
