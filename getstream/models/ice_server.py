from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Iceserver:
    username: str = field(metadata=config(field_name="username"))
    password: str = field(metadata=config(field_name="password"))
    urls: list[str] = field(metadata=config(field_name="urls"))
