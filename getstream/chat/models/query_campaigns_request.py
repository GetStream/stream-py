# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Dict, Optional
from getstream.chat.models.campaign_sort import CampaignSort


@dataclass_json
@dataclass
class QueryCampaignsRequest:
    filter_conditions: Dict[str, object] = field(
        metadata=config(field_name="filter_conditions")
    )
    limit: Optional[int] = field(metadata=config(field_name="limit"), default=None)
    sort: Optional[CampaignSort] = field(
        metadata=config(field_name="sort"), default=None
    )
