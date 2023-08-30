from dataclasses import dataclass


@dataclass
class SFUResponse:
    edge_name: str
    url: str
    ws_endpoint: str

    @classmethod
    def from_dict(cls, data: dict) -> "SFUResponse":
        return cls(**data)
