from typing import List
from dataclasses import dataclass


@dataclass
class GeofenceSettings:
    names: List[str]
