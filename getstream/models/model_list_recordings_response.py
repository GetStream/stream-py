from dataclasses import dataclass
from typing import List

from models.model_call_recording import CallRecording


@dataclass
class ListRecordingsResponse:
    duration: str
    recordings: List[CallRecording]
