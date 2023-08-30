from dataclasses import dataclass


@dataclass
class RequestPermissionResponse:
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "RequestPermissionResponse":
        return cls(**data)
