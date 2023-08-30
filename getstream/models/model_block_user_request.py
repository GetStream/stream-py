from dataclasses import dataclass


@dataclass
class BlockUserRequest:
    user_id: str

    @classmethod
    def from_dict(cls, data: dict) -> "BlockUserRequest":
        return cls(**data)
