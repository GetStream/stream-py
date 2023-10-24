# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class FileUploadConfig:
    allowed_file_extensions: List[str] = field(
        metadata=config(field_name="allowed_file_extensions")
    )
    allowed_mime_types: List[str] = field(
        metadata=config(field_name="allowed_mime_types")
    )
    blocked_file_extensions: List[str] = field(
        metadata=config(field_name="blocked_file_extensions")
    )
    blocked_mime_types: List[str] = field(
        metadata=config(field_name="blocked_mime_types")
    )
