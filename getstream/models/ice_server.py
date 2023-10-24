# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class Iceserver:
    password: str = field(metadata=config(field_name="password"))
    urls: List[str] = field(metadata=config(field_name="urls"))
    username: str = field(metadata=config(field_name="username"))
