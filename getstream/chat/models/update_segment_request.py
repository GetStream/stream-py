# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.segment_updateable_fields_request import (
    SegmentUpdateableFieldsRequest,
)


@dataclass_json
@dataclass
class UpdateSegmentRequest:
    segment: SegmentUpdateableFieldsRequest = field(
        metadata=config(field_name="segment")
    )
