from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class UnpinRequest:
    session_id: str = field(metadata=config(field_name="session_id"))
    user_id: str = field(metadata=config(field_name="user_id"))
