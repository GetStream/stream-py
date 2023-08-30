from dataclasses import dataclass


@dataclass
class SendEventResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "SendEventResponse":
        return cls(**data)
