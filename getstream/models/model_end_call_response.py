from dataclasses import dataclass


@dataclass
class EndCallResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "EndCallResponse":
        return cls(**data)
