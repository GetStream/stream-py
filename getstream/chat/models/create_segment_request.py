# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.segment_data_request import SegmentDataRequest


@dataclass_json
@dataclass
class CreateSegmentRequest:
    segment: SegmentDataRequest = field(metadata=config(field_name="segment"))
