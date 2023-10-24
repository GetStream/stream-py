# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class SendReactionRequest:
    type: str = field(metadata=config(field_name="type"))
    emoji_code: Optional[str] = field(
        metadata=config(field_name="emoji_code"), default=None
    )
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
