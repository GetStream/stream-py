from dataclasses import dataclass


@dataclass
class RecordSettings:
    audio_only: bool
    mode: str
    quality: str
