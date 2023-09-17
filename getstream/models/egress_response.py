from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json
from egress_hls_response import EgressHlsresponse
from egress_rtmp_response import EgressRtmpresponse


@dataclass_json
@dataclass
class EgressResponse:
    rtmps: list[EgressRtmpresponse] = field(metadata=config(field_name="rtmps"))
    broadcasting: bool = field(metadata=config(field_name="broadcasting"))
    hls: Optional[EgressHlsresponse] = field(
        metadata=config(field_name="hls"), default=None
    )
