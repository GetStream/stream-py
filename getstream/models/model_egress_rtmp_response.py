from dataclasses import dataclass


@dataclass
class EgressRTMPResponse:
    name: str
    stream_key: str
    url: str
