# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.flag_message_details import FlagMessageDetails
from getstream.chat.models.message_moderation_result import MessageModerationResult


@dataclass_json
@dataclass
class AutomodDetails:
    action: Optional[str] = field(metadata=config(field_name="action"), default=None)
    image_labels: Optional[List[str]] = field(
        metadata=config(field_name="image_labels"), default=None
    )
    message_details: Optional[FlagMessageDetails] = field(
        metadata=config(field_name="message_details"), default=None
    )
    original_message_type: Optional[str] = field(
        metadata=config(field_name="original_message_type"), default=None
    )
    result: Optional[MessageModerationResult] = field(
        metadata=config(field_name="result"), default=None
    )
