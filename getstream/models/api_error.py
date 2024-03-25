# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional


@dataclass_json
@dataclass
class ApiError:
    code: int = field(metadata=config(field_name="code"))
    details: List[int] = field(metadata=config(field_name="details"))
    duration: str = field(metadata=config(field_name="duration"))
    message: str = field(metadata=config(field_name="message"))
    more_info: str = field(metadata=config(field_name="more_info"))
    status_code: int = field(metadata=config(field_name="StatusCode"))
    exception_fields: Optional[Dict[str, str]] = field(
        metadata=config(field_name="exception_fields"), default=None
    )
