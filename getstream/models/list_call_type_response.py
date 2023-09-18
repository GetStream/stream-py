from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict


@dataclass_json
@dataclass
class ListCallTypeResponse:
    duration: str = field(metadata=config(field_name="duration"))
    call_types: Dict[str, CallTypeResponse] = field(
        metadata=config(field_name="call_types")
    )
