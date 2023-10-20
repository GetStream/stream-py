# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.models.egress_hls_response import EgressHlsresponse
from getstream.models.egress_rtmp_response import EgressRtmpresponse


@dataclass_json
@dataclass
class EgressResponse:
    broadcasting: bool = field(metadata=config(field_name="broadcasting"))
    rtmps: List[EgressRtmpresponse] = field(metadata=config(field_name="rtmps"))
    hls: Optional[EgressHlsresponse] = field(
        metadata=config(field_name="hls"), default=None
    )
