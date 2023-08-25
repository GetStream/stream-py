from dataclasses import dataclass
from typing import List


@dataclass
class ICEServer:
    password: str
    urls: List[str]
    username: str