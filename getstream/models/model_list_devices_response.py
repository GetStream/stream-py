from dataclasses import dataclass
from typing import List

from .model_device import Device


@dataclass
class ListDevicesResponse:
    devices: List[Device]
    duration: str

    @classmethod
    def from_dict(cls, data: dict) -> "ListDevicesResponse":
        data["devices"] = [Device.from_dict(d) for d in data["devices"]]
        return cls(**data)
