from dataclasses import dataclass


@dataclass
class StopTranscriptionResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StopTranscriptionResponse":
        return cls(**data)
