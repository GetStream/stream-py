from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from datetime import datetime
from marshmallow import fields
from getstream.models.call_settings_request import CallSettingsRequest


@dataclass_json
@dataclass
class UpdateCallRequest:
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    settings_override: Optional[CallSettingsRequest] = field(
        metadata=config(field_name="settings_override"), default=None
    )
    starts_at: Optional[datetime] = field(
        metadata=config(
            field_name="starts_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
