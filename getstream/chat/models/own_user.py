# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_mute import UserMute
from getstream.chat.models.push_notification_settings import PushNotificationSettings
from getstream.chat.models.channel_mute import ChannelMute
from getstream.chat.models.device import Device


@dataclass_json
@dataclass
class OwnUser:
    channel_mutes: List[ChannelMute] = field(
        metadata=config(field_name="channel_mutes")
    )
    language: str = field(metadata=config(field_name="language"))
    unread_channels: int = field(metadata=config(field_name="unread_channels"))
    banned: bool = field(metadata=config(field_name="banned"))
    online: bool = field(metadata=config(field_name="online"))
    total_unread_count: int = field(metadata=config(field_name="total_unread_count"))
    devices: List[Device] = field(metadata=config(field_name="devices"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    unread_count: int = field(metadata=config(field_name="unread_count"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = field(metadata=config(field_name="id"))
    mutes: List[UserMute] = field(metadata=config(field_name="mutes"))
    role: str = field(metadata=config(field_name="role"))
    last_active: Optional[datetime] = field(
        metadata=config(
            field_name="last_active",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    latest_hidden_channels: Optional[List[str]] = field(
        metadata=config(field_name="latest_hidden_channels"), default=None
    )
    deactivated_at: Optional[datetime] = field(
        metadata=config(
            field_name="deactivated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    deleted_at: Optional[datetime] = field(
        metadata=config(
            field_name="deleted_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    invisible: Optional[bool] = field(
        metadata=config(field_name="invisible"), default=None
    )
    push_notifications: Optional[PushNotificationSettings] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    teams: Optional[List[str]] = field(
        metadata=config(field_name="teams"), default=None
    )
