from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional


@dataclass_json
@dataclass
class UserRequest:
    id: str = field(metadata=config(field_name="id"))
    role: Optional[str] = field(metadata=config(field_name="role"), default=None)
    teams: Optional[List[str]] = field(
        metadata=config(field_name="teams"), default=None
    )
    custom: Optional[Dict[str, object]] = field(
        metadata=config(field_name="custom"), default=None
    )
    image: Optional[str] = field(metadata=config(field_name="image"), default=None)
    name: Optional[str] = field(metadata=config(field_name="name"), default=None)
