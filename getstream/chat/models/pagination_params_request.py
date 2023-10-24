# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class PaginationParamsRequest:
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    offset: Optional[int] = field(metadata=config(field_name="offset"), default=None)
    id_gt: Optional[int] = field(metadata=config(field_name="id_gt"), default=None)
    id_gte: Optional[int] = field(metadata=config(field_name="id_gte"), default=None)
    id_lt: Optional[int] = field(metadata=config(field_name="id_lt"), default=None)
    id_lte: Optional[int] = field(metadata=config(field_name="id_lte"), default=None)
