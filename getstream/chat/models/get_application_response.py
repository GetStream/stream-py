# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.app import App


@dataclass_json
@dataclass
class GetApplicationResponse:
    app: App = field(metadata=config(field_name="app"))
    duration: str = field(metadata=config(field_name="duration"))
