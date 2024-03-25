# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.call_request import CallRequest


@dataclass_json
@dataclass
class GetOrCreateCallRequest:
    members_limit: Optional[int] = field(
        metadata=config(field_name="members_limit"), default=None
    )
    notify: Optional[bool] = field(metadata=config(field_name="notify"), default=None)
    ring: Optional[bool] = field(metadata=config(field_name="ring"), default=None)
    data: Optional[CallRequest] = field(
        metadata=config(field_name="data"), default=None
    )
