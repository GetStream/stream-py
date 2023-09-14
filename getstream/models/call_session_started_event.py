from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_response import CallResponse


@dataclass_json
@dataclass
class CallSessionStartedEvent:
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: str = field(metadata=config(field_name="created_at"))
    session_id: str = field(metadata=config(field_name="session_id"))
    type: str = field(metadata=config(field_name="type"))
