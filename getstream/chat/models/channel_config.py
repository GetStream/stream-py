# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.thresholds import Thresholds


@dataclass_json
@dataclass
class ChannelConfig:
    search: bool = field(metadata=config(field_name="search"))
    url_enrichment: bool = field(metadata=config(field_name="url_enrichment"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = field(metadata=config(field_name="custom_events"))
    reactions: bool = field(metadata=config(field_name="reactions"))
    reminders: bool = field(metadata=config(field_name="reminders"))
    automod_behavior: str = field(metadata=config(field_name="automod_behavior"))
    commands: List[str] = field(metadata=config(field_name="commands"))
    max_message_length: int = field(metadata=config(field_name="max_message_length"))
    push_notifications: bool = field(metadata=config(field_name="push_notifications"))
    typing_events: bool = field(metadata=config(field_name="typing_events"))
    message_retention: str = field(metadata=config(field_name="message_retention"))
    name: str = field(metadata=config(field_name="name"))
    uploads: bool = field(metadata=config(field_name="uploads"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    automod: str = field(metadata=config(field_name="automod"))
    connect_events: bool = field(metadata=config(field_name="connect_events"))
    mutes: bool = field(metadata=config(field_name="mutes"))
    quotes: bool = field(metadata=config(field_name="quotes"))
    read_events: bool = field(metadata=config(field_name="read_events"))
    replies: bool = field(metadata=config(field_name="replies"))
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    automod_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
