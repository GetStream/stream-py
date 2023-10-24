# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional


@dataclass_json
@dataclass
class TestCampaignResponse:
    duration: str = field(metadata=config(field_name="duration"))
    status: str = field(metadata=config(field_name="status"))
    details: Optional[str] = field(metadata=config(field_name="details"), default=None)
    results: Optional[Dict[str, str]] = field(
        metadata=config(field_name="results"), default=None
    )
