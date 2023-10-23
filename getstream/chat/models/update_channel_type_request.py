# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.policy_request import PolicyRequest
from getstream.chat.models.thresholds_request import ThresholdsRequest


@dataclass_json
@dataclass
class UpdateChannelTypeRequest:
    automod: str = field(metadata=config(field_name="automod"))
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    max_message_length: Optional[int] = field(
        metadata=config(field_name="max_message_length"), default=None
    )
    reactions: Optional[bool] = field(
        metadata=config(field_name="reactions"), default=None
    )
    reminders: Optional[bool] = field(
        metadata=config(field_name="reminders"), default=None
    )
    search: Optional[bool] = field(metadata=config(field_name="search"), default=None)
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    automod_thresholds: Optional[ThresholdsRequest] = field(
        metadata=config(field_name="automod_thresholds"), default=None
    )
    quotes: Optional[bool] = field(metadata=config(field_name="quotes"), default=None)
    read_events: Optional[bool] = field(
        metadata=config(field_name="read_events"), default=None
    )
    typing_events: Optional[bool] = field(
        metadata=config(field_name="typing_events"), default=None
    )
    url_enrichment: Optional[bool] = field(
        metadata=config(field_name="url_enrichment"), default=None
    )
    name_from_path: Optional[str] = field(
        metadata=config(field_name="NameFromPath"), default=None
    )
    automod_behavior: Optional[str] = field(
        metadata=config(field_name="automod_behavior"), default=None
    )
    custom_events: Optional[bool] = field(
        metadata=config(field_name="custom_events"), default=None
    )
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    message_retention: Optional[str] = field(
        metadata=config(field_name="message_retention"), default=None
    )
    replies: Optional[bool] = field(metadata=config(field_name="replies"), default=None)
    connect_events: Optional[bool] = field(
        metadata=config(field_name="connect_events"), default=None
    )
    mutes: Optional[bool] = field(metadata=config(field_name="mutes"), default=None)
    permissions: Optional[List[PolicyRequest]] = field(
        metadata=config(field_name="permissions"), default=None
    )
    push_notifications: Optional[bool] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    uploads: Optional[bool] = field(metadata=config(field_name="uploads"), default=None)
    commands: Optional[List[str]] = field(
        metadata=config(field_name="commands"), default=None
    )
