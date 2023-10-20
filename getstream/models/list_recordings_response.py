# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.call_recording import CallRecording


@dataclass_json
@dataclass
class ListRecordingsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    recordings: List[CallRecording] = field(metadata=config(field_name="recordings"))
