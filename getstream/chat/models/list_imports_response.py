# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List
from getstream.chat.models.import_task import ImportTask


@dataclass_json
@dataclass
class ListImportsResponse:
    duration: str = field(metadata=config(field_name="duration"))
    import_tasks: List[ImportTask] = field(metadata=config(field_name="import_tasks"))
