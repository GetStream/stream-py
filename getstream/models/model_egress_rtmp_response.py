from dataclasses import dataclass


@dataclass
class EgressRTMPResponse:
    name: str
    stream_key: str
    url: str

    @classmethod
    def from_dict(cls, data: dict) -> "EgressRTMPResponse":
        return cls(**data)
