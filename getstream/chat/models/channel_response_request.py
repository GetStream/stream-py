# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.channel_config_with_info_request import (
    ChannelConfigWithInfoRequest,
)
from getstream.chat.models.channel_member_request import ChannelMemberRequest
from getstream.chat.models.user_object_request import UserObjectRequest


@dataclass_json
@dataclass
class ChannelResponseRequest:
    cid: Optional[str] = field(metadata=config(field_name="cid"), default=None)
    config: Optional[ChannelConfigWithInfoRequest] = field(
        metadata=config(field_name="config"), default=None
    )
    id: Optional[str] = field(metadata=config(field_name="id"), default=None)
    type: Optional[str] = field(metadata=config(field_name="type"), default=None)
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    created_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="created_by"), default=None
    )
    member_count: Optional[int] = field(
        metadata=config(field_name="member_count"), default=None
    )
    members: Optional[List[ChannelMemberRequest]] = field(
        metadata=config(field_name="members"), default=None
    )
    mute_expires_at: Optional[datetime] = field(
        metadata=config(
            field_name="mute_expires_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    muted: Optional[bool] = field(metadata=config(field_name="muted"), default=None)
    truncated_by: Optional[UserObjectRequest] = field(
        metadata=config(field_name="truncated_by"), default=None
    )
    truncated_at: Optional[datetime] = field(
        metadata=config(
            field_name="truncated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    auto_translation_language: Optional[str] = field(
        metadata=config(field_name="auto_translation_language"), default=None
    )
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
    frozen: Optional[bool] = field(metadata=config(field_name="frozen"), default=None)
    hidden: Optional[bool] = field(metadata=config(field_name="hidden"), default=None)
    last_message_at: Optional[datetime] = field(
        metadata=config(
            field_name="last_message_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    team: Optional[str] = field(metadata=config(field_name="team"), default=None)
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
    )
    cooldown: Optional[int] = field(
        metadata=config(field_name="cooldown"), default=None
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
    hide_messages_before: Optional[datetime] = field(
        metadata=config(
            field_name="hide_messages_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    own_capabilities: Optional[List[str]] = field(
        metadata=config(field_name="own_capabilities"), default=None
    )
