# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.message_request import MessageRequest


@dataclass_json
@dataclass
class SendMessageRequest:
    message: MessageRequest = field(metadata=config(field_name="message"))
    force_moderation: Optional[bool] = field(
        metadata=config(field_name="force_moderation"), default=None
    )
    is_pending_message: Optional[bool] = field(
        metadata=config(field_name="is_pending_message"), default=None
    )
    keep_channel_hidden: Optional[bool] = field(
        metadata=config(field_name="keep_channel_hidden"), default=None
    )
    pending_message_metadata: Optional[Dict[str, str]] = field(
        metadata=config(field_name="pending_message_metadata"), default=None
    )
    skip_enrich_url: Optional[bool] = field(
        metadata=config(field_name="skip_enrich_url"), default=None
    )
    skip_push: Optional[bool] = field(
        metadata=config(field_name="skip_push"), default=None
    )
