# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class SegmentDataRequest:
    filter: Dict[str, object] = field(metadata=config(field_name="filter"))
    name: str = field(metadata=config(field_name="name"))
    type: str = field(metadata=config(field_name="type"))
    description: Optional[str] = field(
        metadata=config(field_name="description"), default=None
    )
