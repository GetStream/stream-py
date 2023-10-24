# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class FlagMessageDetails:
    skip_push: Optional[bool] = field(
        metadata=config(field_name="skip_push"), default=None
    )
    updated_by_id: Optional[str] = field(
        metadata=config(field_name="updated_by_id"), default=None
    )
    pin_changed: Optional[bool] = field(
        metadata=config(field_name="pin_changed"), default=None
    )
    should_enrich: Optional[bool] = field(
        metadata=config(field_name="should_enrich"), default=None
    )
