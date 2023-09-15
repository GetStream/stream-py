from dataclasses import dataclass, field

from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Apns:
    body: str = field(metadata=config(field_name="body"))
    title: str = field(metadata=config(field_name="title"))
