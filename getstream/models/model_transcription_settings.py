from dataclasses import dataclass


@dataclass
class TranscriptionSettings:
    closed_caption_mode: str
    mode: str
