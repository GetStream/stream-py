# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class GeofenceSettingsRequest:
    names: Optional[List[str]] = field(
        metadata=config(field_name="names"), default=None
    )
