from dataclasses import dataclass


@dataclass
class StartTranscriptionResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StartTranscriptionResponse":
        return cls(**data)
