from dataclasses import dataclass


@dataclass
class UnblockUserResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "UnblockUserResponse":
        return cls(**data)
