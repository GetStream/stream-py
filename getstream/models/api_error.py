from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional


@dataclass_json
@dataclass
class Apierror:
    status_code: int = field(metadata=config(field_name="StatusCode"))
    code: int = field(metadata=config(field_name="code"))
    details: List[int] = field(metadata=config(field_name="details"))
    duration: str = field(metadata=config(field_name="duration"))
    message: str = field(metadata=config(field_name="message"))
    exception_fields: Optional[Dict[str, str]] = field(
        metadata=config(field_name="exception_fields"), default=None
    )
    more_info: Optional[str] = field(
        metadata=config(field_name="more_info"), default=None
    )
