from dataclasses import dataclass
from typing import List

from .model_call_recording import CallRecording


@dataclass
class ListRecordingsResponse:
    duration: str
    recordings: List[CallRecording]
