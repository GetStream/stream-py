# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class GoLiveRequest:
    start_hls: Optional[bool] = field(
        metadata=config(field_name="start_hls"), default=None
    )
    start_recording: Optional[bool] = field(
        metadata=config(field_name="start_recording"), default=None
    )
    start_transcription: Optional[bool] = field(
        metadata=config(field_name="start_transcription"), default=None
    )
    transcription_storage_name: Optional[str] = field(
        metadata=config(field_name="transcription_storage_name"), default=None
    )
    recording_storage_name: Optional[str] = field(
        metadata=config(field_name="recording_storage_name"), default=None
    )
