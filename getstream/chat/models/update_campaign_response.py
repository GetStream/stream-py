# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import Optional
from getstream.chat.models.campaign import Campaign


@dataclass_json
@dataclass
class UpdateCampaignResponse:
    duration: str = field(metadata=config(field_name="duration"))
    campaign: Optional[Campaign] = field(
        metadata=config(field_name="campaign"), default=None
    )
