from dataclasses import dataclass


@dataclass
class UnblockUserRequest:
    user_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "UnblockUserRequest":
        return cls(**data)
