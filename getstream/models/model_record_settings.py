from dataclasses import dataclass


@dataclass
class RecordSettings:
    audio_only: bool
    mode: str
    quality: str

    @classmethod
    def from_dict(cls, data: dict) -> "RecordSettings":
        return cls(**data)
