from dataclasses import dataclass


@dataclass
class StopRecordingResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StopRecordingResponse":
        return cls(**data)
