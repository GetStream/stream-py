# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional


@dataclass_json
@dataclass
class LayoutSettingsRequest:
    name: str = field(metadata=config(field_name="name"))
    external_app_url: Optional[str] = field(
        metadata=config(field_name="external_app_url"), default=None
    )
    external_css_url: Optional[str] = field(
        metadata=config(field_name="external_css_url"), default=None
    )
    options: Optional[object] = field(
        metadata=config(field_name="options"), default=None
    )
