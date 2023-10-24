# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/type.tmpl
from dataclasses import dataclass, field
from dataclasses_json import config, dataclass_json

from typing import List, Dict, Optional
from datetime import datetime
from dateutil.parser import parse
from marshmallow import fields
from getstream.chat.models.config_request import ConfigRequest
from getstream.chat.models.firebase_config_request import FirebaseConfigRequest
from getstream.chat.models.huawei_config_request import HuaweiConfigRequest
from getstream.chat.models.async_moderation_configuration_request import (
    AsyncModerationConfigurationRequest,
)
from getstream.chat.models.file_upload_config_request import FileUploadConfigRequest
from getstream.chat.models.apn_config_request import ApnconfigRequest
from getstream.chat.models.push_config_request import PushConfigRequest
from getstream.chat.models.xiaomi_config_request import XiaomiConfigRequest


@dataclass_json
@dataclass
class UpdateAppRequest:
    image_moderation_enabled: Optional[bool] = field(
        metadata=config(field_name="image_moderation_enabled"), default=None
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
    sqs_key: Optional[str] = field(metadata=config(field_name="sqs_key"), default=None)
    grants: Optional[Dict[str, List[str]]] = field(
        metadata=config(field_name="grants"), default=None
    )
    migrate_permissions_to_v_2: Optional[bool] = field(
        metadata=config(field_name="migrate_permissions_to_v2"), default=None
    )
    sqs_url: Optional[str] = field(metadata=config(field_name="sqs_url"), default=None)
    user_search_disallowed_roles: Optional[List[str]] = field(
        metadata=config(field_name="user_search_disallowed_roles"), default=None
    )
    hms_options: Optional[ConfigRequest] = field(
        metadata=config(field_name="hms_options"), default=None
    )
    async_url_enrich_enabled: Optional[bool] = field(
        metadata=config(field_name="async_url_enrich_enabled"), default=None
    )
    auto_translation_enabled: Optional[bool] = field(
        metadata=config(field_name="auto_translation_enabled"), default=None
    )
    cdn_expiration_seconds: Optional[int] = field(
        metadata=config(field_name="cdn_expiration_seconds"), default=None
    )
    firebase_config: Optional[FirebaseConfigRequest] = field(
        metadata=config(field_name="firebase_config"), default=None
    )
    huawei_config: Optional[HuaweiConfigRequest] = field(
        metadata=config(field_name="huawei_config"), default=None
    )
    webhook_events: Optional[List[str]] = field(
        metadata=config(field_name="webhook_events"), default=None
    )
    async_moderation_config: Optional[AsyncModerationConfigurationRequest] = field(
        metadata=config(field_name="async_moderation_config"), default=None
    )
    before_message_send_hook_url: Optional[str] = field(
        metadata=config(field_name="before_message_send_hook_url"), default=None
    )
    channel_hide_members_only: Optional[bool] = field(
        metadata=config(field_name="channel_hide_members_only"), default=None
    )
    enforce_unique_usernames: Optional[str] = field(
        metadata=config(field_name="enforce_unique_usernames"), default=None
    )
    file_upload_config: Optional[FileUploadConfigRequest] = field(
        metadata=config(field_name="file_upload_config"), default=None
    )
    image_moderation_block_labels: Optional[List[str]] = field(
        metadata=config(field_name="image_moderation_block_labels"), default=None
    )
    image_upload_config: Optional[FileUploadConfigRequest] = field(
        metadata=config(field_name="image_upload_config"), default=None
    )
    permission_version: Optional[str] = field(
        metadata=config(field_name="permission_version"), default=None
    )
    apn_config: Optional[ApnconfigRequest] = field(
        metadata=config(field_name="apn_config"), default=None
    )
    webhook_url: Optional[str] = field(
        metadata=config(field_name="webhook_url"), default=None
    )
    push_config: Optional[PushConfigRequest] = field(
        metadata=config(field_name="push_config"), default=None
    )
    sqs_secret: Optional[str] = field(
        metadata=config(field_name="sqs_secret"), default=None
    )
    reminders_interval: Optional[int] = field(
        metadata=config(field_name="reminders_interval"), default=None
    )
    xiaomi_config: Optional[XiaomiConfigRequest] = field(
        metadata=config(field_name="xiaomi_config"), default=None
    )
    disable_permissions_checks: Optional[bool] = field(
        metadata=config(field_name="disable_permissions_checks"), default=None
    )
    disable_auth_checks: Optional[bool] = field(
        metadata=config(field_name="disable_auth_checks"), default=None
    )
    custom_action_handler_url: Optional[str] = field(
        metadata=config(field_name="custom_action_handler_url"), default=None
    )
    multi_tenant_enabled: Optional[bool] = field(
        metadata=config(field_name="multi_tenant_enabled"), default=None
    )
    video_provider: Optional[str] = field(
        metadata=config(field_name="video_provider"), default=None
    )
    agora_options: Optional[ConfigRequest] = field(
        metadata=config(field_name="agora_options"), default=None
    )
