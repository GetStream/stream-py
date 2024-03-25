# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class S3Request:
    s3_region: str = field(metadata=config(field_name="s3_region"))
    s3_api_key: Optional[str] = field(
        metadata=config(field_name="s3_api_key"), default=None
    )
    s3_secret: Optional[str] = field(
        metadata=config(field_name="s3_secret"), default=None
    )
