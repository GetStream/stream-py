from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.call_state_response_fields import CallStateResponseFields


@dataclass_json
@dataclass
class QueryCallsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    calls: List[CallStateResponseFields] = field(metadata=config(field_name="calls"))
    next: Optional[str] = field(metadata=config(field_name="next"), default=None)
    prev: Optional[str] = field(metadata=config(field_name="prev"), default=None)
