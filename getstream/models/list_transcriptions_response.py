# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.models.call_transcription import CallTranscription


@dataclass_json
@dataclass
class ListTranscriptionsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    transcriptions: List[CallTranscription] = field(
        metadata=config(field_name="transcriptions")
    )
