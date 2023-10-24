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
class UpdateChannelTypeResponse:
    push_notifications: bool = field(metadata=config(field_name="push_notifications"))
    typing_events: bool = field(metadata=config(field_name="typing_events"))
    connect_events: bool = field(metadata=config(field_name="connect_events"))
    reactions: bool = field(metadata=config(field_name="reactions"))
    commands: List[str] = field(metadata=config(field_name="commands"))
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
    duration: str = field(metadata=config(field_name="duration"))
    max_message_length: int = field(metadata=config(field_name="max_message_length"))
    name: str = field(metadata=config(field_name="name"))
    automod: str = field(metadata=config(field_name="automod"))
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    read_events: bool = field(metadata=config(field_name="read_events"))
    replies: bool = field(metadata=config(field_name="replies"))
    url_enrichment: bool = field(metadata=config(field_name="url_enrichment"))
    search: bool = field(metadata=config(field_name="search"))
    permissions: List[PolicyRequest1] = field(metadata=config(field_name="permissions"))
    quotes: bool = field(metadata=config(field_name="quotes"))
    automod_behavior: str = field(metadata=config(field_name="automod_behavior"))
    custom_events: bool = field(metadata=config(field_name="custom_events"))
    reminders: bool = field(metadata=config(field_name="reminders"))
    uploads: bool = field(metadata=config(field_name="uploads"))
    message_retention: str = field(metadata=config(field_name="message_retention"))
    mutes: bool = field(metadata=config(field_name="mutes"))
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    automod_thresholds: Optional[Thresholds] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
