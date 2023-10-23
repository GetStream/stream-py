# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.command import Command
from getstream.chat.models.thresholds import Thresholds
from getstream.chat.models.policy_request_1 import PolicyRequest1


@dataclass_json
@dataclass
class ChannelTypeConfig:
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = field(metadata=config(field_name="name"))
    reactions: bool = field(metadata=config(field_name="reactions"))
    reminders: bool = field(metadata=config(field_name="reminders"))
    typing_events: bool = field(metadata=config(field_name="typing_events"))
    url_enrichment: bool = field(metadata=config(field_name="url_enrichment"))
    connect_events: bool = field(metadata=config(field_name="connect_events"))
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    message_retention: str = field(metadata=config(field_name="message_retention"))
    custom_events: bool = field(metadata=config(field_name="custom_events"))
    mutes: bool = field(metadata=config(field_name="mutes"))
    permissions: List[PolicyRequest1] = field(metadata=config(field_name="permissions"))
    push_notifications: bool = field(metadata=config(field_name="push_notifications"))
    automod: str = field(metadata=config(field_name="automod"))
    automod_behavior: str = field(metadata=config(field_name="automod_behavior"))
    quotes: bool = field(metadata=config(field_name="quotes"))
    search: bool = field(metadata=config(field_name="search"))
    uploads: bool = field(metadata=config(field_name="uploads"))
    max_message_length: int = field(metadata=config(field_name="max_message_length"))
    read_events: bool = field(metadata=config(field_name="read_events"))
    replies: bool = field(metadata=config(field_name="replies"))
    commands: List[Command] = field(metadata=config(field_name="commands"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    automod_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
