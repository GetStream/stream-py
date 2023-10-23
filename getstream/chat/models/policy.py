# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class Policy:
    name: str = field(metadata=config(field_name="name"))
    owner: bool = field(metadata=config(field_name="owner"))
    priority: int = field(metadata=config(field_name="priority"))
    resources: List[str] = field(metadata=config(field_name="resources"))
    roles: List[str] = field(metadata=config(field_name="roles"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    action: int = field(metadata=config(field_name="action"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
