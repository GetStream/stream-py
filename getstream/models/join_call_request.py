from dataclasses import dataclass, field
from typing import Optional
from typing import Optional
from dataclasses_json import config, dataclass_json
from call_request import CallRequest


@dataclass_json
@dataclass
class JoinCallRequest:
    location: str = field(metadata=config(field_name="location"))
    members_limit: Optional[int] = field(
        metadata=config(field_name="members_limit"), default=None
    )
    migrating_from: Optional[str] = field(
        metadata=config(field_name="migrating_from"), default=None
    )
    notify: Optional[bool] = field(metadata=config(field_name="notify"), default=None)
    ring: Optional[bool] = field(metadata=config(field_name="ring"), default=None)
    create: Optional[bool] = field(metadata=config(field_name="create"), default=None)
    data: Optional[CallRequest] = field(
        metadata=config(field_name="data"), default=None
    )
