# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Optional
from getstream.chat.models.firebase_config_fields import FirebaseConfigFields
from getstream.chat.models.huawei_config_fields import HuaweiConfigFields
from getstream.chat.models.push_provider import PushProvider
from getstream.chat.models.xiaomi_config_fields import XiaomiConfigFields
from getstream.chat.models.apn_config_fields import ApnconfigFields


@dataclass_json
@dataclass
class PushNotificationFields:
    version: str = field(metadata=config(field_name="version"))
    xiaomi: XiaomiConfigFields = field(metadata=config(field_name="xiaomi"))
    apn: ApnconfigFields = field(metadata=config(field_name="apn"))
    firebase: FirebaseConfigFields = field(metadata=config(field_name="firebase"))
    huawei: HuaweiConfigFields = field(metadata=config(field_name="huawei"))
    offline_only: bool = field(metadata=config(field_name="offline_only"))
    providers: Optional[List[PushProvider]] = field(
        metadata=config(field_name="providers"), default=None
    )
