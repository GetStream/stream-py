# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.models.s_3_request import S3Request
from getstream.models.azure_request import AzureRequest


@dataclass_json
@dataclass
class CreateExternalStorageRequest:
    bucket: str = field(metadata=config(field_name="bucket"))
    name: str = field(metadata=config(field_name="name"))
    storage_type: str = field(metadata=config(field_name="storage_type"))
    gcs_credentials: Optional[str] = field(
        metadata=config(field_name="gcs_credentials"), default=None
    )
    path: Optional[str] = field(metadata=config(field_name="path"), default=None)
    aws_s_3: Optional[S3Request] = field(
        metadata=config(field_name="aws_s3"), default=None
    )
    azure_blob: Optional[AzureRequest] = field(
        metadata=config(field_name="azure_blob"), default=None
    )
