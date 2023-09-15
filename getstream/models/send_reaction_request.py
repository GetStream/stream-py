from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class SendReactionRequest:
    type: str = field(metadata=config(field_name="type"))
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    emoji_code: Optional[str] = field(
        metadata=config(field_name="emoji_code"), default=None
    )
