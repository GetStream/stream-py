# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict
from getstream.models.external_storage_response import ExternalStorageResponse


@dataclass_json
@dataclass
class ListExternalStorageResponse:
    duration: str = field(metadata=config(field_name="duration"))
    external_storages: Dict[str, ExternalStorageResponse] = field(
        metadata=config(field_name="external_storages")
    )
