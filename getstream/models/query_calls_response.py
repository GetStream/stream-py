from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_state_response_fields import CallStateResponseFields


@dataclass_json
@dataclass
class QueryCallsResponse:
    calls: list[CallStateResponseFields] = field(metadata=config(field_name="calls"))
    duration: str = field(metadata=config(field_name="duration"))
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
