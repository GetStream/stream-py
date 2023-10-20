# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.call_state_response_fields import CallStateResponseFields


@dataclass_json
@dataclass
class QueryCallsResponse:
    calls: List[CallStateResponseFields] = field(metadata=config(field_name="calls"))
    duration: str = field(metadata=config(field_name="duration"))
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
