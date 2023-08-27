from dataclasses import dataclass


@dataclass
class RingSettings:
    auto_cancel_timeout_ms: int
    incoming_call_timeout_ms: int

    @classmethod
    def from_dict(cls, data: dict) -> "RingSettings":
        return cls(**data)
