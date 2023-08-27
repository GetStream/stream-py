from dataclasses import dataclass

from .model_hls_settings import HLSSettings


@dataclass
class BroadcastSettings:
    enabled: bool
    hls: HLSSettings

    @classmethod
    def from_dict(cls, data: dict) -> "BroadcastSettings":
        data["hls"] = HLSSettings.from_dict(data["hls"])
        return cls(**data)
