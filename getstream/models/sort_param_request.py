from dataclasses import dataclass
from dataclasses_json import dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class SortParamRequest:
    field: Optional[str] = None
    direction: Optional[int] = None
