from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from edge_response import EdgeResponse


@dataclass_json
@dataclass
class GetEdgesResponse:
    duration: str = field(metadata=config(field_name="duration"))
    edges: list[EdgeResponse] = field(metadata=config(field_name="edges"))
