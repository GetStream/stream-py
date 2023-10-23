# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class GuestRequest:
    user: UserObjectRequest = field(metadata=config(field_name="user"))
