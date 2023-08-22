from dataclasses import dataclass
from typing import Optional


@dataclass
class APNSRequest:
    body: Optional[str] = None
    title: Optional[str] = None
