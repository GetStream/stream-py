from dataclasses import dataclass


@dataclass
class TranscriptionSettingsRequest:
    closed_caption_mode: str = None
    mode: str = None

    @classmethod
    def from_dict(cls, data: dict) -> "TranscriptionSettingsRequest":
        return cls(**data)
