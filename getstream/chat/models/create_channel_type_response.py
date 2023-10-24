# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.policy_request_1 import PolicyRequest1
from getstream.chat.models.thresholds import Thresholds


@dataclass_json
@dataclass
class CreateChannelTypeResponse:
    updated_at: datetime = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = field(metadata=config(field_name="custom_events"))
    max_message_length: int = field(metadata=config(field_name="max_message_length"))
    message_retention: str = field(metadata=config(field_name="message_retention"))
    search: bool = field(metadata=config(field_name="search"))
    uploads: bool = field(metadata=config(field_name="uploads"))
    connect_events: bool = field(metadata=config(field_name="connect_events"))
    replies: bool = field(metadata=config(field_name="replies"))
    push_notifications: bool = field(metadata=config(field_name="push_notifications"))
    commands: List[str] = field(metadata=config(field_name="commands"))
    duration: str = field(metadata=config(field_name="duration"))
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    mutes: bool = field(metadata=config(field_name="mutes"))
    read_events: bool = field(metadata=config(field_name="read_events"))
    automod_behavior: str = field(metadata=config(field_name="automod_behavior"))
    permissions: List[PolicyRequest1] = field(metadata=config(field_name="permissions"))
    reactions: bool = field(metadata=config(field_name="reactions"))
    url_enrichment: bool = field(metadata=config(field_name="url_enrichment"))
    name: str = field(metadata=config(field_name="name"))
    quotes: bool = field(metadata=config(field_name="quotes"))
    reminders: bool = field(metadata=config(field_name="reminders"))
    typing_events: bool = field(metadata=config(field_name="typing_events"))
    automod: str = field(metadata=config(field_name="automod"))
    created_at: datetime = field(
        metadata=config(
            field_name="created_at",
            encoder=lambda d: d.isoformat(),
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    automod_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
