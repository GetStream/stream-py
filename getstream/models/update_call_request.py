# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.models.call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class UpdateCallRequest:
    custom: Optional[object] = field(metadata=config(field_name="custom"), default=None)
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
