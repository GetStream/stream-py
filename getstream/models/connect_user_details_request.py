from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class ConnectUserDetailsRequest:
    id: str = field(metadata=config(field_name="id"))
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
