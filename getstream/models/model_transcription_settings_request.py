from dataclasses import dataclass


@dataclass
class TranscriptionSettingsRequest:
    closed_caption_mode: str = None
    mode: str = None
