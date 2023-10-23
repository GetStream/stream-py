# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.role import Role


@dataclass_json
@dataclass
class CreateRoleResponse:
    duration: str = field(metadata=config(field_name="duration"))
    role: Role = field(metadata=config(field_name="role"))
