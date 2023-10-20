# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict
from getstream.models.call_type_response import CallTypeResponse


@dataclass_json
@dataclass
class ListCallTypeResponse:
    call_types: Dict[str, CallTypeResponse] = field(
        metadata=config(field_name="call_types")
    )
    duration: str = field(metadata=config(field_name="duration"))
