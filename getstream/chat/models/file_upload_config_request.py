# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional


@dataclass_json
@dataclass
class FileUploadConfigRequest:
    allowed_file_extensions: Optional[List[str]] = field(
        metadata=config(field_name="allowed_file_extensions"), default=None
    )
    allowed_mime_types: Optional[List[str]] = field(
        metadata=config(field_name="allowed_mime_types"), default=None
    )
    blocked_file_extensions: Optional[List[str]] = field(
        metadata=config(field_name="blocked_file_extensions"), default=None
    )
    blocked_mime_types: Optional[List[str]] = field(
        metadata=config(field_name="blocked_mime_types"), default=None
    )
