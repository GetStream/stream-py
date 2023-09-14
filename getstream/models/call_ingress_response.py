from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from rtmp_ingress import Rtmpingress


@dataclass_json
@dataclass
class CallIngressResponse:
    rtmp: Rtmpingress = field(metadata=config(field_name="rtmp"))
