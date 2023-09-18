from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class SortParamRequest:
    field: Optional[str] = field(metadata=config(field_name="field"), default=None)
    direction: Optional[int] = field(
        metadata=config(field_name="direction"), default=None
    )
