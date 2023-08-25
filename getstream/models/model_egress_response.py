from dataclasses import dataclass
from typing import Optional, List
from .model_egress_hls_response import EgressHLSResponse
from .model_egress_rtmp_response import EgressRTMPResponse

@dataclass
class EgressResponse:

    broadcasting: bool
    rtmps: List[EgressRTMPResponse]
    hls: Optional[EgressHLSResponse] = None
