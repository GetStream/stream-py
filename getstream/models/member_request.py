from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class MemberRequest:
    user_id: str = field(metadata=config(field_name="user_id"))
    custom: Optional[dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)