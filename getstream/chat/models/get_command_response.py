# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class GetCommandResponse:
    args: str = field(metadata=config(field_name="args"))
    description: str = field(metadata=config(field_name="description"))
    duration: str = field(metadata=config(field_name="duration"))
    name: str = field(metadata=config(field_name="name"))
    set: str = field(metadata=config(field_name="set"))
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
