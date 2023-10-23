# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.message import Message


@dataclass_json
@dataclass
class MessageWithPendingMetadataResponse:
    duration: str = field(metadata=config(field_name="duration"))
    message: Optional[Message] = field(
        metadata=config(field_name="message"), default=None
    )
    pending_message_metadata: Optional[Dict[str, str]] = field(
        metadata=config(field_name="pending_message_metadata"), default=None
    )
