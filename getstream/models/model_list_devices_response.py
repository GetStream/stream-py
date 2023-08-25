from dataclasses import dataclass
from typing import List

from .model_device import Device


@dataclass
class ListDevicesResponse:
    devices: List[Device]
    duration: str