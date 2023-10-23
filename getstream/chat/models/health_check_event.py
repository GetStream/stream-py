# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.own_user import OwnUser


@dataclass_json
@dataclass
class HealthCheckEvent:
    type: str = field(metadata=config(field_name="type"))
    cid: str = field(metadata=config(field_name="cid"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    me: Optional[OwnUser] = field(metadata=config(field_name="me"), default=None)
