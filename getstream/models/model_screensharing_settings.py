from dataclasses import dataclass


@dataclass
class ScreensharingSettings:
    access_request_enabled: bool
    enabled: bool

    @classmethod
    def from_dict(cls, data: dict) -> "ScreensharingSettings":
        return cls(**data)
