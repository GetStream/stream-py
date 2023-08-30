from dataclasses import dataclass


@dataclass
class AcceptCallResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "AcceptCallResponse":
        return cls(**data)
