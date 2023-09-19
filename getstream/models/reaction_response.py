from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.models.user_response import UserResponse


@dataclass_json
@dataclass
class ReactionResponse:
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    emoji_code: Optional[str] = field(
        metadata=config(field_name="emoji_code"), default=None
    )
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
