from dataclasses import dataclass


@dataclass
class AudioSettings:
    access_request_enabled: bool
    default_device: str
    mic_default_on: bool
    opus_dtx_enabled: bool
    redundant_coding_enabled: bool
    speaker_default_on: bool
