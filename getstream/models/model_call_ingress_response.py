from dataclasses import dataclass


from .model_rtmp_ingress import RTMPIngress
@dataclass
class CallIngressResponse:

    rtmp: RTMPIngress
