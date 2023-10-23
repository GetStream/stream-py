# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.file_upload_config import FileUploadConfig
from getstream.chat.models.channel_config import ChannelConfig
from getstream.chat.models.config import Config
from getstream.chat.models.policy import Policy
from getstream.chat.models.push_notification_fields import PushNotificationFields
from getstream.chat.models.call_type import CallType


@dataclass_json
@dataclass
class App:
    disable_permissions_checks: bool = field(
        metadata=config(field_name="disable_permissions_checks")
    )
    image_moderation_enabled: bool = field(
        metadata=config(field_name="image_moderation_enabled")
    )
    suspended_explanation: str = field(
        metadata=config(field_name="suspended_explanation")
    )
    user_search_disallowed_roles: List[str] = field(
        metadata=config(field_name="user_search_disallowed_roles")
    )
    campaign_enabled: bool = field(metadata=config(field_name="campaign_enabled"))
    channel_configs: Dict[str, ChannelConfig] = field(
        metadata=config(field_name="channel_configs")
    )
    policies: Dict[str, List[Policy]] = field(metadata=config(field_name="policies"))
    sqs_secret: str = field(metadata=config(field_name="sqs_secret"))
    multi_tenant_enabled: bool = field(
        metadata=config(field_name="multi_tenant_enabled")
    )
    name: str = field(metadata=config(field_name="name"))
    suspended: bool = field(metadata=config(field_name="suspended"))
    cdn_expiration_seconds: int = field(
        metadata=config(field_name="cdn_expiration_seconds")
    )
    enforce_unique_usernames: str = field(
        metadata=config(field_name="enforce_unique_usernames")
    )
    grants: Dict[str, List[str]] = field(metadata=config(field_name="grants"))
    push_notifications: PushNotificationFields = field(
        metadata=config(field_name="push_notifications")
    )
    async_url_enrich_enabled: bool = field(
        metadata=config(field_name="async_url_enrich_enabled")
    )
    organization: str = field(metadata=config(field_name="organization"))
    permission_version: str = field(metadata=config(field_name="permission_version"))
    sqs_url: str = field(metadata=config(field_name="sqs_url"))
    search_backend: str = field(metadata=config(field_name="search_backend"))
    video_provider: str = field(metadata=config(field_name="video_provider"))
    webhook_url: str = field(metadata=config(field_name="webhook_url"))
    call_types: Dict[str, CallType] = field(metadata=config(field_name="call_types"))
    file_upload_config: FileUploadConfig = field(
        metadata=config(field_name="file_upload_config")
    )
    reminders_interval: int = field(metadata=config(field_name="reminders_interval"))
    webhook_events: List[str] = field(metadata=config(field_name="webhook_events"))
    custom_action_handler_url: str = field(
        metadata=config(field_name="custom_action_handler_url")
    )
    disable_auth_checks: bool = field(metadata=config(field_name="disable_auth_checks"))
    image_upload_config: FileUploadConfig = field(
        metadata=config(field_name="image_upload_config")
    )
    sqs_key: str = field(metadata=config(field_name="sqs_key"))
    agora_options: Optional[Config] = field(
        metadata=config(field_name="agora_options"), default=None
    )
    before_message_send_hook_url: Optional[str] = field(
        metadata=config(field_name="before_message_send_hook_url"), default=None
    )
    hms_options: Optional[Config] = field(
        metadata=config(field_name="hms_options"), default=None
    )
    image_moderation_labels: Optional[List[str]] = field(
        metadata=config(field_name="image_moderation_labels"), default=None
    )
    revoke_tokens_issued_before: Optional[datetime] = field(
        metadata=config(
            field_name="revoke_tokens_issued_before",
            encoder=lambda d: d.isoformat() if d is not None else None,
            decoder=parse,
            mm_field=fields.DateTime(format="iso"),
        ),
        default=None,
    )
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
    )
