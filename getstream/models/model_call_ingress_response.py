from dataclasses import dataclass


from .model_rtmp_ingress import RTMPIngress


@dataclass
class CallIngressResponse:
    rtmp: RTMPIngress

    @classmethod
    def from_dict(cls, data: dict) -> "CallIngressResponse":
        data["rtmp"] = RTMPIngress.from_dict(data["rtmp"])
        return cls(**data)
