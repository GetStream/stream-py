# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from getstream.chat.models.attachment_request import AttachmentRequest


@dataclass_json
@dataclass
class CampaignUpdateableFieldsRequest:
    description: Optional[str] = field(
        metadata=config(field_name="description"), default=None
    )
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    segment_id: Optional[str] = field(
        metadata=config(field_name="segment_id"), default=None
    )
    sender_id: Optional[str] = field(
        metadata=config(field_name="sender_id"), default=None
    )
    text: Optional[str] = field(metadata=config(field_name="text"), default=None)
    attachments: Optional[List[AttachmentRequest]] = field(
        metadata=config(field_name="attachments"), default=None
    )
    channel_type: Optional[str] = field(
        metadata=config(field_name="channel_type"), default=None
    )
    defaults: Optional[Dict[str, str]] = field(
        metadata=config(field_name="defaults"), default=None
    )
