from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from user_response import UserResponse


@dataclass_json
@dataclass
class ReactionResponse:
    type: str = field(metadata=config(field_name="type"))
    user: UserResponse = field(metadata=config(field_name="user"))
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    emoji_code: Optional[str] = field(
        metadata=config(field_name="emoji_code"), default=None
    )
