from dataclasses import dataclass
from typing import Optional, List
from .model_egress_hls_response import EgressHLSResponse
from .model_egress_rtmp_response import EgressRTMPResponse


@dataclass
class EgressResponse:
    broadcasting: bool
    rtmps: List[EgressRTMPResponse]
    hls: Optional[EgressHLSResponse] = None

    @classmethod
    def from_dict(cls, data: dict) -> "EgressResponse":
        data["rtmps"] = [EgressRTMPResponse.from_dict(d) for d in data["rtmps"]]
        if data.get("hls"):
            data["hls"] = EgressHLSResponse.from_dict(data["hls"])
        return cls(**data)
