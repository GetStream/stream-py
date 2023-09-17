from dataclasses import dataclass, field
from typing import Optional
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class Apierror:
    details: list[int] = field(metadata=config(field_name="details"))
    duration: str = field(metadata=config(field_name="duration"))
    message: str = field(metadata=config(field_name="message"))
    more_info: str = field(metadata=config(field_name="more_info"))
    status_code: int = field(metadata=config(field_name="StatusCode"))
    code: int = field(metadata=config(field_name="code"))
    exception_fields: Optional[dict[str, str]] = field(
        metadata=config(field_name="exception_fields"), default=None
    )
