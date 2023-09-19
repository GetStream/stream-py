from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.device import Device


@dataclass_json
@dataclass
class OwnUserResponse:
    role: str = field(metadata=config(field_name="role"))
    teams: List[str] = field(metadata=config(field_name="teams"))
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
    devices: List[Device] = field(metadata=config(field_name="devices"))
    custom: Dict[str, object] = field(metadata=config(field_name="custom"))
    id: str = field(metadata=config(field_name="id"))
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
