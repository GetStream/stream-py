# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class DeviceRequest:
    id: str = field(metadata=config(field_name="id"))
    push_provider: str = field(metadata=config(field_name="push_provider"))
    voip: Optional[bool] = field(metadata=config(field_name="voip"), default=None)
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    disabled: Optional[bool] = field(
        metadata=config(field_name="disabled"), default=None
    )
    disabled_reason: Optional[str] = field(
        metadata=config(field_name="disabled_reason"), default=None
    )
    push_provider_name: Optional[str] = field(
        metadata=config(field_name="push_provider_name"), default=None
    )
    user_id: Optional[str] = field(metadata=config(field_name="user_id"), default=None)
