from dataclasses import dataclass
from typing import List

from .model_ice_server import ICEServer
from .model_sfu_response import SFUResponse


@dataclass
class Credentials:
    ice_servers: List[ICEServer]
    server: SFUResponse
    token: str

    @classmethod
    def from_dict(cls, data: dict) -> "Credentials":
        data["ice_servers"] = [ICEServer.from_dict(d) for d in data["ice_servers"]]
        data["server"] = SFUResponse.from_dict(data["server"])
        return cls(**data)
