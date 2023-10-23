# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_mute_request import UserMuteRequest
from getstream.chat.models.channel_mute_request import ChannelMuteRequest
from getstream.chat.models.device_request import DeviceRequest
from getstream.chat.models.push_notification_settings_request import (
    PushNotificationSettingsRequest,
)


@dataclass_json
@dataclass
class OwnUserRequest:
    channel_mutes: Optional[List[ChannelMuteRequest]] = field(
        metadata=config(field_name="channel_mutes"), default=None
    )
    devices: Optional[List[DeviceRequest]] = field(
        metadata=config(field_name="devices"), default=None
    )
    invisible: Optional[bool] = field(
        metadata=config(field_name="invisible"), default=None
    )
    language: Optional[str] = field(
        metadata=config(field_name="language"), default=None
    )
    online: Optional[bool] = field(metadata=config(field_name="online"), default=None)
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    unread_count: Optional[int] = field(
        metadata=config(field_name="unread_count"), default=None
    )
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
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
    push_notifications: Optional[PushNotificationSettingsRequest] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    teams: Optional[List[str]] = field(
        metadata=config(field_name="teams"), default=None
    )
    banned: Optional[bool] = field(metadata=config(field_name="banned"), default=None)
    created_at: Optional[datetime] = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    latest_hidden_channels: Optional[List[str]] = field(
        metadata=config(field_name="latest_hidden_channels"), default=None
    )
    mutes: Optional[List[UserMuteRequest]] = field(
        metadata=config(field_name="mutes"), default=None
    )
    total_unread_count: Optional[int] = field(
        metadata=config(field_name="total_unread_count"), default=None
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
    last_active: Optional[datetime] = field(
        metadata=config(
            field_name="last_active",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    unread_channels: Optional[int] = field(
        metadata=config(field_name="unread_channels"), default=None
    )
