from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class BlockUserResponse:
    duration: str = field(metadata=config(field_name="duration"))
