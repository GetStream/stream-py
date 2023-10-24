# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.user_object import UserObject
from getstream.chat.models.flag_feedback import FlagFeedback
from getstream.chat.models.message import Message
from getstream.chat.models.message_moderation_result import MessageModerationResult


@dataclass_json
@dataclass
class MessageFlag:
    created_by_automod: bool = field(metadata=config(field_name="created_by_automod"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    approved_at: Optional[datetime] = field(
        metadata=config(
            field_name="approved_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    moderation_feedback: Optional[FlagFeedback] = field(
        metadata=config(field_name="moderation_feedback"), default=None
    )
    rejected_at: Optional[datetime] = field(
        metadata=config(
            field_name="rejected_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    reviewed_at: Optional[datetime] = field(
        metadata=config(
            field_name="reviewed_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    reviewed_by: Optional[UserObject] = field(
        metadata=config(field_name="reviewed_by"), default=None
    )
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
    moderation_result: Optional[MessageModerationResult] = field(
        metadata=config(field_name="moderation_result"), default=None
    )
    user: Optional[UserObject] = field(metadata=config(field_name="user"), default=None)
