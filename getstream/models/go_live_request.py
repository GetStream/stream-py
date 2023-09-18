from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


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