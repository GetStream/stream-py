# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.import_task import ImportTask


@dataclass_json
@dataclass
class GetImportResponse:
    duration: str = field(metadata=config(field_name="duration"))
    import_task: Optional[ImportTask] = field(
        metadata=config(field_name="import_task"), default=None
    )
