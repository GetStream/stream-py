# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class FileUploadResponse:
    duration: str = field(metadata=config(field_name="duration"))
    thumb_url: Optional[str] = field(
        metadata=config(field_name="thumb_url"), default=None
    )
    file: Optional[str] = field(metadata=config(field_name="file"), default=None)
