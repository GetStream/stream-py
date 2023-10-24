# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.command import Command
from getstream.chat.models.thresholds import Thresholds


@dataclass_json
@dataclass
class ChannelConfigWithInfo:
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    mutes: bool = field(metadata=config(field_name="mutes"))
    search: bool = field(metadata=config(field_name="search"))
    url_enrichment: bool = field(metadata=config(field_name="url_enrichment"))
    commands: List[Command] = field(metadata=config(field_name="commands"))
    message_retention: str = field(metadata=config(field_name="message_retention"))
    push_notifications: bool = field(metadata=config(field_name="push_notifications"))
    quotes: bool = field(metadata=config(field_name="quotes"))
    reactions: bool = field(metadata=config(field_name="reactions"))
    read_events: bool = field(metadata=config(field_name="read_events"))
    reminders: bool = field(metadata=config(field_name="reminders"))
    typing_events: bool = field(metadata=config(field_name="typing_events"))
    connect_events: bool = field(metadata=config(field_name="connect_events"))
    uploads: bool = field(metadata=config(field_name="uploads"))
    replies: bool = field(metadata=config(field_name="replies"))
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    automod_behavior: str = field(metadata=config(field_name="automod_behavior"))
    custom_events: bool = field(metadata=config(field_name="custom_events"))
    max_message_length: int = field(metadata=config(field_name="max_message_length"))
    name: str = field(metadata=config(field_name="name"))
    automod: str = field(metadata=config(field_name="automod"))
    automod_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
