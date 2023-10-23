# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List


@dataclass_json
@dataclass
class ExportUsersRequest:
    user_ids: List[str] = field(metadata=config(field_name="user_ids"))
