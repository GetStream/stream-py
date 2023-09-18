from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class UnblockUserRequest:
    user_id: str = field(metadata=config(field_name="user_id"))