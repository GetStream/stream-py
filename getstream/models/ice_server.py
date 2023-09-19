from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class Iceserver:
    urls: List[str] = field(metadata=config(field_name="urls"))
    username: str = field(metadata=config(field_name="username"))
    password: str = field(metadata=config(field_name="password"))
