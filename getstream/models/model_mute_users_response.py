from dataclasses import dataclass


@dataclass
class MuteUsersResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "MuteUsersResponse":
        return cls(**data)
