# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.thresholds_request import ThresholdsRequest
from getstream.chat.models.command_request import CommandRequest


@dataclass_json
@dataclass
class ChannelConfigWithInfoRequest:
    automod: str = field(metadata=config(field_name="automod"))
    max_message_length: Optional[int] = field(
        metadata=config(field_name="max_message_length"), default=None
    )
    quotes: Optional[bool] = field(metadata=config(field_name="quotes"), default=None)
    updated_at: Optional[datetime] = field(
        metadata=config(
            field_name="updated_at",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    url_enrichment: Optional[bool] = field(
        metadata=config(field_name="url_enrichment"), default=None
    )
    automod_thresholds: Optional[ThresholdsRequest] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
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
    read_events: Optional[bool] = field(
        metadata=config(field_name="read_events"), default=None
    )
    replies: Optional[bool] = field(metadata=config(field_name="replies"), default=None)
    search: Optional[bool] = field(metadata=config(field_name="search"), default=None)
    automod_behavior: Optional[str] = field(
        metadata=config(field_name="automod_behavior"), default=None
    )
    custom_events: Optional[bool] = field(
        metadata=config(field_name="custom_events"), default=None
    )
    mutes: Optional[bool] = field(metadata=config(field_name="mutes"), default=None)
    reactions: Optional[bool] = field(
        metadata=config(field_name="reactions"), default=None
    )
    uploads: Optional[bool] = field(metadata=config(field_name="uploads"), default=None)
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    push_notifications: Optional[bool] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    connect_events: Optional[bool] = field(
        metadata=config(field_name="connect_events"), default=None
    )
    message_retention: Optional[str] = field(
        metadata=config(field_name="message_retention"), default=None
    )
    reminders: Optional[bool] = field(
        metadata=config(field_name="reminders"), default=None
    )
    typing_events: Optional[bool] = field(
        metadata=config(field_name="typing_events"), default=None
    )
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    commands: Optional[List[CommandRequest]] = field(
        metadata=config(field_name="commands"), default=None
    )
