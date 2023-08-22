from dataclasses import dataclass

from models.model_rtmp_ingress import RTMPIngress


@dataclass
class CallIngressResponse:
    rtmp: RTMPIngress
