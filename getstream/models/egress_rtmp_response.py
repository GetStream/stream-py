from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class EgressRtmpresponse:
    name: str = field(metadata=config(field_name="name"))
    stream_key: str = field(metadata=config(field_name="stream_key"))
    url: str = field(metadata=config(field_name="url"))
