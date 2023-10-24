# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.policy_request import PolicyRequest


@dataclass_json
@dataclass
class CreateChannelTypeRequest:
    name: str = field(metadata=config(field_name="name"))
    automod: str = field(metadata=config(field_name="automod"))
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    mutes: Optional[bool] = field(metadata=config(field_name="mutes"), default=None)
    automod_behavior: Optional[str] = field(
        metadata=config(field_name="automod_behavior"), default=None
    )
    connect_events: Optional[bool] = field(
        metadata=config(field_name="connect_events"), default=None
    )
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    max_message_length: Optional[int] = field(
        metadata=config(field_name="max_message_length"), default=None
    )
    search: Optional[bool] = field(metadata=config(field_name="search"), default=None)
    typing_events: Optional[bool] = field(
        metadata=config(field_name="typing_events"), default=None
    )
    custom_events: Optional[bool] = field(
        metadata=config(field_name="custom_events"), default=None
    )
    permissions: Optional[List[PolicyRequest]] = field(
        metadata=config(field_name="permissions"), default=None
    )
    push_notifications: Optional[bool] = field(
        metadata=config(field_name="push_notifications"), default=None
    )
    reactions: Optional[bool] = field(
        metadata=config(field_name="reactions"), default=None
    )
    commands: Optional[List[str]] = field(
        metadata=config(field_name="commands"), default=None
    )
    read_events: Optional[bool] = field(
        metadata=config(field_name="read_events"), default=None
    )
    replies: Optional[bool] = field(metadata=config(field_name="replies"), default=None)
    uploads: Optional[bool] = field(metadata=config(field_name="uploads"), default=None)
    url_enrichment: Optional[bool] = field(
        metadata=config(field_name="url_enrichment"), default=None
    )
    message_retention: Optional[str] = field(
        metadata=config(field_name="message_retention"), default=None
    )
