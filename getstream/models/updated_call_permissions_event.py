# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.own_capability import OwnCapability
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class UpdatedCallPermissionsEvent:
    user: UserResponse = field(metadata=config(field_name="user"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    own_capabilities: List[OwnCapability] = field(
        metadata=config(field_name="own_capabilities")
    )
    type: str = field(metadata=config(field_name="type"))
