# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.call_request import CallRequest


@dataclass_json
@dataclass
class JoinCallRequest:
    location: str = field(metadata=config(field_name="location"))
    create: Optional[bool] = field(metadata=config(field_name="create"), default=None)
    data: Optional[CallRequest] = field(
        metadata=config(field_name="data"), default=None
    )
    members_limit: Optional[int] = field(
        metadata=config(field_name="members_limit"), default=None
    )
    migrating_from: Optional[str] = field(
        metadata=config(field_name="migrating_from"), default=None
    )
    notify: Optional[bool] = field(metadata=config(field_name="notify"), default=None)
    ring: Optional[bool] = field(metadata=config(field_name="ring"), default=None)
