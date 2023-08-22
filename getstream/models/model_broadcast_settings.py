from dataclasses import dataclass

from models.model_hls_settings import HLSSettings


@dataclass
class BroadcastSettings:
    enabled: bool
    hls: HLSSettings
