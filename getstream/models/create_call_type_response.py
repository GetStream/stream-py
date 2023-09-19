from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json
from marshmallow import fields
from typing import List, Dict
from datetime import datetime
from getstream.models.call_settings_response import CallSettingsResponse
from getstream.models.notification_settings import NotificationSettings


@dataclass_json
@dataclass
class CreateCallTypeResponse:
    notification_settings: NotificationSettings = field(
        metadata=config(field_name="notification_settings")
    )
    settings: CallSettingsResponse = field(metadata=config(field_name="settings"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=datetime.isoformat,
            decoder=datetime.fromisoformat,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = field(metadata=config(field_name="duration"))
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    name: str = field(metadata=config(field_name="name"))
