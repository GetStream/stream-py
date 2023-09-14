from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class ListCallTypeResponse:
    duration: str = field(metadata=config(field_name="duration"))
    call_types: dict[str, CallTypeResponse] = field(
        metadata=config(field_name="call_types")
    )
