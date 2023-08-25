from dataclasses import dataclass
from typing import List

from .model_ice_server import ICEServer
from .model_sfu_response import SFUResponse


@dataclass
class Credentials:
    ice_servers: List[ICEServer]
    server: SFUResponse
    token: str
