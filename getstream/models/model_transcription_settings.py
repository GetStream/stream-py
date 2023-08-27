from dataclasses import dataclass


@dataclass
class TranscriptionSettings:
    closed_caption_mode: str
    mode: str

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptionSettings":
        return cls(**data)
