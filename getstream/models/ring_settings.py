# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class RingSettings:
    auto_cancel_timeout_ms: int = field(
        metadata=config(field_name="auto_cancel_timeout_ms")
    )
    incoming_call_timeout_ms: int = field(
        metadata=config(field_name="incoming_call_timeout_ms")
    )
