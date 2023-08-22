from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ConnectUserDetailsRequest:
    custom: Optional[Dict[str, Any]] = None
    id: str
    image: Optional[str] = None
    name: Optional[str] = None
