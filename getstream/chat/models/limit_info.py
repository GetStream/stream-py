# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class LimitInfo:
    limit: int = field(metadata=config(field_name="limit"))
    remaining: int = field(metadata=config(field_name="remaining"))
    reset: int = field(metadata=config(field_name="reset"))
