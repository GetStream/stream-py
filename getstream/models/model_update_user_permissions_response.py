from dataclasses import dataclass


@dataclass
class UpdateUserPermissionsResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "UpdateUserPermissionsResponse":
        return cls(**data)
