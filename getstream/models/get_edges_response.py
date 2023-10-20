# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.edge_response import EdgeResponse


@dataclass_json
@dataclass
class GetEdgesResponse:
    duration: str = field(metadata=config(field_name="duration"))
    edges: List[EdgeResponse] = field(metadata=config(field_name="edges"))
