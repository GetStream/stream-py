# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.thresholds import Thresholds
from getstream.chat.models.moderation_response import ModerationResponse


@dataclass_json
@dataclass
class MessageModerationResult:
    message_id: str = field(metadata=config(field_name="message_id"))
    user_bad_karma: bool = field(metadata=config(field_name="user_bad_karma"))
    action: str = field(metadata=config(field_name="action"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    user_karma: float = field(metadata=config(field_name="user_karma"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    moderation_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="moderation_thresholds"), default=None
    )
    blocked_word: Optional[str] = field(
        metadata=config(field_name="blocked_word"), default=None
    )
    blocklist_name: Optional[str] = field(
        metadata=config(field_name="blocklist_name"), default=None
    )
    ai_moderation_response: Optional[ModerationResponse] = field(
        metadata=config(field_name="ai_moderation_response"), default=None
    )
    moderated_by: Optional[str] = field(
        metadata=config(field_name="moderated_by"), default=None
    )
