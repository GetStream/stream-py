from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class EgressRtmpresponse:
    url: str = field(metadata=config(field_name="url"))
    name: str = field(metadata=config(field_name="name"))
    stream_key: str = field(metadata=config(field_name="stream_key"))
