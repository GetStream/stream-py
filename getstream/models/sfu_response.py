from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Sfuresponse:
    url: str = field(metadata=config(field_name="url"))
    ws_endpoint: str = field(metadata=config(field_name="ws_endpoint"))
    edge_name: str = field(metadata=config(field_name="edge_name"))
