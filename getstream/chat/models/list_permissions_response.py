# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.permission import Permission


@dataclass_json
@dataclass
class ListPermissionsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    permissions: List[Permission] = field(metadata=config(field_name="permissions"))
