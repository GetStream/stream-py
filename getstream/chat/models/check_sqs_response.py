# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class CheckSqsresponse:
    duration: str = field(metadata=config(field_name="duration"))
    status: str = field(metadata=config(field_name="status"))
    error: Optional[str] = field(metadata=config(field_name="error"), default=None)
    data: Optional[Dict[str, object]] = field(
        metadata=config(field_name="data"), default=None
    )
