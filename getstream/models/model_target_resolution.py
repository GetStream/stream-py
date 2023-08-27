from dataclasses import dataclass


@dataclass
class TargetResolution:
    bitrate: int
    height: int
    width: int

    @classmethod
    def from_dict(cls, data: dict) -> "TargetResolution":
        return cls(**data)
