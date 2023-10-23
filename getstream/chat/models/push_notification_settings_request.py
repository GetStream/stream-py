# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields


@dataclass_json
@dataclass
class PushNotificationSettingsRequest:
    disabled: Optional[bool] = field(
        metadata=config(field_name="disabled"), default=None
    )
    disabled_until: Optional[datetime] = field(
        metadata=config(
            field_name="disabled_until",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
