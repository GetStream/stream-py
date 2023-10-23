# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.segment import Segment


@dataclass_json
@dataclass
class CreateSegmentResponse:
    duration: str = field(metadata=config(field_name="duration"))
    segment: Optional[Segment] = field(
        metadata=config(field_name="segment"), default=None
    )
