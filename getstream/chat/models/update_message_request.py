# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.message_request import MessageRequest


@dataclass_json
@dataclass
class UpdateMessageRequest:
    message: MessageRequest = field(metadata=config(field_name="message"))
    pending_message_metadata: Optional[Dict[str, str]] = field(
        metadata=config(field_name="pending_message_metadata"), default=None
    )
    skip_enrich_url: Optional[bool] = field(
        metadata=config(field_name="skip_enrich_url"), default=None
    )
