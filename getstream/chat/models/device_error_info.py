# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class DeviceErrorInfo:
    error_message: str = field(metadata=config(field_name="error_message"))
    provider: str = field(metadata=config(field_name="provider"))
    provider_name: str = field(metadata=config(field_name="provider_name"))
