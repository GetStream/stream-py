from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from call_request import CallRequest


@dataclass_json
@dataclass
class GetOrCreateCallRequest:
    data: Optional[CallRequest] = field(
        metadata=config(field_name="data"), default=None
    )
    members_limit: Optional[int] = field(
        metadata=config(field_name="members_limit"), default=None
    )
    notify: Optional[bool] = field(metadata=config(field_name="notify"), default=None)
    ring: Optional[bool] = field(metadata=config(field_name="ring"), default=None)
