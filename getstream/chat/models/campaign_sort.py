# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.campaign_sort_field import CampaignSortField


@dataclass_json
@dataclass
class CampaignSort:
    fields: List[CampaignSortField] = field(metadata=config(field_name="fields"))
    direction: Optional[str] = field(
        metadata=config(field_name="direction"), default=None
    )
