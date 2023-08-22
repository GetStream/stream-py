from dataclasses import dataclass
from typing import Optional, List

from models.model_egress_hls_response import EgressHLSResponse
from models.model_egress_rtmp_response import EgressRTMPResponse


@dataclass
class EgressResponse:
    broadcasting: bool
    hls: Optional[EgressHLSResponse] = None
    rtmps: List[EgressRTMPResponse]
