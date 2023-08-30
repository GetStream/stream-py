from dataclasses import dataclass
from typing import List

from .model_call_recording import CallRecording


@dataclass
class ListRecordingsResponse:
    duration: str
    recordings: List[CallRecording]

    @classmethod
    def from_dict(cls, data: dict) -> "ListRecordingsResponse":
        data["recordings"] = [CallRecording.from_dict(d) for d in data["recordings"]]
        return cls(**data)
