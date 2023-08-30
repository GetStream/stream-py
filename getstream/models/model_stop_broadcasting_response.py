from dataclasses import dataclass


@dataclass
class StopBroadcastingResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "StopBroadcastingResponse":
        return cls(**data)
