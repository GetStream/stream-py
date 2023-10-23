# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class UpdateUsersRequest:
    users: Dict[str, UserObjectRequest] = field(metadata=config(field_name="users"))
