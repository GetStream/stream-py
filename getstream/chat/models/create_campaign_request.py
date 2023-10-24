# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from getstream.chat.models.campaign_data_request import CampaignDataRequest


@dataclass_json
@dataclass
class CreateCampaignRequest:
    campaign: CampaignDataRequest = field(metadata=config(field_name="campaign"))
