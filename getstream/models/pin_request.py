from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class PinRequest:
    user_id: str = field(metadata=config(field_name="user_id"))
    session_id: str = field(metadata=config(field_name="session_id"))
