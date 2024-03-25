# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json


@dataclass_json
@dataclass
class AzureRequest:
    abs_account_name: str = field(metadata=config(field_name="abs_account_name"))
    abs_client_id: str = field(metadata=config(field_name="abs_client_id"))
    abs_client_secret: str = field(metadata=config(field_name="abs_client_secret"))
    abs_tenant_id: str = field(metadata=config(field_name="abs_tenant_id"))
