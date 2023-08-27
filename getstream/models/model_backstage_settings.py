from dataclasses import dataclass


@dataclass
class BackstageSettings:
    enabled: bool

    @classmethod
    def from_dict(cls, data: dict) -> "BackstageSettings":
        return cls(**data)
