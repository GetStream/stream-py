from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json
from device import Device


@dataclass_json
@dataclass
class ListDevicesResponse:
    devices: list[Device] = field(metadata=config(field_name="devices"))
    duration: str = field(metadata=config(field_name="duration"))
