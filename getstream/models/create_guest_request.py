# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.models.user_request import UserRequest


@dataclass_json
@dataclass
class CreateGuestRequest:
    user: UserRequest = field(metadata=config(field_name="user"))
