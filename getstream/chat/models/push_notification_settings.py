from dataclasses import dataclass, field
from typing import Optional
from marshmallow import fields
from datetime import datetime
from dateutil.parser import parse
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class PushNotificationSettings:
    disabled: bool = field(metadata=config(field_name="disabled"))
    disabled_until: Optional[datetime] = field(
        metadata=config(
            field_name="disabled_until",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
