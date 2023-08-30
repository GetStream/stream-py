from dataclasses import dataclass


@dataclass
class BlockUserResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "BlockUserResponse":
        return cls(**data)
