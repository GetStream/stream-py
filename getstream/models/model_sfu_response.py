from dataclasses import dataclass


@dataclass
class SFUResponse:
    edge_name: str
    url: str
    ws_endpoint: str
