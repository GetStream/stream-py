from dataclasses import dataclass


@dataclass
class RejectCallResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "RejectCallResponse":
        return cls(**data)
