# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class LayoutSettings:
    external_app_url: str = field(metadata=config(field_name="external_app_url"))
    external_css_url: str = field(metadata=config(field_name="external_css_url"))
    name: str = field(metadata=config(field_name="name"))
    options: Optional[object] = field(
        metadata=config(field_name="options"), default=None
    )
