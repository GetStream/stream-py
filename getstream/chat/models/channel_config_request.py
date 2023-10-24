# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional


@dataclass_json
@dataclass
class ChannelConfigRequest:
    url_enrichment: Optional[bool] = field(
        metadata=config(field_name="url_enrichment"), default=None
    )
    reactions: Optional[bool] = field(
        metadata=config(field_name="reactions"), default=None
    )
    blocklist_behavior: Optional[str] = field(
        metadata=config(field_name="blocklist_behavior"), default=None
    )
    commands: Optional[List[str]] = field(
        metadata=config(field_name="commands"), default=None
    )
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    max_message_length: Optional[int] = field(
        metadata=config(field_name="max_message_length"), default=None
    )
    quotes: Optional[bool] = field(metadata=config(field_name="quotes"), default=None)
    replies: Optional[bool] = field(metadata=config(field_name="replies"), default=None)
    typing_events: Optional[bool] = field(
        metadata=config(field_name="typing_events"), default=None
    )
    blocklist: Optional[str] = field(
        metadata=config(field_name="blocklist"), default=None
    )
    uploads: Optional[bool] = field(metadata=config(field_name="uploads"), default=None)
