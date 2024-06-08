from dataclasses import dataclass
from dataclasses import field as dc_field
from dataclasses_json import DataClassJsonMixin
from dataclasses_json import config as dc_config
from datetime import datetime
from marshmallow import fields
from typing import List, Dict, Optional, Final, NewType
from getstream.utils import encode_datetime, datetime_from_unix_ns


@dataclass
class APIError(DataClassJsonMixin):
    code: int = dc_field(metadata=dc_config(field_name="code"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: str = dc_field(metadata=dc_config(field_name="message"))
    more_info: str = dc_field(metadata=dc_config(field_name="more_info"))
    status_code: int = dc_field(metadata=dc_config(field_name="StatusCode"))
    details: "List[int]" = dc_field(metadata=dc_config(field_name="details"))
    exception_fields: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="exception_fields")
    )


@dataclass
class APNConfig(DataClassJsonMixin):
    auth_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auth_key")
    )
    auth_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auth_type")
    )
    bundle_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="bundle_id")
    )
    development: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="development")
    )
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="Disabled")
    )
    host: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="host"))
    key_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="key_id")
    )
    notification_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="notification_template")
    )
    p12_cert: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="p12_cert")
    )
    team_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="team_id")
    )


@dataclass
class APNConfigFields(DataClassJsonMixin):
    development: bool = dc_field(metadata=dc_config(field_name="development"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    notification_template: str = dc_field(
        metadata=dc_config(field_name="notification_template")
    )
    auth_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auth_key")
    )
    auth_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auth_type")
    )
    bundle_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="bundle_id")
    )
    host: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="host"))
    key_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="key_id")
    )
    p12_cert: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="p12_cert")
    )
    team_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="team_id")
    )


@dataclass
class APNS(DataClassJsonMixin):
    body: str = dc_field(metadata=dc_config(field_name="body"))
    title: str = dc_field(metadata=dc_config(field_name="title"))


@dataclass
class Action(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    style: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="style")
    )
    value: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="value")
    )


@dataclass
class AppResponseFields(DataClassJsonMixin):
    async_url_enrich_enabled: bool = dc_field(
        metadata=dc_config(field_name="async_url_enrich_enabled")
    )
    auto_translation_enabled: bool = dc_field(
        metadata=dc_config(field_name="auto_translation_enabled")
    )
    campaign_enabled: bool = dc_field(metadata=dc_config(field_name="campaign_enabled"))
    cdn_expiration_seconds: int = dc_field(
        metadata=dc_config(field_name="cdn_expiration_seconds")
    )
    custom_action_handler_url: str = dc_field(
        metadata=dc_config(field_name="custom_action_handler_url")
    )
    disable_auth_checks: bool = dc_field(
        metadata=dc_config(field_name="disable_auth_checks")
    )
    disable_permissions_checks: bool = dc_field(
        metadata=dc_config(field_name="disable_permissions_checks")
    )
    enforce_unique_usernames: str = dc_field(
        metadata=dc_config(field_name="enforce_unique_usernames")
    )
    image_moderation_enabled: bool = dc_field(
        metadata=dc_config(field_name="image_moderation_enabled")
    )
    multi_tenant_enabled: bool = dc_field(
        metadata=dc_config(field_name="multi_tenant_enabled")
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    organization: str = dc_field(metadata=dc_config(field_name="organization"))
    permission_version: str = dc_field(
        metadata=dc_config(field_name="permission_version")
    )
    polls_enabled: bool = dc_field(metadata=dc_config(field_name="polls_enabled"))
    reminders_interval: int = dc_field(
        metadata=dc_config(field_name="reminders_interval")
    )
    sns_key: str = dc_field(metadata=dc_config(field_name="sns_key"))
    sns_secret: str = dc_field(metadata=dc_config(field_name="sns_secret"))
    sns_topic_arn: str = dc_field(metadata=dc_config(field_name="sns_topic_arn"))
    sqs_key: str = dc_field(metadata=dc_config(field_name="sqs_key"))
    sqs_secret: str = dc_field(metadata=dc_config(field_name="sqs_secret"))
    sqs_url: str = dc_field(metadata=dc_config(field_name="sqs_url"))
    suspended: bool = dc_field(metadata=dc_config(field_name="suspended"))
    suspended_explanation: str = dc_field(
        metadata=dc_config(field_name="suspended_explanation")
    )
    video_provider: str = dc_field(metadata=dc_config(field_name="video_provider"))
    webhook_url: str = dc_field(metadata=dc_config(field_name="webhook_url"))
    user_search_disallowed_roles: List[str] = dc_field(
        metadata=dc_config(field_name="user_search_disallowed_roles")
    )
    webhook_events: List[str] = dc_field(
        metadata=dc_config(field_name="webhook_events")
    )
    call_types: "Dict[str, Optional[CallType]]" = dc_field(
        metadata=dc_config(field_name="call_types")
    )
    channel_configs: "Dict[str, Optional[ChannelConfig]]" = dc_field(
        metadata=dc_config(field_name="channel_configs")
    )
    file_upload_config: "FileUploadConfig" = dc_field(
        metadata=dc_config(field_name="file_upload_config")
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    image_upload_config: "FileUploadConfig" = dc_field(
        metadata=dc_config(field_name="image_upload_config")
    )
    policies: "Dict[str, List[Policy]]" = dc_field(
        metadata=dc_config(field_name="policies")
    )
    push_notifications: "PushNotificationFields" = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    before_message_send_hook_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="before_message_send_hook_url")
    )
    revoke_tokens_issued_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="revoke_tokens_issued_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    geofences: "Optional[List[Optional[GeofenceResponse]]]" = dc_field(
        default=None, metadata=dc_config(field_name="geofences")
    )
    image_moderation_labels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="image_moderation_labels")
    )
    agora_options: "Optional[Config]" = dc_field(
        default=None, metadata=dc_config(field_name="agora_options")
    )
    datadog_info: "Optional[DataDogInfo]" = dc_field(
        default=None, metadata=dc_config(field_name="datadog_info")
    )
    hms_options: "Optional[Config]" = dc_field(
        default=None, metadata=dc_config(field_name="hms_options")
    )


@dataclass
class AsyncModerationCallbackConfig(DataClassJsonMixin):
    mode: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mode"))
    server_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="server_url")
    )


@dataclass
class AsyncModerationConfiguration(DataClassJsonMixin):
    timeout_ms: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="timeout_ms")
    )
    callback: "Optional[AsyncModerationCallbackConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="callback")
    )


@dataclass
class Attachment(DataClassJsonMixin):
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    asset_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="asset_url")
    )
    auth_or_icon: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_icon")
    )
    auth_or_link: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_link")
    )
    auth_or_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_name")
    )
    color: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="color")
    )
    fallback: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="fallback")
    )
    footer: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="footer")
    )
    footer_icon: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="footer_icon")
    )
    image_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="image_url")
    )
    og_scrape_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="og_scrape_url")
    )
    original_height: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="original_height")
    )
    original_width: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="original_width")
    )
    pretext: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="pretext")
    )
    text: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="text"))
    thumb_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thumb_url")
    )
    title: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="title")
    )
    title_link: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="title_link")
    )
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))
    actions: "Optional[List[Optional[Action]]]" = dc_field(
        default=None, metadata=dc_config(field_name="actions")
    )
    fields: "Optional[List[Optional[Field]]]" = dc_field(
        default=None, metadata=dc_config(field_name="fields")
    )
    giphy: "Optional[Images]" = dc_field(
        default=None, metadata=dc_config(field_name="giphy")
    )


@dataclass
class AudioSettings(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    default_device: str = dc_field(metadata=dc_config(field_name="default_device"))
    mic_default_on: bool = dc_field(metadata=dc_config(field_name="mic_default_on"))
    opus_dtx_enabled: bool = dc_field(metadata=dc_config(field_name="opus_dtx_enabled"))
    redundant_coding_enabled: bool = dc_field(
        metadata=dc_config(field_name="redundant_coding_enabled")
    )
    speaker_default_on: bool = dc_field(
        metadata=dc_config(field_name="speaker_default_on")
    )
    noise_cancellation: "Optional[NoiseCancellationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="noise_cancellation")
    )


@dataclass
class AudioSettingsRequest(DataClassJsonMixin):
    default_device: str = dc_field(metadata=dc_config(field_name="default_device"))
    access_request_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="access_request_enabled")
    )
    mic_default_on: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mic_default_on")
    )
    opus_dtx_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="opus_dtx_enabled")
    )
    redundant_coding_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="redundant_coding_enabled")
    )
    speaker_default_on: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="speaker_default_on")
    )
    noise_cancellation: "Optional[NoiseCancellationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="noise_cancellation")
    )


@dataclass
class AudioSettingsResponse(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    default_device: str = dc_field(metadata=dc_config(field_name="default_device"))
    mic_default_on: bool = dc_field(metadata=dc_config(field_name="mic_default_on"))
    opus_dtx_enabled: bool = dc_field(metadata=dc_config(field_name="opus_dtx_enabled"))
    redundant_coding_enabled: bool = dc_field(
        metadata=dc_config(field_name="redundant_coding_enabled")
    )
    speaker_default_on: bool = dc_field(
        metadata=dc_config(field_name="speaker_default_on")
    )
    noise_cancellation: "Optional[NoiseCancellationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="noise_cancellation")
    )


@dataclass
class AutomodDetails(DataClassJsonMixin):
    action: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="action")
    )
    original_message_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="original_message_type")
    )
    image_labels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="image_labels")
    )
    message_details: "Optional[FlagMessageDetails]" = dc_field(
        default=None, metadata=dc_config(field_name="message_details")
    )
    result: "Optional[MessageModerationResult]" = dc_field(
        default=None, metadata=dc_config(field_name="result")
    )


@dataclass
class AzureRequest(DataClassJsonMixin):
    abs_account_name: str = dc_field(metadata=dc_config(field_name="abs_account_name"))
    abs_client_id: str = dc_field(metadata=dc_config(field_name="abs_client_id"))
    abs_client_secret: str = dc_field(
        metadata=dc_config(field_name="abs_client_secret")
    )
    abs_tenant_id: str = dc_field(metadata=dc_config(field_name="abs_tenant_id"))


@dataclass
class BackstageSettings(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))


@dataclass
class BackstageSettingsRequest(DataClassJsonMixin):
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )


@dataclass
class BackstageSettingsResponse(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))


@dataclass
class BanRequest(DataClassJsonMixin):
    target_user_id: str = dc_field(metadata=dc_config(field_name="target_user_id"))
    banned_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="banned_by_id")
    )
    channel_cid: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="channel_cid")
    )
    ip_ban: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="ip_ban")
    )
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    shadow: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="shadow")
    )
    timeout: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="timeout")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    banned_by: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="banned_by")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class BanResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    shadow: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="shadow")
    )
    banned_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="banned_by")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class BlockList(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    words: List[str] = dc_field(metadata=dc_config(field_name="words"))
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class BlockListOptions(DataClassJsonMixin):
    behavior: str = dc_field(metadata=dc_config(field_name="behavior"))
    blocklist: str = dc_field(metadata=dc_config(field_name="blocklist"))


@dataclass
class BlockUserRequest(DataClassJsonMixin):
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))


@dataclass
class BlockUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class BlockUsersRequest(DataClassJsonMixin):
    blocked_user_id: str = dc_field(metadata=dc_config(field_name="blocked_user_id"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class BlockUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    blocks: "List[Optional[UserBlock]]" = dc_field(
        metadata=dc_config(field_name="blocks")
    )


@dataclass
class BlockedUserResponse(DataClassJsonMixin):
    blocked_user_id: str = dc_field(metadata=dc_config(field_name="blocked_user_id"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    blocked_user: "UserResponse" = dc_field(
        metadata=dc_config(field_name="blocked_user")
    )
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))


@dataclass
class BroadcastSettings(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    hls: "HLSSettings" = dc_field(metadata=dc_config(field_name="hls"))


@dataclass
class BroadcastSettingsRequest(DataClassJsonMixin):
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )
    hls: "Optional[HLSSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="hls")
    )


@dataclass
class BroadcastSettingsResponse(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    hls: "HLSSettingsResponse" = dc_field(metadata=dc_config(field_name="hls"))


@dataclass
class CallEvent(DataClassJsonMixin):
    description: str = dc_field(metadata=dc_config(field_name="description"))
    end_timestamp: int = dc_field(metadata=dc_config(field_name="end_timestamp"))
    severity: int = dc_field(metadata=dc_config(field_name="severity"))
    timestamp: int = dc_field(metadata=dc_config(field_name="timestamp"))
    type: str = dc_field(metadata=dc_config(field_name="type"))


@dataclass
class CallIngressResponse(DataClassJsonMixin):
    rtmp: "RTMPIngress" = dc_field(metadata=dc_config(field_name="rtmp"))


@dataclass
class CallParticipantResponse(DataClassJsonMixin):
    joined_at: datetime = dc_field(
        metadata=dc_config(
            field_name="joined_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    role: str = dc_field(metadata=dc_config(field_name="role"))
    user_session_id: str = dc_field(metadata=dc_config(field_name="user_session_id"))
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))


@dataclass
class CallRecording(DataClassJsonMixin):
    end_time: datetime = dc_field(
        metadata=dc_config(
            field_name="end_time",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    filename: str = dc_field(metadata=dc_config(field_name="filename"))
    start_time: datetime = dc_field(
        metadata=dc_config(
            field_name="start_time",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    url: str = dc_field(metadata=dc_config(field_name="url"))


@dataclass
class CallRequest(DataClassJsonMixin):
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    starts_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="starts_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    members: "Optional[List[MemberRequest]]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    created_by: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    settings_override: "Optional[CallSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="settings_override")
    )


@dataclass
class CallResponse(DataClassJsonMixin):
    backstage: bool = dc_field(metadata=dc_config(field_name="backstage"))
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    current_session_id: str = dc_field(
        metadata=dc_config(field_name="current_session_id")
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    recording: bool = dc_field(metadata=dc_config(field_name="recording"))
    transcribing: bool = dc_field(metadata=dc_config(field_name="transcribing"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    blocked_user_ids: List[str] = dc_field(
        metadata=dc_config(field_name="blocked_user_ids")
    )
    created_by: "UserResponse" = dc_field(metadata=dc_config(field_name="created_by"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    egress: "EgressResponse" = dc_field(metadata=dc_config(field_name="egress"))
    ingress: "CallIngressResponse" = dc_field(metadata=dc_config(field_name="ingress"))
    settings: "CallSettingsResponse" = dc_field(
        metadata=dc_config(field_name="settings")
    )
    ended_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="ended_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    starts_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="starts_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    session: "Optional[CallSessionResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="session")
    )
    thumbnails: "Optional[ThumbnailResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="thumbnails")
    )


@dataclass
class CallSessionResponse(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    participants: "List[CallParticipantResponse]" = dc_field(
        metadata=dc_config(field_name="participants")
    )
    accepted_by: "Dict[str, datetime]" = dc_field(
        metadata=dc_config(field_name="accepted_by")
    )
    missed_by: "Dict[str, datetime]" = dc_field(
        metadata=dc_config(field_name="missed_by")
    )
    participants_count_by_role: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="participants_count_by_role")
    )
    rejected_by: "Dict[str, datetime]" = dc_field(
        metadata=dc_config(field_name="rejected_by")
    )
    ended_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="ended_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    live_ended_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="live_ended_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    live_started_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="live_started_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    started_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="started_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    timer_ends_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="timer_ends_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class CallSettings(DataClassJsonMixin):
    audio: "Optional[AudioSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="audio")
    )
    backstage: "Optional[BackstageSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="backstage")
    )
    broadcasting: "Optional[BroadcastSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="broadcasting")
    )
    geofencing: "Optional[GeofenceSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="geofencing")
    )
    limits: "Optional[LimitsSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="limits")
    )
    recording: "Optional[RecordSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="recording")
    )
    ring: "Optional[RingSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="ring")
    )
    screensharing: "Optional[ScreensharingSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="screensharing")
    )
    thumbnails: "Optional[ThumbnailsSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="thumbnails")
    )
    transcription: "Optional[TranscriptionSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="transcription")
    )
    video: "Optional[VideoSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="video")
    )


@dataclass
class CallSettingsRequest(DataClassJsonMixin):
    audio: "Optional[AudioSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="audio")
    )
    backstage: "Optional[BackstageSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="backstage")
    )
    broadcasting: "Optional[BroadcastSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="broadcasting")
    )
    geofencing: "Optional[GeofenceSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="geofencing")
    )
    limits: "Optional[LimitsSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="limits")
    )
    recording: "Optional[RecordSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="recording")
    )
    ring: "Optional[RingSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="ring")
    )
    screensharing: "Optional[ScreensharingSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="screensharing")
    )
    thumbnails: "Optional[ThumbnailsSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="thumbnails")
    )
    transcription: "Optional[TranscriptionSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="transcription")
    )
    video: "Optional[VideoSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="video")
    )


@dataclass
class CallSettingsResponse(DataClassJsonMixin):
    audio: "AudioSettingsResponse" = dc_field(metadata=dc_config(field_name="audio"))
    backstage: "BackstageSettingsResponse" = dc_field(
        metadata=dc_config(field_name="backstage")
    )
    broadcasting: "BroadcastSettingsResponse" = dc_field(
        metadata=dc_config(field_name="broadcasting")
    )
    geofencing: "GeofenceSettingsResponse" = dc_field(
        metadata=dc_config(field_name="geofencing")
    )
    limits: "LimitsSettingsResponse" = dc_field(metadata=dc_config(field_name="limits"))
    recording: "RecordSettingsResponse" = dc_field(
        metadata=dc_config(field_name="recording")
    )
    ring: "RingSettingsResponse" = dc_field(metadata=dc_config(field_name="ring"))
    screensharing: "ScreensharingSettingsResponse" = dc_field(
        metadata=dc_config(field_name="screensharing")
    )
    thumbnails: "ThumbnailsSettingsResponse" = dc_field(
        metadata=dc_config(field_name="thumbnails")
    )
    transcription: "TranscriptionSettingsResponse" = dc_field(
        metadata=dc_config(field_name="transcription")
    )
    video: "VideoSettingsResponse" = dc_field(metadata=dc_config(field_name="video"))


@dataclass
class CallStateResponseFields(DataClassJsonMixin):
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))
    own_capabilities: "List[OwnCapability]" = dc_field(
        metadata=dc_config(field_name="own_capabilities")
    )
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class CallStatsReportSummaryResponse(DataClassJsonMixin):
    call_cid: str = dc_field(metadata=dc_config(field_name="call_cid"))
    call_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="call_duration_seconds")
    )
    call_session_id: str = dc_field(metadata=dc_config(field_name="call_session_id"))
    call_status: str = dc_field(metadata=dc_config(field_name="call_status"))
    first_stats_time: datetime = dc_field(
        metadata=dc_config(
            field_name="first_stats_time",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    quality_score: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="quality_score")
    )


@dataclass
class CallTimeline(DataClassJsonMixin):
    events: "List[Optional[CallEvent]]" = dc_field(
        metadata=dc_config(field_name="events")
    )


@dataclass
class CallTranscription(DataClassJsonMixin):
    end_time: datetime = dc_field(
        metadata=dc_config(
            field_name="end_time",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    filename: str = dc_field(metadata=dc_config(field_name="filename"))
    start_time: datetime = dc_field(
        metadata=dc_config(
            field_name="start_time",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    url: str = dc_field(metadata=dc_config(field_name="url"))


@dataclass
class CallType(DataClassJsonMixin):
    app_pk: int = dc_field(metadata=dc_config(field_name="AppPK"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="CreatedAt",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    external_storage: str = dc_field(metadata=dc_config(field_name="ExternalStorage"))
    name: str = dc_field(metadata=dc_config(field_name="Name"))
    pk: int = dc_field(metadata=dc_config(field_name="PK"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="UpdatedAt",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    notification_settings: "Optional[NotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="NotificationSettings")
    )
    settings: "Optional[CallSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="Settings")
    )


@dataclass
class CallTypeResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    notification_settings: "NotificationSettings" = dc_field(
        metadata=dc_config(field_name="notification_settings")
    )
    settings: "CallSettingsResponse" = dc_field(
        metadata=dc_config(field_name="settings")
    )
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )


@dataclass
class CastPollVoteRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )
    vote: "Optional[VoteData]" = dc_field(
        default=None, metadata=dc_config(field_name="vote")
    )


@dataclass
class Channel(DataClassJsonMixin):
    auto_translation_language: str = dc_field(
        metadata=dc_config(field_name="auto_translation_language")
    )
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    disabled: bool = dc_field(metadata=dc_config(field_name="disabled"))
    frozen: bool = dc_field(metadata=dc_config(field_name="frozen"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    auto_translation_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_enabled")
    )
    cooldown: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="cooldown")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    member_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="member_count")
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    invites: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="invites")
    )
    members: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    config: "Optional[ChannelConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="config")
    )
    config_overrides: "Optional[ChannelConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="config_overrides")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    truncated_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="truncated_by")
    )


@dataclass
class ChannelConfig(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    connect_events: bool = dc_field(metadata=dc_config(field_name="connect_events"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = dc_field(metadata=dc_config(field_name="custom_events"))
    mark_messages_pending: bool = dc_field(
        metadata=dc_config(field_name="mark_messages_pending")
    )
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    mutes: bool = dc_field(metadata=dc_config(field_name="mutes"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    polls: bool = dc_field(metadata=dc_config(field_name="polls"))
    push_notifications: bool = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    quotes: bool = dc_field(metadata=dc_config(field_name="quotes"))
    reactions: bool = dc_field(metadata=dc_config(field_name="reactions"))
    read_events: bool = dc_field(metadata=dc_config(field_name="read_events"))
    reminders: bool = dc_field(metadata=dc_config(field_name="reminders"))
    replies: bool = dc_field(metadata=dc_config(field_name="replies"))
    search: bool = dc_field(metadata=dc_config(field_name="search"))
    typing_events: bool = dc_field(metadata=dc_config(field_name="typing_events"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    uploads: bool = dc_field(metadata=dc_config(field_name="uploads"))
    url_enrichment: bool = dc_field(metadata=dc_config(field_name="url_enrichment"))
    commands: List[str] = dc_field(metadata=dc_config(field_name="commands"))
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )


@dataclass
class ChannelConfigWithInfo(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    connect_events: bool = dc_field(metadata=dc_config(field_name="connect_events"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = dc_field(metadata=dc_config(field_name="custom_events"))
    mark_messages_pending: bool = dc_field(
        metadata=dc_config(field_name="mark_messages_pending")
    )
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    mutes: bool = dc_field(metadata=dc_config(field_name="mutes"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    polls: bool = dc_field(metadata=dc_config(field_name="polls"))
    push_notifications: bool = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    quotes: bool = dc_field(metadata=dc_config(field_name="quotes"))
    reactions: bool = dc_field(metadata=dc_config(field_name="reactions"))
    read_events: bool = dc_field(metadata=dc_config(field_name="read_events"))
    reminders: bool = dc_field(metadata=dc_config(field_name="reminders"))
    replies: bool = dc_field(metadata=dc_config(field_name="replies"))
    search: bool = dc_field(metadata=dc_config(field_name="search"))
    typing_events: bool = dc_field(metadata=dc_config(field_name="typing_events"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    uploads: bool = dc_field(metadata=dc_config(field_name="uploads"))
    url_enrichment: bool = dc_field(metadata=dc_config(field_name="url_enrichment"))
    commands: "List[Optional[Command]]" = dc_field(
        metadata=dc_config(field_name="commands")
    )
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )


@dataclass
class ChannelExport(DataClassJsonMixin):
    cid: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="cid"))
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    messages_since: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="messages_since",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    messages_until: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="messages_until",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))


@dataclass
class ChannelGetOrCreateRequest(DataClassJsonMixin):
    hide_for_creator: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hide_for_creator")
    )
    state: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="state")
    )
    thread_unread_counts: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="thread_unread_counts")
    )
    data: "Optional[ChannelInput]" = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )
    members: "Optional[PaginationParams]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    messages: "Optional[MessagePaginationParams]" = dc_field(
        default=None, metadata=dc_config(field_name="messages")
    )
    watchers: "Optional[PaginationParams]" = dc_field(
        default=None, metadata=dc_config(field_name="watchers")
    )


@dataclass
class ChannelInput(DataClassJsonMixin):
    auto_translation_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_enabled")
    )
    auto_translation_language: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_language")
    )
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="disabled")
    )
    frozen: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="frozen")
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    truncated_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="truncated_by_id")
    )
    invites: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="invites")
    )
    members: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    config_overrides: "Optional[ChannelConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="config_overrides")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )


@dataclass
class ChannelMember(DataClassJsonMixin):
    banned: bool = dc_field(metadata=dc_config(field_name="banned"))
    channel_role: str = dc_field(metadata=dc_config(field_name="channel_role"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    notifications_muted: bool = dc_field(
        metadata=dc_config(field_name="notifications_muted")
    )
    shadow_banned: bool = dc_field(metadata=dc_config(field_name="shadow_banned"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    ban_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="ban_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    invite_accepted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="invite_accepted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    invite_rejected_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="invite_rejected_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    invited: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="invited")
    )
    is_moderator: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_moderator")
    )
    status: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="status")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ChannelMute(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ChannelResponse(DataClassJsonMixin):
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    disabled: bool = dc_field(metadata=dc_config(field_name="disabled"))
    frozen: bool = dc_field(metadata=dc_config(field_name="frozen"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    auto_translation_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_enabled")
    )
    auto_translation_language: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_language")
    )
    blocked: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="blocked")
    )
    cooldown: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="cooldown")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    hidden: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hidden")
    )
    hide_messages_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="hide_messages_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    member_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="member_count")
    )
    mute_expires_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="mute_expires_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    muted: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="muted")
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    truncated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="truncated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    members: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    own_capabilities: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="own_capabilities")
    )
    config: "Optional[ChannelConfigWithInfo]" = dc_field(
        default=None, metadata=dc_config(field_name="config")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    truncated_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="truncated_by")
    )


@dataclass
class ChannelStateResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[Optional[ChannelMember]]" = dc_field(
        metadata=dc_config(field_name="members")
    )
    messages: "List[MessageResponse]" = dc_field(
        metadata=dc_config(field_name="messages")
    )
    pinned_messages: "List[MessageResponse]" = dc_field(
        metadata=dc_config(field_name="pinned_messages")
    )
    threads: "List[Optional[ThreadState]]" = dc_field(
        metadata=dc_config(field_name="threads")
    )
    hidden: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hidden")
    )
    hide_messages_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="hide_messages_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    watcher_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="watcher_count")
    )
    pending_messages: "Optional[List[Optional[PendingMessage]]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_messages")
    )
    read: "Optional[List[ReadStateResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="read")
    )
    watchers: "Optional[List[UserResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="watchers")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    membership: "Optional[ChannelMember]" = dc_field(
        default=None, metadata=dc_config(field_name="membership")
    )


@dataclass
class ChannelStateResponseFields(DataClassJsonMixin):
    members: "List[Optional[ChannelMember]]" = dc_field(
        metadata=dc_config(field_name="members")
    )
    messages: "List[MessageResponse]" = dc_field(
        metadata=dc_config(field_name="messages")
    )
    pinned_messages: "List[MessageResponse]" = dc_field(
        metadata=dc_config(field_name="pinned_messages")
    )
    threads: "List[Optional[ThreadState]]" = dc_field(
        metadata=dc_config(field_name="threads")
    )
    hidden: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hidden")
    )
    hide_messages_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="hide_messages_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    watcher_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="watcher_count")
    )
    pending_messages: "Optional[List[Optional[PendingMessage]]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_messages")
    )
    read: "Optional[List[ReadStateResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="read")
    )
    watchers: "Optional[List[UserResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="watchers")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    membership: "Optional[ChannelMember]" = dc_field(
        default=None, metadata=dc_config(field_name="membership")
    )


@dataclass
class ChannelTypeConfig(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    connect_events: bool = dc_field(metadata=dc_config(field_name="connect_events"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = dc_field(metadata=dc_config(field_name="custom_events"))
    mark_messages_pending: bool = dc_field(
        metadata=dc_config(field_name="mark_messages_pending")
    )
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    mutes: bool = dc_field(metadata=dc_config(field_name="mutes"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    polls: bool = dc_field(metadata=dc_config(field_name="polls"))
    push_notifications: bool = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    quotes: bool = dc_field(metadata=dc_config(field_name="quotes"))
    reactions: bool = dc_field(metadata=dc_config(field_name="reactions"))
    read_events: bool = dc_field(metadata=dc_config(field_name="read_events"))
    reminders: bool = dc_field(metadata=dc_config(field_name="reminders"))
    replies: bool = dc_field(metadata=dc_config(field_name="replies"))
    search: bool = dc_field(metadata=dc_config(field_name="search"))
    typing_events: bool = dc_field(metadata=dc_config(field_name="typing_events"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    uploads: bool = dc_field(metadata=dc_config(field_name="uploads"))
    url_enrichment: bool = dc_field(metadata=dc_config(field_name="url_enrichment"))
    commands: "List[Optional[Command]]" = dc_field(
        metadata=dc_config(field_name="commands")
    )
    permissions: "List[PolicyRequest]" = dc_field(
        metadata=dc_config(field_name="permissions")
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )


@dataclass
class CheckExternalStorageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    file_url: str = dc_field(metadata=dc_config(field_name="file_url"))


@dataclass
class CheckPushRequest(DataClassJsonMixin):
    apn_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_template")
    )
    firebase_data_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_data_template")
    )
    firebase_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_template")
    )
    message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="message_id")
    )
    push_provider_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="push_provider_name")
    )
    push_provider_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="push_provider_type")
    )
    skip_devices: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_devices")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class CheckPushResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    rendered_apn_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="rendered_apn_template")
    )
    rendered_firebase_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="rendered_firebase_template")
    )
    skip_devices: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_devices")
    )
    general_errors: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="general_errors")
    )
    device_errors: "Optional[Dict[str, DeviceErrorInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="device_errors")
    )
    rendered_message: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="rendered_message")
    )


@dataclass
class CheckSNSRequest(DataClassJsonMixin):
    sns_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_key")
    )
    sns_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_secret")
    )
    sns_topic_arn: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_topic_arn")
    )


@dataclass
class CheckSNSResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    status: str = dc_field(metadata=dc_config(field_name="status"))
    error: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="error")
    )
    data: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )


@dataclass
class CheckSQSRequest(DataClassJsonMixin):
    sqs_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_key")
    )
    sqs_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_secret")
    )
    sqs_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_url")
    )


@dataclass
class CheckSQSResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    status: str = dc_field(metadata=dc_config(field_name="status"))
    error: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="error")
    )
    data: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )


@dataclass
class CollectUserFeedbackRequest(DataClassJsonMixin):
    rating: int = dc_field(metadata=dc_config(field_name="rating"))
    sdk: str = dc_field(metadata=dc_config(field_name="sdk"))
    sdk_version: str = dc_field(metadata=dc_config(field_name="sdk_version"))
    user_session_id: str = dc_field(metadata=dc_config(field_name="user_session_id"))
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )


@dataclass
class CollectUserFeedbackResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class Command(DataClassJsonMixin):
    args: str = dc_field(metadata=dc_config(field_name="args"))
    description: str = dc_field(metadata=dc_config(field_name="description"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    set: str = dc_field(metadata=dc_config(field_name="set"))
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class CommitMessageRequest(DataClassJsonMixin):
    pass


@dataclass
class Config(DataClassJsonMixin):
    app_certificate: str = dc_field(metadata=dc_config(field_name="app_certificate"))
    app_id: str = dc_field(metadata=dc_config(field_name="app_id"))
    default_role: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="default_role")
    )
    role_map: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="role_map")
    )


@dataclass
class Coordinates(DataClassJsonMixin):
    latitude: float = dc_field(metadata=dc_config(field_name="latitude"))
    longitude: float = dc_field(metadata=dc_config(field_name="longitude"))


@dataclass
class CreateBlockListRequest(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    words: List[str] = dc_field(metadata=dc_config(field_name="words"))
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))


@dataclass
class CreateCallTypeRequest(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )
    notification_settings: "Optional[NotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="notification_settings")
    )
    settings: "Optional[CallSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="settings")
    )


@dataclass
class CreateCallTypeResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    notification_settings: "NotificationSettings" = dc_field(
        metadata=dc_config(field_name="notification_settings")
    )
    settings: "CallSettingsResponse" = dc_field(
        metadata=dc_config(field_name="settings")
    )
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )


@dataclass
class CreateChannelTypeRequest(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    connect_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="connect_events")
    )
    custom_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="custom_events")
    )
    mark_messages_pending: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mark_messages_pending")
    )
    message_retention: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="message_retention")
    )
    mutes: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mutes")
    )
    polls: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="polls")
    )
    push_notifications: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )
    reactions: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="reactions")
    )
    read_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="read_events")
    )
    replies: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="replies")
    )
    search: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="search")
    )
    typing_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="typing_events")
    )
    uploads: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="uploads")
    )
    url_enrichment: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="url_enrichment")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    commands: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="commands")
    )
    permissions: "Optional[List[PolicyRequest]]" = dc_field(
        default=None, metadata=dc_config(field_name="permissions")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )


@dataclass
class CreateChannelTypeResponse(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    connect_events: bool = dc_field(metadata=dc_config(field_name="connect_events"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = dc_field(metadata=dc_config(field_name="custom_events"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    mark_messages_pending: bool = dc_field(
        metadata=dc_config(field_name="mark_messages_pending")
    )
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    mutes: bool = dc_field(metadata=dc_config(field_name="mutes"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    polls: bool = dc_field(metadata=dc_config(field_name="polls"))
    push_notifications: bool = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    quotes: bool = dc_field(metadata=dc_config(field_name="quotes"))
    reactions: bool = dc_field(metadata=dc_config(field_name="reactions"))
    read_events: bool = dc_field(metadata=dc_config(field_name="read_events"))
    reminders: bool = dc_field(metadata=dc_config(field_name="reminders"))
    replies: bool = dc_field(metadata=dc_config(field_name="replies"))
    search: bool = dc_field(metadata=dc_config(field_name="search"))
    typing_events: bool = dc_field(metadata=dc_config(field_name="typing_events"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    uploads: bool = dc_field(metadata=dc_config(field_name="uploads"))
    url_enrichment: bool = dc_field(metadata=dc_config(field_name="url_enrichment"))
    commands: List[str] = dc_field(metadata=dc_config(field_name="commands"))
    permissions: "List[PolicyRequest]" = dc_field(
        metadata=dc_config(field_name="permissions")
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )


@dataclass
class CreateCommandRequest(DataClassJsonMixin):
    description: str = dc_field(metadata=dc_config(field_name="description"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    args: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="args"))
    set: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="set"))


@dataclass
class CreateCommandResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    command: "Optional[Command]" = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )


@dataclass
class CreateDeviceRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    push_provider: str = dc_field(metadata=dc_config(field_name="push_provider"))
    push_provider_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="push_provider_name")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    voip_token: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="voip_token")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class CreateExternalStorageRequest(DataClassJsonMixin):
    bucket: str = dc_field(metadata=dc_config(field_name="bucket"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    storage_type: str = dc_field(metadata=dc_config(field_name="storage_type"))
    gcs_credentials: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="gcs_credentials")
    )
    path: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="path"))
    aws_s3: "Optional[S3Request]" = dc_field(
        default=None, metadata=dc_config(field_name="aws_s3")
    )
    azure_blob: "Optional[AzureRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="azure_blob")
    )


@dataclass
class CreateExternalStorageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class CreateGuestRequest(DataClassJsonMixin):
    user: "UserRequest" = dc_field(metadata=dc_config(field_name="user"))


@dataclass
class CreateGuestResponse(DataClassJsonMixin):
    access_token: str = dc_field(metadata=dc_config(field_name="access_token"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))


@dataclass
class CreateImportRequest(DataClassJsonMixin):
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    path: str = dc_field(metadata=dc_config(field_name="path"))


@dataclass
class CreateImportResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    import_task: "Optional[ImportTask]" = dc_field(
        default=None, metadata=dc_config(field_name="import_task")
    )


@dataclass
class CreateImportURLRequest(DataClassJsonMixin):
    filename: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="filename")
    )


@dataclass
class CreateImportURLResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    path: str = dc_field(metadata=dc_config(field_name="path"))
    upload_url: str = dc_field(metadata=dc_config(field_name="upload_url"))


@dataclass
class CreatePollOptionRequest(DataClassJsonMixin):
    text: str = dc_field(metadata=dc_config(field_name="text"))
    position: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="position")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="Custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class CreatePollRequest(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    allow_answers: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="allow_answers")
    )
    allow_user_suggested_options: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="allow_user_suggested_options")
    )
    description: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="description")
    )
    enforce_unique_vote: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enforce_unique_vote")
    )
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    is_closed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_closed")
    )
    max_votes_allowed: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_votes_allowed")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    voting_visibility: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="voting_visibility")
    )
    options: "Optional[List[Optional[PollOptionInput]]]" = dc_field(
        default=None, metadata=dc_config(field_name="options")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="Custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class CreateRoleRequest(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))


@dataclass
class CreateRoleResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    role: "Role" = dc_field(metadata=dc_config(field_name="role"))


@dataclass
class DataDogInfo(DataClassJsonMixin):
    api_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="api_key")
    )
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )
    site: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="site"))


@dataclass
class DeactivateUserRequest(DataClassJsonMixin):
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    mark_messages_deleted: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mark_messages_deleted")
    )


@dataclass
class DeactivateUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class DeactivateUsersRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    mark_channels_deleted: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mark_channels_deleted")
    )
    mark_messages_deleted: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mark_messages_deleted")
    )


@dataclass
class DeactivateUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))


@dataclass
class DeleteChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )


@dataclass
class DeleteChannelsRequest(DataClassJsonMixin):
    cids: List[str] = dc_field(metadata=dc_config(field_name="cids"))
    hard_delete: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hard_delete")
    )


@dataclass
class DeleteChannelsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="task_id")
    )
    result: "Optional[Dict[str, Optional[DeleteChannelsResult]]]" = dc_field(
        default=None, metadata=dc_config(field_name="result")
    )


@dataclass
class DeleteChannelsResult(DataClassJsonMixin):
    status: str = dc_field(metadata=dc_config(field_name="status"))
    error: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="error")
    )


@dataclass
class DeleteCommandResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))


@dataclass
class DeleteExternalStorageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class DeleteMessageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "MessageResponse" = dc_field(metadata=dc_config(field_name="message"))


@dataclass
class DeleteRecordingResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class DeleteTranscriptionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class DeleteUsersRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))
    calls: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="calls")
    )
    conversations: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="conversations")
    )
    messages: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="messages")
    )
    new_call_owner_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="new_call_owner_id")
    )
    new_channel_owner_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="new_channel_owner_id")
    )
    user: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="user"))


@dataclass
class DeleteUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))


@dataclass
class Device(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    push_provider: str = dc_field(metadata=dc_config(field_name="push_provider"))
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="disabled")
    )
    disabled_reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="disabled_reason")
    )
    push_provider_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="push_provider_name")
    )
    voip: Optional[bool] = dc_field(default=None, metadata=dc_config(field_name="voip"))


@dataclass
class DeviceErrorInfo(DataClassJsonMixin):
    error_message: str = dc_field(metadata=dc_config(field_name="error_message"))
    provider: str = dc_field(metadata=dc_config(field_name="provider"))
    provider_name: str = dc_field(metadata=dc_config(field_name="provider_name"))


@dataclass
class EdgeResponse(DataClassJsonMixin):
    continent_code: str = dc_field(metadata=dc_config(field_name="continent_code"))
    country_iso_code: str = dc_field(metadata=dc_config(field_name="country_iso_code"))
    green: int = dc_field(metadata=dc_config(field_name="green"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    latency_test_url: str = dc_field(metadata=dc_config(field_name="latency_test_url"))
    latitude: float = dc_field(metadata=dc_config(field_name="latitude"))
    longitude: float = dc_field(metadata=dc_config(field_name="longitude"))
    red: int = dc_field(metadata=dc_config(field_name="red"))
    subdivision_iso_code: str = dc_field(
        metadata=dc_config(field_name="subdivision_iso_code")
    )
    yellow: int = dc_field(metadata=dc_config(field_name="yellow"))


@dataclass
class EgressHLSResponse(DataClassJsonMixin):
    playlist_url: str = dc_field(metadata=dc_config(field_name="playlist_url"))


@dataclass
class EgressRTMPResponse(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    stream_key: str = dc_field(metadata=dc_config(field_name="stream_key"))
    url: str = dc_field(metadata=dc_config(field_name="url"))


@dataclass
class EgressResponse(DataClassJsonMixin):
    broadcasting: bool = dc_field(metadata=dc_config(field_name="broadcasting"))
    rtmp_s: "List[EgressRTMPResponse]" = dc_field(
        metadata=dc_config(field_name="rtmps")
    )
    hls: "Optional[EgressHLSResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="hls")
    )


@dataclass
class EndCallRequest(DataClassJsonMixin):
    pass


@dataclass
class EndCallResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class ErrorResult(DataClassJsonMixin):
    type: str = dc_field(metadata=dc_config(field_name="type"))
    stacktrace: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="stacktrace")
    )
    version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="version")
    )


@dataclass
class EventNotificationSettings(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    apns: "APNS" = dc_field(metadata=dc_config(field_name="apns"))


@dataclass
class EventRequest(DataClassJsonMixin):
    type: str = dc_field(metadata=dc_config(field_name="type"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class EventResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    event: "WSEvent" = dc_field(metadata=dc_config(field_name="event"))


@dataclass
class ExportChannelsRequest(DataClassJsonMixin):
    channels: "List[ChannelExport]" = dc_field(
        metadata=dc_config(field_name="channels")
    )
    clear_deleted_message_text: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="clear_deleted_message_text")
    )
    export_users: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="export_users")
    )
    include_soft_deleted_channels: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="include_soft_deleted_channels")
    )
    include_truncated_messages: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="include_truncated_messages")
    )
    version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="version")
    )


@dataclass
class ExportChannelsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))


@dataclass
class ExportChannelsResult(DataClassJsonMixin):
    url: str = dc_field(metadata=dc_config(field_name="url"))
    path: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="path"))
    s3_bucket_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="s3_bucket_name")
    )


@dataclass
class ExportUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    messages: "Optional[List[Optional[Message]]]" = dc_field(
        default=None, metadata=dc_config(field_name="messages")
    )
    reactions: "Optional[List[Optional[Reaction]]]" = dc_field(
        default=None, metadata=dc_config(field_name="reactions")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ExportUsersRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))


@dataclass
class ExportUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))


@dataclass
class ExternalStorageResponse(DataClassJsonMixin):
    bucket: str = dc_field(metadata=dc_config(field_name="bucket"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    path: str = dc_field(metadata=dc_config(field_name="path"))
    type: str = dc_field(metadata=dc_config(field_name="type"))


@dataclass
class Field(DataClassJsonMixin):
    short: bool = dc_field(metadata=dc_config(field_name="short"))
    title: str = dc_field(metadata=dc_config(field_name="title"))
    value: str = dc_field(metadata=dc_config(field_name="value"))


@dataclass
class FileDeleteResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class FileUploadConfig(DataClassJsonMixin):
    size_limit: int = dc_field(metadata=dc_config(field_name="size_limit"))
    allowed_file_extensions: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_file_extensions")
    )
    allowed_mime_types: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_mime_types")
    )
    blocked_file_extensions: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="blocked_file_extensions")
    )
    blocked_mime_types: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="blocked_mime_types")
    )


@dataclass
class FileUploadRequest(DataClassJsonMixin):
    file: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="file"))
    user: "Optional[OnlyUserID]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class FileUploadResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    file: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="file"))
    thumb_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thumb_url")
    )


@dataclass
class FirebaseConfig(DataClassJsonMixin):
    apn_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_template")
    )
    credentials_json: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="credentials_json")
    )
    data_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="data_template")
    )
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="Disabled")
    )
    notification_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="notification_template")
    )
    server_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="server_key")
    )


@dataclass
class FirebaseConfigFields(DataClassJsonMixin):
    apn_template: str = dc_field(metadata=dc_config(field_name="apn_template"))
    data_template: str = dc_field(metadata=dc_config(field_name="data_template"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    notification_template: str = dc_field(
        metadata=dc_config(field_name="notification_template")
    )
    credentials_json: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="credentials_json")
    )
    server_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="server_key")
    )


@dataclass
class Flag(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_automod: bool = dc_field(
        metadata=dc_config(field_name="created_by_automod")
    )
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    app_roved_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="approved_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    rejected_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="rejected_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reviewed_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="reviewed_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reviewed_by: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reviewed_by")
    )
    target_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="target_message_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    details: "Optional[FlagDetails]" = dc_field(
        default=None, metadata=dc_config(field_name="details")
    )
    target_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="target_message")
    )
    target_user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="target_user")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class FlagDetails(DataClassJsonMixin):
    original_text: str = dc_field(metadata=dc_config(field_name="original_text"))
    extra: Dict[str, object] = dc_field(metadata=dc_config(field_name="Extra"))
    automod: "Optional[AutomodDetails]" = dc_field(
        default=None, metadata=dc_config(field_name="automod")
    )


@dataclass
class FlagFeedback(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    message_id: str = dc_field(metadata=dc_config(field_name="message_id"))
    labels: "List[Label]" = dc_field(metadata=dc_config(field_name="labels"))


@dataclass
class FlagMessageDetails(DataClassJsonMixin):
    pin_changed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="pin_changed")
    )
    should_enrich: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="should_enrich")
    )
    skip_push: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_push")
    )
    updated_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="updated_by_id")
    )


@dataclass
class FlagRequest(DataClassJsonMixin):
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    target_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="target_message_id")
    )
    target_user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="target_user_id")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class FlagResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    flag: "Optional[Flag]" = dc_field(
        default=None, metadata=dc_config(field_name="flag")
    )


@dataclass
class FullUserResponse(DataClassJsonMixin):
    banned: bool = dc_field(metadata=dc_config(field_name="banned"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    invisible: bool = dc_field(metadata=dc_config(field_name="invisible"))
    language: str = dc_field(metadata=dc_config(field_name="language"))
    online: bool = dc_field(metadata=dc_config(field_name="online"))
    role: str = dc_field(metadata=dc_config(field_name="role"))
    shadow_banned: bool = dc_field(metadata=dc_config(field_name="shadow_banned"))
    total_unread_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_count")
    )
    unread_channels: int = dc_field(metadata=dc_config(field_name="unread_channels"))
    unread_threads: int = dc_field(metadata=dc_config(field_name="unread_threads"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    blocked_user_ids: List[str] = dc_field(
        metadata=dc_config(field_name="blocked_user_ids")
    )
    channel_mutes: "List[Optional[ChannelMute]]" = dc_field(
        metadata=dc_config(field_name="channel_mutes")
    )
    devices: "List[Optional[Device]]" = dc_field(
        metadata=dc_config(field_name="devices")
    )
    mutes: "List[Optional[UserMute]]" = dc_field(metadata=dc_config(field_name="mutes"))
    teams: List[str] = dc_field(metadata=dc_config(field_name="teams"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deactivated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deactivated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    image: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="image")
    )
    last_active: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_active",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    name: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="name"))
    revoke_tokens_issued_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="revoke_tokens_issued_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    latest_hidden_channels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="latest_hidden_channels")
    )
    privacy_settings: "Optional[PrivacySettings]" = dc_field(
        default=None, metadata=dc_config(field_name="privacy_settings")
    )
    push_notifications: "Optional[PushNotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )


@dataclass
class GeofenceResponse(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    description: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="description")
    )
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))
    country_codes: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="country_codes")
    )


@dataclass
class GeofenceSettings(DataClassJsonMixin):
    names: List[str] = dc_field(metadata=dc_config(field_name="names"))


@dataclass
class GeofenceSettingsRequest(DataClassJsonMixin):
    names: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="names")
    )


@dataclass
class GeofenceSettingsResponse(DataClassJsonMixin):
    names: List[str] = dc_field(metadata=dc_config(field_name="names"))


@dataclass
class GeolocationResult(DataClassJsonMixin):
    accuracy_radius: int = dc_field(metadata=dc_config(field_name="accuracy_radius"))
    city: str = dc_field(metadata=dc_config(field_name="city"))
    continent: str = dc_field(metadata=dc_config(field_name="continent"))
    continent_code: str = dc_field(metadata=dc_config(field_name="continent_code"))
    country: str = dc_field(metadata=dc_config(field_name="country"))
    country_iso_code: str = dc_field(metadata=dc_config(field_name="country_iso_code"))
    latitude: float = dc_field(metadata=dc_config(field_name="latitude"))
    longitude: float = dc_field(metadata=dc_config(field_name="longitude"))
    subdivision: str = dc_field(metadata=dc_config(field_name="subdivision"))
    subdivision_iso_code: str = dc_field(
        metadata=dc_config(field_name="subdivision_iso_code")
    )


@dataclass
class GetApplicationResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    app: "AppResponseFields" = dc_field(metadata=dc_config(field_name="app"))


@dataclass
class GetBlockListResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    blocklist: "Optional[BlockList]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )


@dataclass
class GetBlockedUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    blocks: "List[Optional[BlockedUserResponse]]" = dc_field(
        metadata=dc_config(field_name="blocks")
    )


@dataclass
class GetCallResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))
    own_capabilities: "List[OwnCapability]" = dc_field(
        metadata=dc_config(field_name="own_capabilities")
    )
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class GetCallStatsResponse(DataClassJsonMixin):
    call_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="call_duration_seconds")
    )
    call_status: str = dc_field(metadata=dc_config(field_name="call_status"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    max_freezes_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="max_freezes_duration_seconds")
    )
    max_participants: int = dc_field(metadata=dc_config(field_name="max_participants"))
    max_total_quality_limitation_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="max_total_quality_limitation_duration_seconds")
    )
    publishing_participants: int = dc_field(
        metadata=dc_config(field_name="publishing_participants")
    )
    quality_score: int = dc_field(metadata=dc_config(field_name="quality_score"))
    sfu_count: int = dc_field(metadata=dc_config(field_name="sfu_count"))
    participant_report: "List[Optional[UserStats]]" = dc_field(
        metadata=dc_config(field_name="participant_report")
    )
    sfus: "List[SFULocationResponse]" = dc_field(metadata=dc_config(field_name="sfus"))
    call_timeline: "Optional[CallTimeline]" = dc_field(
        default=None, metadata=dc_config(field_name="call_timeline")
    )
    jitter: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="jitter")
    )
    latency: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="latency")
    )


@dataclass
class GetCallTypeResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    notification_settings: "NotificationSettings" = dc_field(
        metadata=dc_config(field_name="notification_settings")
    )
    settings: "CallSettingsResponse" = dc_field(
        metadata=dc_config(field_name="settings")
    )
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )


@dataclass
class GetCommandResponse(DataClassJsonMixin):
    args: str = dc_field(metadata=dc_config(field_name="args"))
    description: str = dc_field(metadata=dc_config(field_name="description"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    set: str = dc_field(metadata=dc_config(field_name="set"))
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class GetCustomPermissionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    permission: "Permission" = dc_field(metadata=dc_config(field_name="permission"))


@dataclass
class GetEdgesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    edges: "List[EdgeResponse]" = dc_field(metadata=dc_config(field_name="edges"))


@dataclass
class GetExportChannelsStatusResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    status: str = dc_field(metadata=dc_config(field_name="status"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    error: "Optional[ErrorResult]" = dc_field(
        default=None, metadata=dc_config(field_name="error")
    )
    result: "Optional[ExportChannelsResult]" = dc_field(
        default=None, metadata=dc_config(field_name="result")
    )


@dataclass
class GetImportResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    import_task: "Optional[ImportTask]" = dc_field(
        default=None, metadata=dc_config(field_name="import_task")
    )


@dataclass
class GetManyMessagesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    messages: "List[Optional[Message]]" = dc_field(
        metadata=dc_config(field_name="messages")
    )


@dataclass
class GetMessageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "MessageWithChannelResponse" = dc_field(
        metadata=dc_config(field_name="message")
    )
    pending_message_metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_message_metadata")
    )


@dataclass
class GetOGResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    asset_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="asset_url")
    )
    auth_or_icon: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_icon")
    )
    auth_or_link: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_link")
    )
    auth_or_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="author_name")
    )
    color: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="color")
    )
    fallback: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="fallback")
    )
    footer: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="footer")
    )
    footer_icon: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="footer_icon")
    )
    image_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="image_url")
    )
    og_scrape_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="og_scrape_url")
    )
    original_height: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="original_height")
    )
    original_width: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="original_width")
    )
    pretext: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="pretext")
    )
    text: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="text"))
    thumb_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thumb_url")
    )
    title: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="title")
    )
    title_link: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="title_link")
    )
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))
    actions: "Optional[List[Optional[Action]]]" = dc_field(
        default=None, metadata=dc_config(field_name="actions")
    )
    fields: "Optional[List[Optional[Field]]]" = dc_field(
        default=None, metadata=dc_config(field_name="fields")
    )
    giphy: "Optional[Images]" = dc_field(
        default=None, metadata=dc_config(field_name="giphy")
    )


@dataclass
class GetOrCreateCallRequest(DataClassJsonMixin):
    members_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="members_limit")
    )
    notify: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="notify")
    )
    ring: Optional[bool] = dc_field(default=None, metadata=dc_config(field_name="ring"))
    data: "Optional[CallRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )


@dataclass
class GetOrCreateCallResponse(DataClassJsonMixin):
    created: bool = dc_field(metadata=dc_config(field_name="created"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))
    own_capabilities: "List[OwnCapability]" = dc_field(
        metadata=dc_config(field_name="own_capabilities")
    )
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class GetRateLimitsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    android: "Optional[Dict[str, LimitInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="android")
    )
    ios: "Optional[Dict[str, LimitInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="ios")
    )
    server_side: "Optional[Dict[str, LimitInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="server_side")
    )
    web: "Optional[Dict[str, LimitInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="web")
    )


@dataclass
class GetReactionsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    reactions: "List[Optional[Reaction]]" = dc_field(
        metadata=dc_config(field_name="reactions")
    )


@dataclass
class GetRepliesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    messages: "List[MessageResponse]" = dc_field(
        metadata=dc_config(field_name="messages")
    )


@dataclass
class GetTaskResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    status: str = dc_field(metadata=dc_config(field_name="status"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    error: "Optional[ErrorResult]" = dc_field(
        default=None, metadata=dc_config(field_name="error")
    )
    result: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="result")
    )


@dataclass
class GetThreadResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    thread: "ThreadStateResponse" = dc_field(metadata=dc_config(field_name="thread"))


@dataclass
class GoLiveRequest(DataClassJsonMixin):
    recording_storage_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="recording_storage_name")
    )
    start_hls: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="start_hls")
    )
    start_recording: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="start_recording")
    )
    start_transcription: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="start_transcription")
    )
    transcription_storage_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="transcription_storage_name")
    )


@dataclass
class GoLiveResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class HLSSettings(DataClassJsonMixin):
    auto_on: bool = dc_field(metadata=dc_config(field_name="auto_on"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    quality_tracks: List[str] = dc_field(
        metadata=dc_config(field_name="quality_tracks")
    )
    layout: "Optional[LayoutSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="layout")
    )


@dataclass
class HLSSettingsRequest(DataClassJsonMixin):
    quality_tracks: List[str] = dc_field(
        metadata=dc_config(field_name="quality_tracks")
    )
    auto_on: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="auto_on")
    )
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )
    layout: "Optional[LayoutSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="layout")
    )


@dataclass
class HLSSettingsResponse(DataClassJsonMixin):
    auto_on: bool = dc_field(metadata=dc_config(field_name="auto_on"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    quality_tracks: List[str] = dc_field(
        metadata=dc_config(field_name="quality_tracks")
    )
    layout: "LayoutSettingsResponse" = dc_field(metadata=dc_config(field_name="layout"))


@dataclass
class HideChannelRequest(DataClassJsonMixin):
    clear_history: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="clear_history")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class HideChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class HuaweiConfig(DataClassJsonMixin):
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="Disabled")
    )
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="secret")
    )


@dataclass
class HuaweiConfigFields(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="secret")
    )


@dataclass
class ImageData(DataClassJsonMixin):
    frames: str = dc_field(metadata=dc_config(field_name="frames"))
    height: str = dc_field(metadata=dc_config(field_name="height"))
    size: str = dc_field(metadata=dc_config(field_name="size"))
    url: str = dc_field(metadata=dc_config(field_name="url"))
    width: str = dc_field(metadata=dc_config(field_name="width"))


@dataclass
class ImageSize(DataClassJsonMixin):
    crop: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="crop"))
    height: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="height")
    )
    resize: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="resize")
    )
    width: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="width")
    )


@dataclass
class ImageUploadRequest(DataClassJsonMixin):
    file: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="file"))
    upload_sizes: "Optional[List[ImageSize]]" = dc_field(
        default=None, metadata=dc_config(field_name="upload_sizes")
    )
    user: "Optional[OnlyUserID]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ImageUploadResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    file: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="file"))
    thumb_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thumb_url")
    )
    upload_sizes: "Optional[List[ImageSize]]" = dc_field(
        default=None, metadata=dc_config(field_name="upload_sizes")
    )


@dataclass
class Images(DataClassJsonMixin):
    fixed_height: "ImageData" = dc_field(metadata=dc_config(field_name="fixed_height"))
    fixed_height_downsampled: "ImageData" = dc_field(
        metadata=dc_config(field_name="fixed_height_downsampled")
    )
    fixed_height_still: "ImageData" = dc_field(
        metadata=dc_config(field_name="fixed_height_still")
    )
    fixed_width: "ImageData" = dc_field(metadata=dc_config(field_name="fixed_width"))
    fixed_width_downsampled: "ImageData" = dc_field(
        metadata=dc_config(field_name="fixed_width_downsampled")
    )
    fixed_width_still: "ImageData" = dc_field(
        metadata=dc_config(field_name="fixed_width_still")
    )
    original: "ImageData" = dc_field(metadata=dc_config(field_name="original"))


@dataclass
class ImportTask(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    path: str = dc_field(metadata=dc_config(field_name="path"))
    state: str = dc_field(metadata=dc_config(field_name="state"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    history: "List[Optional[ImportTaskHistory]]" = dc_field(
        metadata=dc_config(field_name="history")
    )
    size: Optional[int] = dc_field(default=None, metadata=dc_config(field_name="size"))


@dataclass
class ImportTaskHistory(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    next_state: str = dc_field(metadata=dc_config(field_name="next_state"))
    prev_state: str = dc_field(metadata=dc_config(field_name="prev_state"))


@dataclass
class Label(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    harm_labels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="harm_labels")
    )
    phrase_list_ids: "Optional[List[int]]" = dc_field(
        default=None, metadata=dc_config(field_name="phrase_list_ids")
    )


@dataclass
class LabelThresholds(DataClassJsonMixin):
    block: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="block")
    )
    flag: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="flag")
    )


@dataclass
class LayoutSettings(DataClassJsonMixin):
    external_app_url: str = dc_field(metadata=dc_config(field_name="external_app_url"))
    external_css_url: str = dc_field(metadata=dc_config(field_name="external_css_url"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    options: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="options")
    )


@dataclass
class LayoutSettingsRequest(DataClassJsonMixin):
    name: str = dc_field(metadata=dc_config(field_name="name"))
    external_app_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_app_url")
    )
    external_css_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_css_url")
    )
    options: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="options")
    )


@dataclass
class LayoutSettingsResponse(DataClassJsonMixin):
    external_app_url: str = dc_field(metadata=dc_config(field_name="external_app_url"))
    external_css_url: str = dc_field(metadata=dc_config(field_name="external_css_url"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    options: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="options")
    )


@dataclass
class LimitInfo(DataClassJsonMixin):
    limit: int = dc_field(metadata=dc_config(field_name="limit"))
    remaining: int = dc_field(metadata=dc_config(field_name="remaining"))
    reset: int = dc_field(metadata=dc_config(field_name="reset"))


@dataclass
class LimitsSettings(DataClassJsonMixin):
    max_duration_seconds: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_duration_seconds")
    )
    max_participants: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_participants")
    )


@dataclass
class LimitsSettingsRequest(DataClassJsonMixin):
    max_duration_seconds: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_duration_seconds")
    )
    max_participants: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_participants")
    )


@dataclass
class LimitsSettingsResponse(DataClassJsonMixin):
    max_duration_seconds: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_duration_seconds")
    )
    max_participants: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_participants")
    )


@dataclass
class ListBlockListResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    blocklists: "List[Optional[BlockList]]" = dc_field(
        metadata=dc_config(field_name="blocklists")
    )


@dataclass
class ListCallTypeResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    call_types: "Dict[str, CallTypeResponse]" = dc_field(
        metadata=dc_config(field_name="call_types")
    )


@dataclass
class ListChannelTypesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    channel_types: "Dict[str, Optional[ChannelTypeConfig]]" = dc_field(
        metadata=dc_config(field_name="channel_types")
    )


@dataclass
class ListCommandsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    commands: "List[Optional[Command]]" = dc_field(
        metadata=dc_config(field_name="commands")
    )


@dataclass
class ListDevicesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    devices: "List[Optional[Device]]" = dc_field(
        metadata=dc_config(field_name="devices")
    )


@dataclass
class ListExternalStorageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    external_storages: "Dict[str, ExternalStorageResponse]" = dc_field(
        metadata=dc_config(field_name="external_storages")
    )


@dataclass
class ListImportsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    import_tasks: "List[ImportTask]" = dc_field(
        metadata=dc_config(field_name="import_tasks")
    )


@dataclass
class ListPermissionsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    permissions: "List[Permission]" = dc_field(
        metadata=dc_config(field_name="permissions")
    )


@dataclass
class ListPushProvidersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    push_providers: "List[PushProviderResponse]" = dc_field(
        metadata=dc_config(field_name="push_providers")
    )


@dataclass
class ListRecordingsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    recordings: "List[CallRecording]" = dc_field(
        metadata=dc_config(field_name="recordings")
    )


@dataclass
class ListRolesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    roles: "List[Role]" = dc_field(metadata=dc_config(field_name="roles"))


@dataclass
class ListTranscriptionsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    transcriptions: "List[CallTranscription]" = dc_field(
        metadata=dc_config(field_name="transcriptions")
    )


@dataclass
class Location(DataClassJsonMixin):
    continent_code: str = dc_field(metadata=dc_config(field_name="continent_code"))
    country_iso_code: str = dc_field(metadata=dc_config(field_name="country_iso_code"))
    subdivision_iso_code: str = dc_field(
        metadata=dc_config(field_name="subdivision_iso_code")
    )


@dataclass
class MOSStats(DataClassJsonMixin):
    average_score: float = dc_field(metadata=dc_config(field_name="average_score"))
    max_score: float = dc_field(metadata=dc_config(field_name="max_score"))
    min_score: float = dc_field(metadata=dc_config(field_name="min_score"))
    hist_og_ram_duration_seconds: "List[float]" = dc_field(
        metadata=dc_config(field_name="histogram_duration_seconds")
    )


@dataclass
class MarkChannelsReadRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    read_by_channel: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="read_by_channel")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MarkReadRequest(DataClassJsonMixin):
    message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="message_id")
    )
    thread_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thread_id")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MarkReadResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    event: "Optional[MessageReadEvent]" = dc_field(
        default=None, metadata=dc_config(field_name="event")
    )


@dataclass
class MarkUnreadRequest(DataClassJsonMixin):
    message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="message_id")
    )
    thread_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thread_id")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MediaPubSubHint(DataClassJsonMixin):
    audio_published: bool = dc_field(metadata=dc_config(field_name="audio_published"))
    audio_subscribed: bool = dc_field(metadata=dc_config(field_name="audio_subscribed"))
    video_published: bool = dc_field(metadata=dc_config(field_name="video_published"))
    video_subscribed: bool = dc_field(metadata=dc_config(field_name="video_subscribed"))


@dataclass
class MemberRequest(DataClassJsonMixin):
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    role: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="role"))
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )


@dataclass
class MemberResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    role: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="role"))


@dataclass
class MembersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[Optional[ChannelMember]]" = dc_field(
        metadata=dc_config(field_name="members")
    )


@dataclass
class Message(DataClassJsonMixin):
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    deleted_reply_count: int = dc_field(
        metadata=dc_config(field_name="deleted_reply_count")
    )
    html: str = dc_field(metadata=dc_config(field_name="html"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    pinned: bool = dc_field(metadata=dc_config(field_name="pinned"))
    reply_count: int = dc_field(metadata=dc_config(field_name="reply_count"))
    shadowed: bool = dc_field(metadata=dc_config(field_name="shadowed"))
    silent: bool = dc_field(metadata=dc_config(field_name="silent"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: "List[Optional[Attachment]]" = dc_field(
        metadata=dc_config(field_name="attachments")
    )
    latest_reactions: "List[Optional[Reaction]]" = dc_field(
        metadata=dc_config(field_name="latest_reactions")
    )
    mentioned_users: "List[UserObject]" = dc_field(
        metadata=dc_config(field_name="mentioned_users")
    )
    own_reactions: "List[Optional[Reaction]]" = dc_field(
        metadata=dc_config(field_name="own_reactions")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    reaction_counts: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_counts")
    )
    reaction_groups: "Dict[str, Optional[ReactionGroupResponse]]" = dc_field(
        metadata=dc_config(field_name="reaction_groups")
    )
    reaction_scores: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_scores")
    )
    before_message_send_failed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="before_message_send_failed")
    )
    command: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    message_text_updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="message_text_updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    mml: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mml"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    pin_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pin_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    pinned_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pinned_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    poll_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="poll_id")
    )
    quoted_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message_id")
    )
    show_in_channel: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_in_channel")
    )
    thread_participants: "Optional[List[UserObject]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    i18n: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="i18n")
    )
    image_labels: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="image_labels")
    )
    pinned_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="pinned_by")
    )
    poll: "Optional[Poll]" = dc_field(
        default=None, metadata=dc_config(field_name="poll")
    )
    quoted_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MessageActionRequest(DataClassJsonMixin):
    form_data: "Dict[str, str]" = dc_field(metadata=dc_config(field_name="form_data"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MessageChangeSet(DataClassJsonMixin):
    attachments: bool = dc_field(metadata=dc_config(field_name="attachments"))
    custom: bool = dc_field(metadata=dc_config(field_name="custom"))
    html: bool = dc_field(metadata=dc_config(field_name="html"))
    mentioned_user_ids: bool = dc_field(
        metadata=dc_config(field_name="mentioned_user_ids")
    )
    mml: bool = dc_field(metadata=dc_config(field_name="mml"))
    pin: bool = dc_field(metadata=dc_config(field_name="pin"))
    quoted_message_id: bool = dc_field(
        metadata=dc_config(field_name="quoted_message_id")
    )
    silent: bool = dc_field(metadata=dc_config(field_name="silent"))
    text: bool = dc_field(metadata=dc_config(field_name="text"))


@dataclass
class MessageFlag(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_automod: bool = dc_field(
        metadata=dc_config(field_name="created_by_automod")
    )
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    app_roved_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="approved_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    rejected_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="rejected_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    reviewed_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="reviewed_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    details: "Optional[FlagDetails]" = dc_field(
        default=None, metadata=dc_config(field_name="details")
    )
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    moderation_feedback: "Optional[FlagFeedback]" = dc_field(
        default=None, metadata=dc_config(field_name="moderation_feedback")
    )
    moderation_result: "Optional[MessageModerationResult]" = dc_field(
        default=None, metadata=dc_config(field_name="moderation_result")
    )
    reviewed_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="reviewed_by")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MessageHistoryEntry(DataClassJsonMixin):
    message_id: str = dc_field(metadata=dc_config(field_name="message_id"))
    message_updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="message_updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    message_updated_by_id: str = dc_field(
        metadata=dc_config(field_name="message_updated_by_id")
    )
    text: str = dc_field(metadata=dc_config(field_name="text"))
    attachments: "List[Optional[Attachment]]" = dc_field(
        metadata=dc_config(field_name="attachments")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="Custom"))


@dataclass
class MessageModerationResult(DataClassJsonMixin):
    action: str = dc_field(metadata=dc_config(field_name="action"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    message_id: str = dc_field(metadata=dc_config(field_name="message_id"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    user_bad_karma: bool = dc_field(metadata=dc_config(field_name="user_bad_karma"))
    user_karma: float = dc_field(metadata=dc_config(field_name="user_karma"))
    blocked_word: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocked_word")
    )
    blocklist_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_name")
    )
    moderated_by: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="moderated_by")
    )
    ai_moderation_response: "Optional[ModerationResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="ai_moderation_response")
    )
    moderation_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="moderation_thresholds")
    )


@dataclass
class MessagePaginationParams(DataClassJsonMixin):
    pass


@dataclass
class MessageReadEvent(DataClassJsonMixin):
    channel_id: str = dc_field(metadata=dc_config(field_name="channel_id"))
    channel_type: str = dc_field(metadata=dc_config(field_name="channel_type"))
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = dc_field(metadata=dc_config(field_name="type"))
    last_read_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="last_read_message_id")
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    thread: "Optional[Thread]" = dc_field(
        default=None, metadata=dc_config(field_name="thread")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MessageRequest(DataClassJsonMixin):
    html: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="html"))
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    mml: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mml"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    pin_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pin_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    pinned: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="pinned")
    )
    pinned_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pinned_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    poll_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="poll_id")
    )
    quoted_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message_id")
    )
    show_in_channel: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_in_channel")
    )
    silent: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="silent")
    )
    text: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="text"))
    type: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="type"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    attachments: "Optional[List[Optional[Attachment]]]" = dc_field(
        default=None, metadata=dc_config(field_name="attachments")
    )
    mentioned_users: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="mentioned_users")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MessageResponse(DataClassJsonMixin):
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    deleted_reply_count: int = dc_field(
        metadata=dc_config(field_name="deleted_reply_count")
    )
    html: str = dc_field(metadata=dc_config(field_name="html"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    pinned: bool = dc_field(metadata=dc_config(field_name="pinned"))
    reply_count: int = dc_field(metadata=dc_config(field_name="reply_count"))
    shadowed: bool = dc_field(metadata=dc_config(field_name="shadowed"))
    silent: bool = dc_field(metadata=dc_config(field_name="silent"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: "List[Optional[Attachment]]" = dc_field(
        metadata=dc_config(field_name="attachments")
    )
    latest_reactions: "List[ReactionResponse]" = dc_field(
        metadata=dc_config(field_name="latest_reactions")
    )
    mentioned_users: "List[UserResponse]" = dc_field(
        metadata=dc_config(field_name="mentioned_users")
    )
    own_reactions: "List[ReactionResponse]" = dc_field(
        metadata=dc_config(field_name="own_reactions")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    reaction_counts: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_counts")
    )
    reaction_scores: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_scores")
    )
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))
    command: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    message_text_updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="message_text_updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    mml: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mml"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    pin_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pin_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    pinned_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pinned_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    poll_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="poll_id")
    )
    quoted_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message_id")
    )
    show_in_channel: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_in_channel")
    )
    thread_participants: "Optional[List[UserResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    i18n: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="i18n")
    )
    image_labels: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="image_labels")
    )
    pinned_by: "Optional[UserResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="pinned_by")
    )
    poll: "Optional[Poll]" = dc_field(
        default=None, metadata=dc_config(field_name="poll")
    )
    quoted_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message")
    )
    reaction_groups: "Optional[Dict[str, Optional[ReactionGroupResponse]]]" = dc_field(
        default=None, metadata=dc_config(field_name="reaction_groups")
    )


@dataclass
class MessageUpdate(DataClassJsonMixin):
    old_text: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="old_text")
    )
    change_set: "Optional[MessageChangeSet]" = dc_field(
        default=None, metadata=dc_config(field_name="change_set")
    )


@dataclass
class MessageWithChannelResponse(DataClassJsonMixin):
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    deleted_reply_count: int = dc_field(
        metadata=dc_config(field_name="deleted_reply_count")
    )
    html: str = dc_field(metadata=dc_config(field_name="html"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    pinned: bool = dc_field(metadata=dc_config(field_name="pinned"))
    reply_count: int = dc_field(metadata=dc_config(field_name="reply_count"))
    shadowed: bool = dc_field(metadata=dc_config(field_name="shadowed"))
    silent: bool = dc_field(metadata=dc_config(field_name="silent"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: "List[Optional[Attachment]]" = dc_field(
        metadata=dc_config(field_name="attachments")
    )
    latest_reactions: "List[ReactionResponse]" = dc_field(
        metadata=dc_config(field_name="latest_reactions")
    )
    mentioned_users: "List[UserResponse]" = dc_field(
        metadata=dc_config(field_name="mentioned_users")
    )
    own_reactions: "List[ReactionResponse]" = dc_field(
        metadata=dc_config(field_name="own_reactions")
    )
    channel: "ChannelResponse" = dc_field(metadata=dc_config(field_name="channel"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    reaction_counts: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_counts")
    )
    reaction_scores: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_scores")
    )
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))
    command: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    message_text_updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="message_text_updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    mml: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mml"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    pin_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pin_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    pinned_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pinned_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    poll_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="poll_id")
    )
    quoted_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message_id")
    )
    show_in_channel: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_in_channel")
    )
    thread_participants: "Optional[List[UserResponse]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    i18n: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="i18n")
    )
    image_labels: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="image_labels")
    )
    pinned_by: "Optional[UserResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="pinned_by")
    )
    poll: "Optional[Poll]" = dc_field(
        default=None, metadata=dc_config(field_name="poll")
    )
    quoted_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message")
    )
    reaction_groups: "Optional[Dict[str, Optional[ReactionGroupResponse]]]" = dc_field(
        default=None, metadata=dc_config(field_name="reaction_groups")
    )


@dataclass
class ModerationResponse(DataClassJsonMixin):
    action: str = dc_field(metadata=dc_config(field_name="action"))
    explicit: float = dc_field(metadata=dc_config(field_name="explicit"))
    spam: float = dc_field(metadata=dc_config(field_name="spam"))
    toxic: float = dc_field(metadata=dc_config(field_name="toxic"))


@dataclass
class MuteChannelRequest(DataClassJsonMixin):
    expiration: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="expiration")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    channel_cids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="channel_cids")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MuteChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    channel_mutes: "Optional[List[Optional[ChannelMute]]]" = dc_field(
        default=None, metadata=dc_config(field_name="channel_mutes")
    )
    channel_mute: "Optional[ChannelMute]" = dc_field(
        default=None, metadata=dc_config(field_name="channel_mute")
    )
    own_user: "Optional[OwnUser]" = dc_field(
        default=None, metadata=dc_config(field_name="own_user")
    )


@dataclass
class MuteUserRequest(DataClassJsonMixin):
    timeout: int = dc_field(metadata=dc_config(field_name="timeout"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    target_ids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="target_ids")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class MuteUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    mutes: "Optional[List[Optional[UserMute]]]" = dc_field(
        default=None, metadata=dc_config(field_name="mutes")
    )
    non_existing_users: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="non_existing_users")
    )
    mute: "Optional[UserMute]" = dc_field(
        default=None, metadata=dc_config(field_name="mute")
    )
    own_user: "Optional[OwnUser]" = dc_field(
        default=None, metadata=dc_config(field_name="own_user")
    )


@dataclass
class MuteUsersRequest(DataClassJsonMixin):
    audio: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="audio")
    )
    mute_all_users: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mute_all_users")
    )
    muted_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="muted_by_id")
    )
    screenshare: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="screenshare")
    )
    screenshare_audio: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="screenshare_audio")
    )
    video: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="video")
    )
    user_ids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="user_ids")
    )
    muted_by: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="muted_by")
    )


@dataclass
class MuteUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class NoiseCancellationSettings(DataClassJsonMixin):
    mode: str = dc_field(metadata=dc_config(field_name="mode"))


@dataclass
class NotificationSettings(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    call_live_started: "EventNotificationSettings" = dc_field(
        metadata=dc_config(field_name="call_live_started")
    )
    call_missed: "EventNotificationSettings" = dc_field(
        metadata=dc_config(field_name="call_missed")
    )
    call_notification: "EventNotificationSettings" = dc_field(
        metadata=dc_config(field_name="call_notification")
    )
    call_ring: "EventNotificationSettings" = dc_field(
        metadata=dc_config(field_name="call_ring")
    )
    session_started: "EventNotificationSettings" = dc_field(
        metadata=dc_config(field_name="session_started")
    )


@dataclass
class NullBool(DataClassJsonMixin):
    has_value: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="HasValue")
    )
    value: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="Value")
    )


@dataclass
class NullTime(DataClassJsonMixin):
    has_value: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="HasValue")
    )
    value: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="Value",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class OnlyUserID(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))


OwnCapabilityType = NewType("OwnCapabilityType", str)


class OwnCapability:
    BLOCK_USERS: Final[OwnCapabilityType] = "block-users"
    CHANGE_MAX_DURATION: Final[OwnCapabilityType] = "change-max-duration"
    CREATE_CALL: Final[OwnCapabilityType] = "create-call"
    CREATE_REACTION: Final[OwnCapabilityType] = "create-reaction"
    ENABLE_NOISE_CANCELLATION: Final[OwnCapabilityType] = "enable-noise-cancellation"
    END_CALL: Final[OwnCapabilityType] = "end-call"
    JOIN_BACKSTAGE: Final[OwnCapabilityType] = "join-backstage"
    JOIN_CALL: Final[OwnCapabilityType] = "join-call"
    JOIN_ENDED_CALL: Final[OwnCapabilityType] = "join-ended-call"
    MUTE_USERS: Final[OwnCapabilityType] = "mute-users"
    PIN_FOR_EVERYONE: Final[OwnCapabilityType] = "pin-for-everyone"
    READ_CALL: Final[OwnCapabilityType] = "read-call"
    REMOVE_CALL_MEMBER: Final[OwnCapabilityType] = "remove-call-member"
    SCREENSHARE: Final[OwnCapabilityType] = "screenshare"
    SEND_AUDIO: Final[OwnCapabilityType] = "send-audio"
    SEND_VIDEO: Final[OwnCapabilityType] = "send-video"
    START_BROADCAST_CALL: Final[OwnCapabilityType] = "start-broadcast-call"
    START_RECORD_CALL: Final[OwnCapabilityType] = "start-record-call"
    START_TRANSCRIPTION_CALL: Final[OwnCapabilityType] = "start-transcription-call"
    STOP_BROADCAST_CALL: Final[OwnCapabilityType] = "stop-broadcast-call"
    STOP_RECORD_CALL: Final[OwnCapabilityType] = "stop-record-call"
    STOP_TRANSCRIPTION_CALL: Final[OwnCapabilityType] = "stop-transcription-call"
    UPDATE_CALL: Final[OwnCapabilityType] = "update-call"
    UPDATE_CALL_MEMBER: Final[OwnCapabilityType] = "update-call-member"
    UPDATE_CALL_PERMISSIONS: Final[OwnCapabilityType] = "update-call-permissions"
    UPDATE_CALL_SETTINGS: Final[OwnCapabilityType] = "update-call-settings"


@dataclass
class OwnUser(DataClassJsonMixin):
    banned: bool = dc_field(metadata=dc_config(field_name="banned"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    language: str = dc_field(metadata=dc_config(field_name="language"))
    online: bool = dc_field(metadata=dc_config(field_name="online"))
    role: str = dc_field(metadata=dc_config(field_name="role"))
    total_unread_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_count")
    )
    unread_channels: int = dc_field(metadata=dc_config(field_name="unread_channels"))
    unread_count: int = dc_field(metadata=dc_config(field_name="unread_count"))
    unread_threads: int = dc_field(metadata=dc_config(field_name="unread_threads"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    channel_mutes: "List[Optional[ChannelMute]]" = dc_field(
        metadata=dc_config(field_name="channel_mutes")
    )
    devices: "List[Optional[Device]]" = dc_field(
        metadata=dc_config(field_name="devices")
    )
    mutes: "List[Optional[UserMute]]" = dc_field(metadata=dc_config(field_name="mutes"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deactivated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deactivated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    invisible: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="invisible")
    )
    last_active: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_active",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    blocked_user_ids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="blocked_user_ids")
    )
    latest_hidden_channels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="latest_hidden_channels")
    )
    teams: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="teams")
    )
    privacy_settings: "Optional[PrivacySettings]" = dc_field(
        default=None, metadata=dc_config(field_name="privacy_settings")
    )
    push_notifications: "Optional[PushNotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )


@dataclass
class PaginationParams(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )


@dataclass
class PendingMessage(DataClassJsonMixin):
    channel: "Optional[Channel]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="metadata")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class Permission(DataClassJsonMixin):
    action: str = dc_field(metadata=dc_config(field_name="action"))
    custom: bool = dc_field(metadata=dc_config(field_name="custom"))
    description: str = dc_field(metadata=dc_config(field_name="description"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    level: str = dc_field(metadata=dc_config(field_name="level"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    owner: bool = dc_field(metadata=dc_config(field_name="owner"))
    same_team: bool = dc_field(metadata=dc_config(field_name="same_team"))
    tags: List[str] = dc_field(metadata=dc_config(field_name="tags"))
    condition: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="condition")
    )


@dataclass
class PinRequest(DataClassJsonMixin):
    session_id: str = dc_field(metadata=dc_config(field_name="session_id"))
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))


@dataclass
class PinResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class Policy(DataClassJsonMixin):
    action: int = dc_field(metadata=dc_config(field_name="action"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    owner: bool = dc_field(metadata=dc_config(field_name="owner"))
    priority: int = dc_field(metadata=dc_config(field_name="priority"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    resources: List[str] = dc_field(metadata=dc_config(field_name="resources"))
    roles: List[str] = dc_field(metadata=dc_config(field_name="roles"))


@dataclass
class PolicyRequest(DataClassJsonMixin):
    action: str = dc_field(metadata=dc_config(field_name="action"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    owner: bool = dc_field(metadata=dc_config(field_name="owner"))
    priority: int = dc_field(metadata=dc_config(field_name="priority"))
    resources: List[str] = dc_field(metadata=dc_config(field_name="resources"))
    roles: List[str] = dc_field(metadata=dc_config(field_name="roles"))


@dataclass
class Poll(DataClassJsonMixin):
    allow_answers: bool = dc_field(metadata=dc_config(field_name="allow_answers"))
    allow_user_suggested_options: bool = dc_field(
        metadata=dc_config(field_name="allow_user_suggested_options")
    )
    answers_count: int = dc_field(metadata=dc_config(field_name="answers_count"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_id: str = dc_field(metadata=dc_config(field_name="created_by_id"))
    description: str = dc_field(metadata=dc_config(field_name="description"))
    enforce_unique_vote: bool = dc_field(
        metadata=dc_config(field_name="enforce_unique_vote")
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    vote_count: int = dc_field(metadata=dc_config(field_name="vote_count"))
    latest_answers: "List[Optional[PollVote]]" = dc_field(
        metadata=dc_config(field_name="latest_answers")
    )
    options: "List[Optional[PollOption]]" = dc_field(
        metadata=dc_config(field_name="options")
    )
    own_votes: "List[Optional[PollVote]]" = dc_field(
        metadata=dc_config(field_name="own_votes")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="Custom"))
    latest_votes_by_option: "Dict[str, List[Optional[PollVote]]]" = dc_field(
        metadata=dc_config(field_name="latest_votes_by_option")
    )
    vote_counts_by_option: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="vote_counts_by_option")
    )
    is_closed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_closed")
    )
    max_votes_allowed: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_votes_allowed")
    )
    voting_visibility: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="voting_visibility")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )


@dataclass
class PollOption(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))


@dataclass
class PollOptionInput(DataClassJsonMixin):
    text: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="text"))
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )


@dataclass
class PollOptionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    poll_option: "PollOptionResponseData" = dc_field(
        metadata=dc_config(field_name="poll_option")
    )


@dataclass
class PollOptionResponseData(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))


@dataclass
class PollResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    poll: "PollResponseData" = dc_field(metadata=dc_config(field_name="poll"))


@dataclass
class PollResponseData(DataClassJsonMixin):
    allow_answers: bool = dc_field(metadata=dc_config(field_name="allow_answers"))
    allow_user_suggested_options: bool = dc_field(
        metadata=dc_config(field_name="allow_user_suggested_options")
    )
    answers_count: int = dc_field(metadata=dc_config(field_name="answers_count"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_id: str = dc_field(metadata=dc_config(field_name="created_by_id"))
    description: str = dc_field(metadata=dc_config(field_name="description"))
    enforce_unique_vote: bool = dc_field(
        metadata=dc_config(field_name="enforce_unique_vote")
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    vote_count: int = dc_field(metadata=dc_config(field_name="vote_count"))
    voting_visibility: str = dc_field(
        metadata=dc_config(field_name="voting_visibility")
    )
    options: "List[Optional[PollOptionResponseData]]" = dc_field(
        metadata=dc_config(field_name="options")
    )
    own_votes: "List[Optional[PollVoteResponseData]]" = dc_field(
        metadata=dc_config(field_name="own_votes")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="Custom"))
    latest_votes_by_option: "Dict[str, List[Optional[PollVoteResponseData]]]" = (
        dc_field(metadata=dc_config(field_name="latest_votes_by_option"))
    )
    vote_counts_by_option: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="vote_counts_by_option")
    )
    is_closed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_closed")
    )
    max_votes_allowed: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_votes_allowed")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )


@dataclass
class PollVote(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    option_id: str = dc_field(metadata=dc_config(field_name="option_id"))
    poll_id: str = dc_field(metadata=dc_config(field_name="poll_id"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    answer_text: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="answer_text")
    )
    is_answer: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_answer")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class PollVoteResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    vote: "Optional[PollVoteResponseData]" = dc_field(
        default=None, metadata=dc_config(field_name="vote")
    )


@dataclass
class PollVoteResponseData(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    option_id: str = dc_field(metadata=dc_config(field_name="option_id"))
    poll_id: str = dc_field(metadata=dc_config(field_name="poll_id"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    answer_text: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="answer_text")
    )
    is_answer: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_answer")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class PollVotesResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    votes: "List[Optional[PollVoteResponseData]]" = dc_field(
        metadata=dc_config(field_name="votes")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class PrivacySettings(DataClassJsonMixin):
    read_receipts: "Optional[ReadReceipts]" = dc_field(
        default=None, metadata=dc_config(field_name="read_receipts")
    )
    typing_indicators: "Optional[TypingIndicators]" = dc_field(
        default=None, metadata=dc_config(field_name="typing_indicators")
    )


@dataclass
class PublishedTrackInfo(DataClassJsonMixin):
    codec_mime_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="codec_mime_type")
    )
    duration_seconds: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="duration_seconds")
    )
    track_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="track_type")
    )


@dataclass
class PushConfig(DataClassJsonMixin):
    version: str = dc_field(metadata=dc_config(field_name="version"))
    offline_only: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="offline_only")
    )


@dataclass
class PushNotificationFields(DataClassJsonMixin):
    offline_only: bool = dc_field(metadata=dc_config(field_name="offline_only"))
    version: str = dc_field(metadata=dc_config(field_name="version"))
    apn: "APNConfigFields" = dc_field(metadata=dc_config(field_name="apn"))
    firebase: "FirebaseConfigFields" = dc_field(
        metadata=dc_config(field_name="firebase")
    )
    huawei: "HuaweiConfigFields" = dc_field(metadata=dc_config(field_name="huawei"))
    xiaomi: "XiaomiConfigFields" = dc_field(metadata=dc_config(field_name="xiaomi"))
    providers: "Optional[List[Optional[PushProvider]]]" = dc_field(
        default=None, metadata=dc_config(field_name="providers")
    )


@dataclass
class PushNotificationSettings(DataClassJsonMixin):
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="disabled")
    )
    disabled_until: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="disabled_until",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )


@dataclass
class PushNotificationSettingsInput(DataClassJsonMixin):
    disabled: "Optional[NullBool]" = dc_field(
        default=None, metadata=dc_config(field_name="disabled")
    )
    disabled_until: "Optional[NullTime]" = dc_field(
        default=None, metadata=dc_config(field_name="disabled_until")
    )


@dataclass
class PushProvider(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    apn_auth_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_auth_key")
    )
    apn_auth_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_auth_type")
    )
    apn_development: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="apn_development")
    )
    apn_host: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_host")
    )
    apn_key_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_key_id")
    )
    apn_notification_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_notification_template")
    )
    apn_p12_cert: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_p12_cert")
    )
    apn_team_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_team_id")
    )
    apn_topic: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_topic")
    )
    description: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="description")
    )
    disabled_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="disabled_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    disabled_reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="disabled_reason")
    )
    firebase_apn_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_apn_template")
    )
    firebase_credentials: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_credentials")
    )
    firebase_data_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_data_template")
    )
    firebase_host: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_host")
    )
    firebase_notification_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_notification_template")
    )
    firebase_server_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_server_key")
    )
    huawei_app_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="huawei_app_id")
    )
    huawei_app_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="huawei_app_secret")
    )
    xiaomi_app_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="xiaomi_app_secret")
    )
    xiaomi_package_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="xiaomi_package_name")
    )


@dataclass
class PushProviderResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    name: str = dc_field(metadata=dc_config(field_name="name"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    apn_auth_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_auth_key")
    )
    apn_auth_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_auth_type")
    )
    apn_development: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="apn_development")
    )
    apn_host: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_host")
    )
    apn_key_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_key_id")
    )
    apn_p12_cert: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_p12_cert")
    )
    apn_sandbox_certificate: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="apn_sandbox_certificate")
    )
    apn_supports_remote_notifications: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="apn_supports_remote_notifications")
    )
    apn_supports_voip_notifications: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="apn_supports_voip_notifications")
    )
    apn_team_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_team_id")
    )
    apn_topic: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="apn_topic")
    )
    description: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="description")
    )
    disabled_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="disabled_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    disabled_reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="disabled_reason")
    )
    firebase_apn_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_apn_template")
    )
    firebase_credentials: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_credentials")
    )
    firebase_data_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_data_template")
    )
    firebase_host: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_host")
    )
    firebase_notification_template: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_notification_template")
    )
    firebase_server_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="firebase_server_key")
    )
    huawei_app_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="huawei_app_id")
    )
    huawei_app_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="huawei_app_secret")
    )
    xiaomi_app_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="xiaomi_app_secret")
    )
    xiaomi_package_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="xiaomi_package_name")
    )


@dataclass
class QueryBannedUsersRequest(DataClassJsonMixin):
    filter_conditions: Dict[str, object] = dc_field(
        metadata=dc_config(field_name="filter_conditions")
    )
    exclude_expired_bans: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="exclude_expired_bans")
    )
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryBannedUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    bans: "List[Optional[BanResponse]]" = dc_field(
        metadata=dc_config(field_name="bans")
    )


@dataclass
class QueryCallMembersRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter_conditions")
    )


@dataclass
class QueryCallMembersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryCallStatsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter_conditions")
    )


@dataclass
class QueryCallStatsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    reports: "List[CallStatsReportSummaryResponse]" = dc_field(
        metadata=dc_config(field_name="reports")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryCallsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter_conditions")
    )


@dataclass
class QueryCallsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    calls: "List[CallStateResponseFields]" = dc_field(
        metadata=dc_config(field_name="calls")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryChannelsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    member_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="member_limit")
    )
    message_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="message_limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    state: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="state")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter_conditions")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryChannelsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    channels: "List[ChannelStateResponseFields]" = dc_field(
        metadata=dc_config(field_name="channels")
    )


@dataclass
class QueryMembersRequest(DataClassJsonMixin):
    type: str = dc_field(metadata=dc_config(field_name="type"))
    filter_conditions: Dict[str, object] = dc_field(
        metadata=dc_config(field_name="filter_conditions")
    )
    id: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="id"))
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    members: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="members")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryMessageFlagsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    show_deleted_messages: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_deleted_messages")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter_conditions")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryMessageFlagsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    flags: "List[Optional[MessageFlag]]" = dc_field(
        metadata=dc_config(field_name="flags")
    )


@dataclass
class QueryMessageHistoryRequest(DataClassJsonMixin):
    filter: Dict[str, object] = dc_field(metadata=dc_config(field_name="filter"))
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )


@dataclass
class QueryMessageHistoryResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message_history: "List[Optional[MessageHistoryEntry]]" = dc_field(
        metadata=dc_config(field_name="message_history")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryPollVotesRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter")
    )


@dataclass
class QueryPollsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter")
    )


@dataclass
class QueryPollsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    polls: "List[PollResponseData]" = dc_field(metadata=dc_config(field_name="polls"))
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryReactionsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    filter: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="filter")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryReactionsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    reactions: "List[ReactionResponse]" = dc_field(
        metadata=dc_config(field_name="reactions")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryThreadsRequest(DataClassJsonMixin):
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    member_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="member_limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    participant_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="participant_limit")
    )
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))
    reply_limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reply_limit")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryThreadsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    threads: "List[ThreadStateResponse]" = dc_field(
        metadata=dc_config(field_name="threads")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    prev: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="prev"))


@dataclass
class QueryUsersPayload(DataClassJsonMixin):
    filter_conditions: Dict[str, object] = dc_field(
        metadata=dc_config(field_name="filter_conditions")
    )
    include_deactivated_users: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="include_deactivated_users")
    )
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    presence: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="presence")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class QueryUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    users: "List[FullUserResponse]" = dc_field(metadata=dc_config(field_name="users"))


@dataclass
class RTMPIngress(DataClassJsonMixin):
    address: str = dc_field(metadata=dc_config(field_name="address"))


@dataclass
class Reaction(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    message_id: str = dc_field(metadata=dc_config(field_name="message_id"))
    score: int = dc_field(metadata=dc_config(field_name="score"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ReactionGroupResponse(DataClassJsonMixin):
    count: int = dc_field(metadata=dc_config(field_name="count"))
    first_reaction_at: datetime = dc_field(
        metadata=dc_config(
            field_name="first_reaction_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    last_reaction_at: datetime = dc_field(
        metadata=dc_config(
            field_name="last_reaction_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    sum_scores: int = dc_field(metadata=dc_config(field_name="sum_scores"))


@dataclass
class ReactionRemovalResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    reaction: "Optional[Reaction]" = dc_field(
        default=None, metadata=dc_config(field_name="reaction")
    )


@dataclass
class ReactionRequest(DataClassJsonMixin):
    type: str = dc_field(metadata=dc_config(field_name="type"))
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    score: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="score")
    )
    updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ReactionResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    message_id: str = dc_field(metadata=dc_config(field_name="message_id"))
    score: int = dc_field(metadata=dc_config(field_name="score"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))


@dataclass
class ReactivateUserRequest(DataClassJsonMixin):
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    name: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="name"))
    restore_messages: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="restore_messages")
    )


@dataclass
class ReactivateUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ReactivateUsersRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))
    created_by_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="created_by_id")
    )
    restore_channels: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="restore_channels")
    )
    restore_messages: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="restore_messages")
    )


@dataclass
class ReactivateUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    task_id: str = dc_field(metadata=dc_config(field_name="task_id"))


@dataclass
class Read(DataClassJsonMixin):
    last_read: datetime = dc_field(
        metadata=dc_config(
            field_name="last_read",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    unread_messages: int = dc_field(metadata=dc_config(field_name="unread_messages"))
    last_read_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="last_read_message_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ReadReceipts(DataClassJsonMixin):
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )


@dataclass
class ReadStateResponse(DataClassJsonMixin):
    last_read: datetime = dc_field(
        metadata=dc_config(
            field_name="last_read",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    unread_messages: int = dc_field(metadata=dc_config(field_name="unread_messages"))
    user: "UserResponse" = dc_field(metadata=dc_config(field_name="user"))
    last_read_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="last_read_message_id")
    )


@dataclass
class RecordSettings(DataClassJsonMixin):
    audio_only: bool = dc_field(metadata=dc_config(field_name="audio_only"))
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    quality: str = dc_field(metadata=dc_config(field_name="quality"))
    layout: "Optional[LayoutSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="layout")
    )


@dataclass
class RecordSettingsRequest(DataClassJsonMixin):
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    audio_only: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="audio_only")
    )
    quality: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quality")
    )
    layout: "Optional[LayoutSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="layout")
    )


@dataclass
class RecordSettingsResponse(DataClassJsonMixin):
    audio_only: bool = dc_field(metadata=dc_config(field_name="audio_only"))
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    quality: str = dc_field(metadata=dc_config(field_name="quality"))
    layout: "LayoutSettingsResponse" = dc_field(metadata=dc_config(field_name="layout"))


@dataclass
class Response(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class RestoreUsersRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))


@dataclass
class RingSettings(DataClassJsonMixin):
    auto_cancel_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="auto_cancel_timeout_ms")
    )
    incoming_call_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="incoming_call_timeout_ms")
    )
    missed_call_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="missed_call_timeout_ms")
    )


@dataclass
class RingSettingsRequest(DataClassJsonMixin):
    auto_cancel_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="auto_cancel_timeout_ms")
    )
    incoming_call_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="incoming_call_timeout_ms")
    )
    missed_call_timeout_ms: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="missed_call_timeout_ms")
    )


@dataclass
class RingSettingsResponse(DataClassJsonMixin):
    auto_cancel_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="auto_cancel_timeout_ms")
    )
    incoming_call_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="incoming_call_timeout_ms")
    )
    missed_call_timeout_ms: int = dc_field(
        metadata=dc_config(field_name="missed_call_timeout_ms")
    )


@dataclass
class Role(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: bool = dc_field(metadata=dc_config(field_name="custom"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    scopes: List[str] = dc_field(metadata=dc_config(field_name="scopes"))


@dataclass
class S3Request(DataClassJsonMixin):
    s3_region: str = dc_field(metadata=dc_config(field_name="s3_region"))
    s3_api_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="s3_api_key")
    )
    s3_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="s3_secret")
    )


@dataclass
class SFULocationResponse(DataClassJsonMixin):
    datacenter: str = dc_field(metadata=dc_config(field_name="datacenter"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    coordinates: "Coordinates" = dc_field(metadata=dc_config(field_name="coordinates"))
    location: "Location" = dc_field(metadata=dc_config(field_name="location"))


@dataclass
class ScreensharingSettings(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    target_resolution: "Optional[TargetResolution]" = dc_field(
        default=None, metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class ScreensharingSettingsRequest(DataClassJsonMixin):
    access_request_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="access_request_enabled")
    )
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )
    target_resolution: "Optional[TargetResolution]" = dc_field(
        default=None, metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class ScreensharingSettingsResponse(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    target_resolution: "Optional[TargetResolution]" = dc_field(
        default=None, metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class SearchRequest(DataClassJsonMixin):
    filter_conditions: Dict[str, object] = dc_field(
        metadata=dc_config(field_name="filter_conditions")
    )
    limit: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="limit")
    )
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    offset: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="offset")
    )
    query: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="query")
    )
    sort: "Optional[List[Optional[SortParam]]]" = dc_field(
        default=None, metadata=dc_config(field_name="sort")
    )
    message_filter_conditions: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="message_filter_conditions")
    )


@dataclass
class SearchResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    results: "List[SearchResult]" = dc_field(metadata=dc_config(field_name="results"))
    next: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="next"))
    previous: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="previous")
    )
    results_warning: "Optional[SearchWarning]" = dc_field(
        default=None, metadata=dc_config(field_name="results_warning")
    )


@dataclass
class SearchResult(DataClassJsonMixin):
    message: "Optional[SearchResultMessage]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )


@dataclass
class SearchResultMessage(DataClassJsonMixin):
    cid: str = dc_field(metadata=dc_config(field_name="cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    deleted_reply_count: int = dc_field(
        metadata=dc_config(field_name="deleted_reply_count")
    )
    html: str = dc_field(metadata=dc_config(field_name="html"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    pinned: bool = dc_field(metadata=dc_config(field_name="pinned"))
    reply_count: int = dc_field(metadata=dc_config(field_name="reply_count"))
    shadowed: bool = dc_field(metadata=dc_config(field_name="shadowed"))
    silent: bool = dc_field(metadata=dc_config(field_name="silent"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    type: str = dc_field(metadata=dc_config(field_name="type"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    attachments: "List[Optional[Attachment]]" = dc_field(
        metadata=dc_config(field_name="attachments")
    )
    latest_reactions: "List[Optional[Reaction]]" = dc_field(
        metadata=dc_config(field_name="latest_reactions")
    )
    mentioned_users: "List[UserObject]" = dc_field(
        metadata=dc_config(field_name="mentioned_users")
    )
    own_reactions: "List[Optional[Reaction]]" = dc_field(
        metadata=dc_config(field_name="own_reactions")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    reaction_counts: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_counts")
    )
    reaction_groups: "Dict[str, Optional[ReactionGroupResponse]]" = dc_field(
        metadata=dc_config(field_name="reaction_groups")
    )
    reaction_scores: "Dict[str, int]" = dc_field(
        metadata=dc_config(field_name="reaction_scores")
    )
    before_message_send_failed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="before_message_send_failed")
    )
    command: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    message_text_updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="message_text_updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    mml: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="mml"))
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    pin_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pin_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    pinned_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="pinned_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    poll_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="poll_id")
    )
    quoted_message_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message_id")
    )
    show_in_channel: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="show_in_channel")
    )
    thread_participants: "Optional[List[UserObject]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    i18n: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="i18n")
    )
    image_labels: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="image_labels")
    )
    pinned_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="pinned_by")
    )
    poll: "Optional[Poll]" = dc_field(
        default=None, metadata=dc_config(field_name="poll")
    )
    quoted_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="quoted_message")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class SearchWarning(DataClassJsonMixin):
    warning_code: int = dc_field(metadata=dc_config(field_name="warning_code"))
    warning_description: str = dc_field(
        metadata=dc_config(field_name="warning_description")
    )
    channel_search_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="channel_search_count")
    )
    channel_search_cids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="channel_search_cids")
    )


@dataclass
class SendCallEventRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class SendCallEventResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class SendEventRequest(DataClassJsonMixin):
    event: "EventRequest" = dc_field(metadata=dc_config(field_name="event"))


@dataclass
class SendMessageRequest(DataClassJsonMixin):
    message: "MessageRequest" = dc_field(metadata=dc_config(field_name="message"))
    force_moderation: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="force_moderation")
    )
    keep_channel_hidden: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="keep_channel_hidden")
    )
    pending: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="pending")
    )
    skip_enrich_url: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_enrich_url")
    )
    skip_push: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_push")
    )
    pending_message_metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_message_metadata")
    )


@dataclass
class SendMessageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "MessageResponse" = dc_field(metadata=dc_config(field_name="message"))
    pending_message_metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_message_metadata")
    )


@dataclass
class SendReactionRequest(DataClassJsonMixin):
    reaction: "ReactionRequest" = dc_field(metadata=dc_config(field_name="reaction"))
    enforce_unique: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enforce_unique")
    )
    skip_push: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_push")
    )


@dataclass
class SendReactionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "MessageResponse" = dc_field(metadata=dc_config(field_name="message"))
    reaction: "ReactionResponse" = dc_field(metadata=dc_config(field_name="reaction"))


@dataclass
class SendUserCustomEventRequest(DataClassJsonMixin):
    event: "UserCustomEventRequest" = dc_field(metadata=dc_config(field_name="event"))


@dataclass
class ShowChannelRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ShowChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class SortParam(DataClassJsonMixin):
    direction: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="direction")
    )
    field: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="field")
    )


@dataclass
class StartHLSBroadcastingRequest(DataClassJsonMixin):
    pass


@dataclass
class StartHLSBroadcastingResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    playlist_url: str = dc_field(metadata=dc_config(field_name="playlist_url"))


@dataclass
class StartRecordingRequest(DataClassJsonMixin):
    recording_external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="recording_external_storage")
    )


@dataclass
class StartRecordingResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class StartTranscriptionRequest(DataClassJsonMixin):
    transcription_external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="transcription_external_storage")
    )


@dataclass
class StartTranscriptionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class Stats(DataClassJsonMixin):
    average_seconds: float = dc_field(metadata=dc_config(field_name="average_seconds"))
    max_seconds: float = dc_field(metadata=dc_config(field_name="max_seconds"))


@dataclass
class StopHLSBroadcastingRequest(DataClassJsonMixin):
    pass


@dataclass
class StopHLSBroadcastingResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class StopLiveRequest(DataClassJsonMixin):
    pass


@dataclass
class StopLiveResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class StopRecordingRequest(DataClassJsonMixin):
    pass


@dataclass
class StopRecordingResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class StopTranscriptionRequest(DataClassJsonMixin):
    pass


@dataclass
class StopTranscriptionResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class Subsession(DataClassJsonMixin):
    ended_at: int = dc_field(metadata=dc_config(field_name="ended_at"))
    joined_at: int = dc_field(metadata=dc_config(field_name="joined_at"))
    sfu_id: str = dc_field(metadata=dc_config(field_name="sfu_id"))
    pub_sub_hint: "Optional[MediaPubSubHint]" = dc_field(
        default=None, metadata=dc_config(field_name="pub_sub_hint")
    )


@dataclass
class TargetResolution(DataClassJsonMixin):
    bitrate: int = dc_field(metadata=dc_config(field_name="bitrate"))
    height: int = dc_field(metadata=dc_config(field_name="height"))
    width: int = dc_field(metadata=dc_config(field_name="width"))


@dataclass
class Thread(DataClassJsonMixin):
    channel_cid: str = dc_field(metadata=dc_config(field_name="channel_cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    parent_message_id: str = dc_field(
        metadata=dc_config(field_name="parent_message_id")
    )
    title: str = dc_field(metadata=dc_config(field_name="title"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    participant_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="participant_count")
    )
    reply_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reply_count")
    )
    thread_participants: "Optional[List[Optional[ThreadParticipant]]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    channel: "Optional[Channel]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    parent_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="parent_message")
    )


@dataclass
class ThreadParticipant(DataClassJsonMixin):
    app_pk: int = dc_field(metadata=dc_config(field_name="app_pk"))
    channel_cid: str = dc_field(metadata=dc_config(field_name="channel_cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    last_read_at: datetime = dc_field(
        metadata=dc_config(
            field_name="last_read_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    last_thread_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_thread_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    left_thread_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="left_thread_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    thread_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="thread_id")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class ThreadResponse(DataClassJsonMixin):
    channel_cid: str = dc_field(metadata=dc_config(field_name="channel_cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_user_id: str = dc_field(
        metadata=dc_config(field_name="created_by_user_id")
    )
    parent_message_id: str = dc_field(
        metadata=dc_config(field_name="parent_message_id")
    )
    title: str = dc_field(metadata=dc_config(field_name="title"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    participant_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="participant_count")
    )
    reply_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reply_count")
    )
    thread_participants: "Optional[List[Optional[ThreadParticipant]]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    parent_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="parent_message")
    )


@dataclass
class ThreadState(DataClassJsonMixin):
    channel_cid: str = dc_field(metadata=dc_config(field_name="channel_cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    parent_message_id: str = dc_field(
        metadata=dc_config(field_name="parent_message_id")
    )
    title: str = dc_field(metadata=dc_config(field_name="title"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    latest_replies: "List[Optional[Message]]" = dc_field(
        metadata=dc_config(field_name="latest_replies")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    participant_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="participant_count")
    )
    reply_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reply_count")
    )
    read: "Optional[List[Optional[Read]]]" = dc_field(
        default=None, metadata=dc_config(field_name="read")
    )
    thread_participants: "Optional[List[Optional[ThreadParticipant]]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    channel: "Optional[Channel]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    parent_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="parent_message")
    )


@dataclass
class ThreadStateResponse(DataClassJsonMixin):
    channel_cid: str = dc_field(metadata=dc_config(field_name="channel_cid"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    created_by_user_id: str = dc_field(
        metadata=dc_config(field_name="created_by_user_id")
    )
    parent_message_id: str = dc_field(
        metadata=dc_config(field_name="parent_message_id")
    )
    title: str = dc_field(metadata=dc_config(field_name="title"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    latest_replies: "List[Optional[Message]]" = dc_field(
        metadata=dc_config(field_name="latest_replies")
    )
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    last_message_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_message_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    participant_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="participant_count")
    )
    reply_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reply_count")
    )
    read: "Optional[List[Optional[Read]]]" = dc_field(
        default=None, metadata=dc_config(field_name="read")
    )
    thread_participants: "Optional[List[Optional[ThreadParticipant]]]" = dc_field(
        default=None, metadata=dc_config(field_name="thread_participants")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    parent_message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="parent_message")
    )


@dataclass
class Thresholds(DataClassJsonMixin):
    explicit: "Optional[LabelThresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="explicit")
    )
    spam: "Optional[LabelThresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="spam")
    )
    toxic: "Optional[LabelThresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="toxic")
    )


@dataclass
class ThumbnailResponse(DataClassJsonMixin):
    image_url: str = dc_field(metadata=dc_config(field_name="image_url"))


@dataclass
class ThumbnailsSettings(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))


@dataclass
class ThumbnailsSettingsRequest(DataClassJsonMixin):
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )


@dataclass
class ThumbnailsSettingsResponse(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))


@dataclass
class TranscriptionSettings(DataClassJsonMixin):
    closed_caption_mode: str = dc_field(
        metadata=dc_config(field_name="closed_caption_mode")
    )
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    languages: List[str] = dc_field(metadata=dc_config(field_name="languages"))


@dataclass
class TranscriptionSettingsRequest(DataClassJsonMixin):
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    closed_caption_mode: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="closed_caption_mode")
    )
    languages: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="languages")
    )


@dataclass
class TranscriptionSettingsResponse(DataClassJsonMixin):
    closed_caption_mode: str = dc_field(
        metadata=dc_config(field_name="closed_caption_mode")
    )
    mode: str = dc_field(metadata=dc_config(field_name="mode"))
    languages: List[str] = dc_field(metadata=dc_config(field_name="languages"))


@dataclass
class TranslateMessageRequest(DataClassJsonMixin):
    language: str = dc_field(metadata=dc_config(field_name="language"))


@dataclass
class TruncateChannelRequest(DataClassJsonMixin):
    hard_delete: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hard_delete")
    )
    skip_push: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_push")
    )
    truncated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="truncated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    message: "Optional[MessageRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class TruncateChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )


@dataclass
class TypingIndicators(DataClassJsonMixin):
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )


@dataclass
class UnblockUserRequest(DataClassJsonMixin):
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))


@dataclass
class UnblockUserResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class UnblockUsersRequest(DataClassJsonMixin):
    blocked_user_id: str = dc_field(metadata=dc_config(field_name="blocked_user_id"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UnblockUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class UnmuteChannelRequest(DataClassJsonMixin):
    expiration: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="expiration")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    channel_cids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="channel_cids")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UnmuteResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    non_existing_users: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="non_existing_users")
    )


@dataclass
class UnmuteUserRequest(DataClassJsonMixin):
    timeout: int = dc_field(metadata=dc_config(field_name="timeout"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    target_ids: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="target_ids")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UnpinRequest(DataClassJsonMixin):
    session_id: str = dc_field(metadata=dc_config(field_name="session_id"))
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))


@dataclass
class UnpinResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class UnreadCountsBatchRequest(DataClassJsonMixin):
    user_ids: List[str] = dc_field(metadata=dc_config(field_name="user_ids"))


@dataclass
class UnreadCountsBatchResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    counts_by_user: "Dict[str, Optional[UnreadCountsResponse]]" = dc_field(
        metadata=dc_config(field_name="counts_by_user")
    )


@dataclass
class UnreadCountsChannel(DataClassJsonMixin):
    channel_id: str = dc_field(metadata=dc_config(field_name="channel_id"))
    last_read: datetime = dc_field(
        metadata=dc_config(
            field_name="last_read",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    unread_count: int = dc_field(metadata=dc_config(field_name="unread_count"))


@dataclass
class UnreadCountsChannelType(DataClassJsonMixin):
    channel_count: int = dc_field(metadata=dc_config(field_name="channel_count"))
    channel_type: str = dc_field(metadata=dc_config(field_name="channel_type"))
    unread_count: int = dc_field(metadata=dc_config(field_name="unread_count"))


@dataclass
class UnreadCountsResponse(DataClassJsonMixin):
    total_unread_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_count")
    )
    total_unread_threads_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_threads_count")
    )
    channel_type: "List[UnreadCountsChannelType]" = dc_field(
        metadata=dc_config(field_name="channel_type")
    )
    channels: "List[UnreadCountsChannel]" = dc_field(
        metadata=dc_config(field_name="channels")
    )
    threads: "List[UnreadCountsThread]" = dc_field(
        metadata=dc_config(field_name="threads")
    )


@dataclass
class UnreadCountsThread(DataClassJsonMixin):
    last_read: datetime = dc_field(
        metadata=dc_config(
            field_name="last_read",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    last_read_message_id: str = dc_field(
        metadata=dc_config(field_name="last_read_message_id")
    )
    parent_message_id: str = dc_field(
        metadata=dc_config(field_name="parent_message_id")
    )
    unread_count: int = dc_field(metadata=dc_config(field_name="unread_count"))


@dataclass
class UpdateAppRequest(DataClassJsonMixin):
    async_url_enrich_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="async_url_enrich_enabled")
    )
    auto_translation_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="auto_translation_enabled")
    )
    before_message_send_hook_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="before_message_send_hook_url")
    )
    cdn_expiration_seconds: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="cdn_expiration_seconds")
    )
    channel_hide_members_only: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="channel_hide_members_only")
    )
    custom_action_handler_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="custom_action_handler_url")
    )
    disable_auth_checks: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="disable_auth_checks")
    )
    disable_permissions_checks: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="disable_permissions_checks")
    )
    enforce_unique_usernames: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="enforce_unique_usernames")
    )
    image_moderation_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="image_moderation_enabled")
    )
    migrate_permissions_to_v2: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="migrate_permissions_to_v2")
    )
    multi_tenant_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="multi_tenant_enabled")
    )
    permission_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="permission_version")
    )
    reminders_interval: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reminders_interval")
    )
    reminders_max_members: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="reminders_max_members")
    )
    revoke_tokens_issued_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="revoke_tokens_issued_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    sns_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_key")
    )
    sns_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_secret")
    )
    sns_topic_arn: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sns_topic_arn")
    )
    sqs_key: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_key")
    )
    sqs_secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_secret")
    )
    sqs_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sqs_url")
    )
    video_provider: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="video_provider")
    )
    webhook_url: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="webhook_url")
    )
    image_moderation_block_labels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="image_moderation_block_labels")
    )
    image_moderation_labels: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="image_moderation_labels")
    )
    user_search_disallowed_roles: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="user_search_disallowed_roles")
    )
    webhook_events: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="webhook_events")
    )
    agora_options: "Optional[Config]" = dc_field(
        default=None, metadata=dc_config(field_name="agora_options")
    )
    apn_config: "Optional[APNConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="apn_config")
    )
    async_moderation_config: "Optional[AsyncModerationConfiguration]" = dc_field(
        default=None, metadata=dc_config(field_name="async_moderation_config")
    )
    datadog_info: "Optional[DataDogInfo]" = dc_field(
        default=None, metadata=dc_config(field_name="datadog_info")
    )
    file_upload_config: "Optional[FileUploadConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="file_upload_config")
    )
    firebase_config: "Optional[FirebaseConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="firebase_config")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )
    hms_options: "Optional[Config]" = dc_field(
        default=None, metadata=dc_config(field_name="hms_options")
    )
    huawei_config: "Optional[HuaweiConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="huawei_config")
    )
    image_upload_config: "Optional[FileUploadConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="image_upload_config")
    )
    push_config: "Optional[PushConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="push_config")
    )
    xiaomi_config: "Optional[XiaomiConfig]" = dc_field(
        default=None, metadata=dc_config(field_name="xiaomi_config")
    )


@dataclass
class UpdateBlockListRequest(DataClassJsonMixin):
    words: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="words")
    )


@dataclass
class UpdateCallMembersRequest(DataClassJsonMixin):
    remove_members: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="remove_members")
    )
    update_members: "Optional[List[MemberRequest]]" = dc_field(
        default=None, metadata=dc_config(field_name="update_members")
    )


@dataclass
class UpdateCallMembersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))


@dataclass
class UpdateCallRequest(DataClassJsonMixin):
    starts_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="starts_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    settings_override: "Optional[CallSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="settings_override")
    )


@dataclass
class UpdateCallResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[MemberResponse]" = dc_field(metadata=dc_config(field_name="members"))
    own_capabilities: "List[OwnCapability]" = dc_field(
        metadata=dc_config(field_name="own_capabilities")
    )
    call: "CallResponse" = dc_field(metadata=dc_config(field_name="call"))


@dataclass
class UpdateCallTypeRequest(DataClassJsonMixin):
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )
    notification_settings: "Optional[NotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="notification_settings")
    )
    settings: "Optional[CallSettingsRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="settings")
    )


@dataclass
class UpdateCallTypeResponse(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    notification_settings: "NotificationSettings" = dc_field(
        metadata=dc_config(field_name="notification_settings")
    )
    settings: "CallSettingsResponse" = dc_field(
        metadata=dc_config(field_name="settings")
    )
    external_storage: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="external_storage")
    )


@dataclass
class UpdateChannelPartialRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    unset: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="unset")
    )
    set: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="set")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdateChannelPartialResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[Optional[ChannelMember]]" = dc_field(
        metadata=dc_config(field_name="members")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )


@dataclass
class UpdateChannelRequest(DataClassJsonMixin):
    accept_invite: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="accept_invite")
    )
    cooldown: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="cooldown")
    )
    hide_history: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="hide_history")
    )
    reject_invite: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="reject_invite")
    )
    skip_push: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_push")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    add_members: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="add_members")
    )
    add_moderators: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="add_moderators")
    )
    assign_roles: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="assign_roles")
    )
    demote_moderators: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="demote_moderators")
    )
    invites: "Optional[List[Optional[ChannelMember]]]" = dc_field(
        default=None, metadata=dc_config(field_name="invites")
    )
    remove_members: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="remove_members")
    )
    data: "Optional[ChannelInput]" = dc_field(
        default=None, metadata=dc_config(field_name="data")
    )
    message: "Optional[MessageRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdateChannelResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    members: "List[Optional[ChannelMember]]" = dc_field(
        metadata=dc_config(field_name="members")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )


@dataclass
class UpdateChannelTypeRequest(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    connect_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="connect_events")
    )
    custom_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="custom_events")
    )
    mark_messages_pending: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mark_messages_pending")
    )
    mutes: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="mutes")
    )
    polls: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="polls")
    )
    push_notifications: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )
    quotes: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="quotes")
    )
    reactions: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="reactions")
    )
    read_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="read_events")
    )
    reminders: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="reminders")
    )
    replies: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="replies")
    )
    search: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="search")
    )
    typing_events: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="typing_events")
    )
    uploads: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="uploads")
    )
    url_enrichment: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="url_enrichment")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    commands: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="commands")
    )
    permissions: "Optional[List[PolicyRequest]]" = dc_field(
        default=None, metadata=dc_config(field_name="permissions")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )
    grants: "Optional[Dict[str, List[str]]]" = dc_field(
        default=None, metadata=dc_config(field_name="grants")
    )


@dataclass
class UpdateChannelTypeResponse(DataClassJsonMixin):
    automod: str = dc_field(metadata=dc_config(field_name="automod"))
    automod_behavior: str = dc_field(metadata=dc_config(field_name="automod_behavior"))
    connect_events: bool = dc_field(metadata=dc_config(field_name="connect_events"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    custom_events: bool = dc_field(metadata=dc_config(field_name="custom_events"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    mark_messages_pending: bool = dc_field(
        metadata=dc_config(field_name="mark_messages_pending")
    )
    max_message_length: int = dc_field(
        metadata=dc_config(field_name="max_message_length")
    )
    mutes: bool = dc_field(metadata=dc_config(field_name="mutes"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    polls: bool = dc_field(metadata=dc_config(field_name="polls"))
    push_notifications: bool = dc_field(
        metadata=dc_config(field_name="push_notifications")
    )
    quotes: bool = dc_field(metadata=dc_config(field_name="quotes"))
    reactions: bool = dc_field(metadata=dc_config(field_name="reactions"))
    read_events: bool = dc_field(metadata=dc_config(field_name="read_events"))
    reminders: bool = dc_field(metadata=dc_config(field_name="reminders"))
    replies: bool = dc_field(metadata=dc_config(field_name="replies"))
    search: bool = dc_field(metadata=dc_config(field_name="search"))
    typing_events: bool = dc_field(metadata=dc_config(field_name="typing_events"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    uploads: bool = dc_field(metadata=dc_config(field_name="uploads"))
    url_enrichment: bool = dc_field(metadata=dc_config(field_name="url_enrichment"))
    commands: List[str] = dc_field(metadata=dc_config(field_name="commands"))
    permissions: "List[PolicyRequest]" = dc_field(
        metadata=dc_config(field_name="permissions")
    )
    grants: "Dict[str, List[str]]" = dc_field(metadata=dc_config(field_name="grants"))
    blocklist: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist")
    )
    blocklist_behavior: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="blocklist_behavior")
    )
    allowed_flag_reasons: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="allowed_flag_reasons")
    )
    blocklists: "Optional[List[BlockListOptions]]" = dc_field(
        default=None, metadata=dc_config(field_name="blocklists")
    )
    automod_thresholds: "Optional[Thresholds]" = dc_field(
        default=None, metadata=dc_config(field_name="automod_thresholds")
    )


@dataclass
class UpdateCommandRequest(DataClassJsonMixin):
    description: str = dc_field(metadata=dc_config(field_name="description"))
    args: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="args"))
    set: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="set"))


@dataclass
class UpdateCommandResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    command: "Optional[Command]" = dc_field(
        default=None, metadata=dc_config(field_name="command")
    )


@dataclass
class UpdateExternalStorageRequest(DataClassJsonMixin):
    bucket: str = dc_field(metadata=dc_config(field_name="bucket"))
    storage_type: str = dc_field(metadata=dc_config(field_name="storage_type"))
    gcs_credentials: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="gcs_credentials")
    )
    path: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="path"))
    aws_s3: "Optional[S3Request]" = dc_field(
        default=None, metadata=dc_config(field_name="aws_s3")
    )
    azure_blob: "Optional[AzureRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="azure_blob")
    )


@dataclass
class UpdateExternalStorageResponse(DataClassJsonMixin):
    bucket: str = dc_field(metadata=dc_config(field_name="bucket"))
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    path: str = dc_field(metadata=dc_config(field_name="path"))
    type: str = dc_field(metadata=dc_config(field_name="type"))


@dataclass
class UpdateMessagePartialRequest(DataClassJsonMixin):
    skip_enrich_url: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_enrich_url")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    unset: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="unset")
    )
    set: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="set")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdateMessagePartialResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    pending_message_metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_message_metadata")
    )


@dataclass
class UpdateMessageRequest(DataClassJsonMixin):
    message: "MessageRequest" = dc_field(metadata=dc_config(field_name="message"))
    skip_enrich_url: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="skip_enrich_url")
    )


@dataclass
class UpdateMessageResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    message: "Message" = dc_field(metadata=dc_config(field_name="message"))
    pending_message_metadata: "Optional[Dict[str, str]]" = dc_field(
        default=None, metadata=dc_config(field_name="pending_message_metadata")
    )


@dataclass
class UpdatePollOptionRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    text: str = dc_field(metadata=dc_config(field_name="text"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="Custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdatePollPartialRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    unset: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="unset")
    )
    set: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="set")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdatePollRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    allow_answers: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="allow_answers")
    )
    allow_user_suggested_options: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="allow_user_suggested_options")
    )
    description: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="description")
    )
    enforce_unique_vote: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enforce_unique_vote")
    )
    is_closed: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="is_closed")
    )
    max_votes_allowed: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="max_votes_allowed")
    )
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    voting_visibility: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="voting_visibility")
    )
    options: "Optional[List[Optional[PollOption]]]" = dc_field(
        default=None, metadata=dc_config(field_name="options")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="Custom")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdateThreadPartialRequest(DataClassJsonMixin):
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    unset: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="unset")
    )
    set: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="set")
    )
    user: "Optional[UserRequest]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UpdateThreadPartialResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    thread: "ThreadResponse" = dc_field(metadata=dc_config(field_name="thread"))


@dataclass
class UpdateUserPartialRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    unset: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="unset")
    )
    set: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="set")
    )


@dataclass
class UpdateUserPermissionsRequest(DataClassJsonMixin):
    user_id: str = dc_field(metadata=dc_config(field_name="user_id"))
    grant_permissions: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="grant_permissions")
    )
    revoke_permissions: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="revoke_permissions")
    )


@dataclass
class UpdateUserPermissionsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))


@dataclass
class UpdateUsersPartialRequest(DataClassJsonMixin):
    users: "List[UpdateUserPartialRequest]" = dc_field(
        metadata=dc_config(field_name="users")
    )


@dataclass
class UpdateUsersRequest(DataClassJsonMixin):
    users: "Dict[str, UserRequest]" = dc_field(metadata=dc_config(field_name="users"))


@dataclass
class UpdateUsersResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    membership_deletion_task_id: str = dc_field(
        metadata=dc_config(field_name="membership_deletion_task_id")
    )
    users: "Dict[str, FullUserResponse]" = dc_field(
        metadata=dc_config(field_name="users")
    )


@dataclass
class UpsertPushProviderRequest(DataClassJsonMixin):
    push_provider: "Optional[PushProvider]" = dc_field(
        default=None, metadata=dc_config(field_name="push_provider")
    )


@dataclass
class UpsertPushProviderResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    push_provider: "PushProviderResponse" = dc_field(
        metadata=dc_config(field_name="push_provider")
    )


@dataclass
class UserBlock(DataClassJsonMixin):
    blocked_by_user_id: str = dc_field(
        metadata=dc_config(field_name="blocked_by_user_id")
    )
    blocked_user_id: str = dc_field(metadata=dc_config(field_name="blocked_user_id"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )


@dataclass
class UserCustomEventRequest(DataClassJsonMixin):
    type: str = dc_field(metadata=dc_config(field_name="type"))
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )


@dataclass
class UserInfoResponse(DataClassJsonMixin):
    image: str = dc_field(metadata=dc_config(field_name="image"))
    name: str = dc_field(metadata=dc_config(field_name="name"))
    roles: List[str] = dc_field(metadata=dc_config(field_name="roles"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))


@dataclass
class UserMute(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    target: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="target")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class UserObject(DataClassJsonMixin):
    banned: bool = dc_field(metadata=dc_config(field_name="banned"))
    id: str = dc_field(metadata=dc_config(field_name="id"))
    online: bool = dc_field(metadata=dc_config(field_name="online"))
    role: str = dc_field(metadata=dc_config(field_name="role"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    ban_expires: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="ban_expires",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    created_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deactivated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deactivated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    invisible: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="invisible")
    )
    language: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="language")
    )
    last_active: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_active",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    revoke_tokens_issued_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="revoke_tokens_issued_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    updated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    teams: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="teams")
    )
    privacy_settings: "Optional[PrivacySettings]" = dc_field(
        default=None, metadata=dc_config(field_name="privacy_settings")
    )
    push_notifications: "Optional[PushNotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )


@dataclass
class UserRequest(DataClassJsonMixin):
    id: str = dc_field(metadata=dc_config(field_name="id"))
    image: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="image")
    )
    invisible: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="invisible")
    )
    language: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="language")
    )
    name: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="name"))
    role: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="role"))
    teams: Optional[List[str]] = dc_field(
        default=None, metadata=dc_config(field_name="teams")
    )
    custom: Optional[Dict[str, object]] = dc_field(
        default=None, metadata=dc_config(field_name="custom")
    )
    privacy_settings: "Optional[PrivacySettings]" = dc_field(
        default=None, metadata=dc_config(field_name="privacy_settings")
    )
    push_notifications: "Optional[PushNotificationSettingsInput]" = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )


@dataclass
class UserResponse(DataClassJsonMixin):
    banned: bool = dc_field(metadata=dc_config(field_name="banned"))
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    id: str = dc_field(metadata=dc_config(field_name="id"))
    invisible: bool = dc_field(metadata=dc_config(field_name="invisible"))
    language: str = dc_field(metadata=dc_config(field_name="language"))
    online: bool = dc_field(metadata=dc_config(field_name="online"))
    role: str = dc_field(metadata=dc_config(field_name="role"))
    shadow_banned: bool = dc_field(metadata=dc_config(field_name="shadow_banned"))
    updated_at: datetime = dc_field(
        metadata=dc_config(
            field_name="updated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    blocked_user_ids: List[str] = dc_field(
        metadata=dc_config(field_name="blocked_user_ids")
    )
    devices: "List[Optional[Device]]" = dc_field(
        metadata=dc_config(field_name="devices")
    )
    teams: List[str] = dc_field(metadata=dc_config(field_name="teams"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    deactivated_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deactivated_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    deleted_at: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="deleted_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    image: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="image")
    )
    last_active: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="last_active",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    name: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="name"))
    revoke_tokens_issued_before: Optional[datetime] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="revoke_tokens_issued_before",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        ),
    )
    push_notifications: "Optional[PushNotificationSettings]" = dc_field(
        default=None, metadata=dc_config(field_name="push_notifications")
    )


@dataclass
class UserSessionStats(DataClassJsonMixin):
    freeze_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="freeze_duration_seconds")
    )
    max_freeze_fraction: float = dc_field(
        metadata=dc_config(field_name="max_freeze_fraction")
    )
    max_freezes_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="max_freezes_duration_seconds")
    )
    packet_loss_fraction: float = dc_field(
        metadata=dc_config(field_name="packet_loss_fraction")
    )
    publisher_packet_loss_fraction: float = dc_field(
        metadata=dc_config(field_name="publisher_packet_loss_fraction")
    )
    publishing_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="publishing_duration_seconds")
    )
    quality_score: float = dc_field(metadata=dc_config(field_name="quality_score"))
    receiving_duration_seconds: int = dc_field(
        metadata=dc_config(field_name="receiving_duration_seconds")
    )
    session_id: str = dc_field(metadata=dc_config(field_name="session_id"))
    total_pixels_in: int = dc_field(metadata=dc_config(field_name="total_pixels_in"))
    total_pixels_out: int = dc_field(metadata=dc_config(field_name="total_pixels_out"))
    bro_ws_er: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="browser")
    )
    browser_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="browser_version")
    )
    current_ip: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="current_ip")
    )
    current_sfu: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="current_sfu")
    )
    device_model: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="device_model")
    )
    device_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="device_version")
    )
    distance_to_sfu_kilometers: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="distance_to_sfu_kilometers")
    )
    max_fir_per_second: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="max_fir_per_second")
    )
    max_freezes_per_second: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="max_freezes_per_second")
    )
    max_nack_per_second: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="max_nack_per_second")
    )
    max_pli_per_second: Optional[float] = dc_field(
        default=None, metadata=dc_config(field_name="max_pli_per_second")
    )
    os: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="os"))
    os_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="os_version")
    )
    publisher_noise_cancellation_seconds: Optional[float] = dc_field(
        default=None,
        metadata=dc_config(field_name="publisher_noise_cancellation_seconds"),
    )
    publisher_quality_limitation_fraction: Optional[float] = dc_field(
        default=None,
        metadata=dc_config(field_name="publisher_quality_limitation_fraction"),
    )
    publishing_audio_codec: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="publishing_audio_codec")
    )
    publishing_video_codec: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="publishing_video_codec")
    )
    receiving_audio_codec: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="receiving_audio_codec")
    )
    receiving_video_codec: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="receiving_video_codec")
    )
    sdk: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="sdk"))
    sdk_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="sdk_version")
    )
    subscriber_video_quality_throttled_duration_seconds: Optional[float] = dc_field(
        default=None,
        metadata=dc_config(
            field_name="subscriber_video_quality_throttled_duration_seconds"
        ),
    )
    webrtc_version: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="webrtc_version")
    )
    published_tracks: "Optional[List[PublishedTrackInfo]]" = dc_field(
        default=None, metadata=dc_config(field_name="published_tracks")
    )
    subsessions: "Optional[List[Optional[Subsession]]]" = dc_field(
        default=None, metadata=dc_config(field_name="subsessions")
    )
    geolocation: "Optional[GeolocationResult]" = dc_field(
        default=None, metadata=dc_config(field_name="geolocation")
    )
    jitter: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="jitter")
    )
    latency: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="latency")
    )
    max_publishing_video_quality: "Optional[VideoQuality]" = dc_field(
        default=None, metadata=dc_config(field_name="max_publishing_video_quality")
    )
    max_receiving_video_quality: "Optional[VideoQuality]" = dc_field(
        default=None, metadata=dc_config(field_name="max_receiving_video_quality")
    )
    pub_sub_hints: "Optional[MediaPubSubHint]" = dc_field(
        default=None, metadata=dc_config(field_name="pub_sub_hints")
    )
    publisher_audio_mos: "Optional[MOSStats]" = dc_field(
        default=None, metadata=dc_config(field_name="publisher_audio_mos")
    )
    publisher_jitter: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="publisher_jitter")
    )
    publisher_latency: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="publisher_latency")
    )
    publisher_video_quality_limitation_duration_seconds: "Optional[Dict[str, float]]" = dc_field(
        default=None,
        metadata=dc_config(
            field_name="publisher_video_quality_limitation_duration_seconds"
        ),
    )
    subscriber_audio_mos: "Optional[MOSStats]" = dc_field(
        default=None, metadata=dc_config(field_name="subscriber_audio_mos")
    )
    subscriber_jitter: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="subscriber_jitter")
    )
    subscriber_latency: "Optional[Stats]" = dc_field(
        default=None, metadata=dc_config(field_name="subscriber_latency")
    )
    timeline: "Optional[CallTimeline]" = dc_field(
        default=None, metadata=dc_config(field_name="timeline")
    )


@dataclass
class UserStats(DataClassJsonMixin):
    min_event_ts: int = dc_field(metadata=dc_config(field_name="min_event_ts"))
    session_stats: "List[UserSessionStats]" = dc_field(
        metadata=dc_config(field_name="session_stats")
    )
    info: "UserInfoResponse" = dc_field(metadata=dc_config(field_name="info"))
    rating: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="rating")
    )


@dataclass
class VideoQuality(DataClassJsonMixin):
    usage_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="usage_type")
    )
    resolution: "Optional[VideoResolution]" = dc_field(
        default=None, metadata=dc_config(field_name="resolution")
    )


@dataclass
class VideoResolution(DataClassJsonMixin):
    height: int = dc_field(metadata=dc_config(field_name="height"))
    width: int = dc_field(metadata=dc_config(field_name="width"))


@dataclass
class VideoSettings(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    camera_default_on: bool = dc_field(
        metadata=dc_config(field_name="camera_default_on")
    )
    camera_facing: str = dc_field(metadata=dc_config(field_name="camera_facing"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    target_resolution: "TargetResolution" = dc_field(
        metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class VideoSettingsRequest(DataClassJsonMixin):
    access_request_enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="access_request_enabled")
    )
    camera_default_on: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="camera_default_on")
    )
    camera_facing: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="camera_facing")
    )
    enabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="enabled")
    )
    target_resolution: "Optional[TargetResolution]" = dc_field(
        default=None, metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class VideoSettingsResponse(DataClassJsonMixin):
    access_request_enabled: bool = dc_field(
        metadata=dc_config(field_name="access_request_enabled")
    )
    camera_default_on: bool = dc_field(
        metadata=dc_config(field_name="camera_default_on")
    )
    camera_facing: str = dc_field(metadata=dc_config(field_name="camera_facing"))
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    target_resolution: "TargetResolution" = dc_field(
        metadata=dc_config(field_name="target_resolution")
    )


@dataclass
class VoteData(DataClassJsonMixin):
    answer_text: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="answer_text")
    )
    option_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="option_id")
    )
    option: "Optional[PollOption]" = dc_field(
        default=None, metadata=dc_config(field_name="Option")
    )


@dataclass
class WSEvent(DataClassJsonMixin):
    created_at: datetime = dc_field(
        metadata=dc_config(
            field_name="created_at",
            encoder=encode_datetime,
            decoder=datetime_from_unix_ns,
            mm_field=fields.DateTime(format="iso"),
        )
    )
    type: str = dc_field(metadata=dc_config(field_name="type"))
    custom: Dict[str, object] = dc_field(metadata=dc_config(field_name="custom"))
    automoderation: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="automoderation")
    )
    channel_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="channel_id")
    )
    channel_type: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="channel_type")
    )
    cid: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="cid"))
    connection_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="connection_id")
    )
    parent_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="parent_id")
    )
    reason: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="reason")
    )
    team: Optional[str] = dc_field(default=None, metadata=dc_config(field_name="team"))
    user_id: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="user_id")
    )
    watcher_count: Optional[int] = dc_field(
        default=None, metadata=dc_config(field_name="watcher_count")
    )
    automoderation_scores: "Optional[ModerationResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="automoderation_scores")
    )
    channel: "Optional[ChannelResponse]" = dc_field(
        default=None, metadata=dc_config(field_name="channel")
    )
    created_by: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="created_by")
    )
    me: "Optional[OwnUser]" = dc_field(
        default=None, metadata=dc_config(field_name="me")
    )
    member: "Optional[ChannelMember]" = dc_field(
        default=None, metadata=dc_config(field_name="member")
    )
    message: "Optional[Message]" = dc_field(
        default=None, metadata=dc_config(field_name="message")
    )
    message_update: "Optional[MessageUpdate]" = dc_field(
        default=None, metadata=dc_config(field_name="message_update")
    )
    poll: "Optional[Poll]" = dc_field(
        default=None, metadata=dc_config(field_name="poll")
    )
    poll_vote: "Optional[PollVote]" = dc_field(
        default=None, metadata=dc_config(field_name="poll_vote")
    )
    reaction: "Optional[Reaction]" = dc_field(
        default=None, metadata=dc_config(field_name="reaction")
    )
    thread: "Optional[Thread]" = dc_field(
        default=None, metadata=dc_config(field_name="thread")
    )
    user: "Optional[UserObject]" = dc_field(
        default=None, metadata=dc_config(field_name="user")
    )


@dataclass
class WrappedUnreadCountsResponse(DataClassJsonMixin):
    duration: str = dc_field(metadata=dc_config(field_name="duration"))
    total_unread_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_count")
    )
    total_unread_threads_count: int = dc_field(
        metadata=dc_config(field_name="total_unread_threads_count")
    )
    channel_type: "List[UnreadCountsChannelType]" = dc_field(
        metadata=dc_config(field_name="channel_type")
    )
    channels: "List[UnreadCountsChannel]" = dc_field(
        metadata=dc_config(field_name="channels")
    )
    threads: "List[UnreadCountsThread]" = dc_field(
        metadata=dc_config(field_name="threads")
    )


@dataclass
class XiaomiConfig(DataClassJsonMixin):
    disabled: Optional[bool] = dc_field(
        default=None, metadata=dc_config(field_name="Disabled")
    )
    package_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="package_name")
    )
    secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="secret")
    )


@dataclass
class XiaomiConfigFields(DataClassJsonMixin):
    enabled: bool = dc_field(metadata=dc_config(field_name="enabled"))
    package_name: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="package_name")
    )
    secret: Optional[str] = dc_field(
        default=None, metadata=dc_config(field_name="secret")
    )
