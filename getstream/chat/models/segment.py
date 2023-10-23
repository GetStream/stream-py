# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class Segment:
    filter: Dict[str, object] = field(metadata=config(field_name="filter"))
    in_use: bool = field(metadata=config(field_name="in_use"))
    type: str = field(metadata=config(field_name="type"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    description: str = field(metadata=config(field_name="description"))
    size: int = field(metadata=config(field_name="size"))
    status: str = field(metadata=config(field_name="status"))
    id: str = field(metadata=config(field_name="id"))
    name: str = field(metadata=config(field_name="name"))
