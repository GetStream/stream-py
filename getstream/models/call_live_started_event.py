from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from datetime import datetime
from getstream.models.call_response import CallResponse


@dataclass_json
@dataclass
class CallLiveStartedEvent:
    call: CallResponse = field(metadata=config(field_name="call"))
    call_cid: str = field(metadata=config(field_name="call_cid"))
    created_at: datetime = field(metadata=config(field_name="created_at"))
    type: str = field(metadata=config(field_name="type"))
