# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.device import Device


@dataclass_json
@dataclass
class OwnUserResponse:
    role: str = field(metadata=config(field_name="role"))
    teams: List[str] = field(metadata=config(field_name="teams"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    devices: List[Device] = field(metadata=config(field_name="devices"))
    id: str = field(metadata=config(field_name="id"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
