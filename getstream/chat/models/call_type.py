# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.notification_settings import NotificationSettings
from getstream.chat.models.call_settings import CallSettings


@dataclass_json
@dataclass
class CallType:
    app_pk: int = field(metadata=config(field_name="AppPK"))
    created_at: datetime = field(
        metadata=config(
            field_name="CreatedAt",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = field(metadata=config(field_name="Name"))
    pk: int = field(metadata=config(field_name="PK"))
    updated_at: datetime = field(
        metadata=config(
            field_name="UpdatedAt",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    notification_settings: Optional[NotificationSettings] = field(
        metadata=config(field_name="NotificationSettings"), default=None
    )
    settings: Optional[CallSettings] = field(
        metadata=config(field_name="Settings"), default=None
    )
