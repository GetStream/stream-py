# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Sfuresponse:
    edge_name: str = field(metadata=config(field_name="edge_name"))
    url: str = field(metadata=config(field_name="url"))
    ws_endpoint: str = field(metadata=config(field_name="ws_endpoint"))
