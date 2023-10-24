# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class ExportChannelsResult:
    url: str = field(metadata=config(field_name="url"))
    path: Optional[str] = field(metadata=config(field_name="path"), default=None)
    s_3_bucket_name: Optional[str] = field(
        metadata=config(field_name="s3_bucket_name"), default=None
    )
