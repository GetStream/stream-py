from dataclasses import dataclass


@dataclass
class StartRecordingResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StartRecordingResponse":
        return cls(**data)
