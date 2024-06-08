from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import build_query_param, build_body_dict


class CommonRestClient(BaseClient):
    def __init__(self, api_key: str, base_url: str, timeout: float, token: str):
        """
        Initializes CommonClient with BaseClient instance
        :param api_key: A string representing the client's API key
        :param base_url: A string representing the base uniform resource locator
        :param timeout: A number representing the time limit for a request
        :param token: A string instance representing the client's token
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            token=token,
        )

    def get_app(self) -> StreamResponse[GetApplicationResponse]:
        return self.get("/api/v2/app", GetApplicationResponse)

    def update_app(
        self,
        async_url_enrich_enabled: Optional[bool] = None,
        auto_translation_enabled: Optional[bool] = None,
        before_message_send_hook_url: Optional[str] = None,
        cdn_expiration_seconds: Optional[int] = None,
        channel_hide_members_only: Optional[bool] = None,
        custom_action_handler_url: Optional[str] = None,
        disable_auth_checks: Optional[bool] = None,
        disable_permissions_checks: Optional[bool] = None,
        enforce_unique_usernames: Optional[str] = None,
        image_moderation_enabled: Optional[bool] = None,
        migrate_permissions_to_v2: Optional[bool] = None,
        multi_tenant_enabled: Optional[bool] = None,
        permission_version: Optional[str] = None,
        reminders_interval: Optional[int] = None,
        reminders_max_members: Optional[int] = None,
        revoke_tokens_issued_before: Optional[datetime] = None,
        sns_key: Optional[str] = None,
        sns_secret: Optional[str] = None,
        sns_topic_arn: Optional[str] = None,
        sqs_key: Optional[str] = None,
        sqs_secret: Optional[str] = None,
        sqs_url: Optional[str] = None,
        video_provider: Optional[str] = None,
        webhook_url: Optional[str] = None,
        image_moderation_block_labels: Optional[List[str]] = None,
        image_moderation_labels: Optional[List[str]] = None,
        user_search_disallowed_roles: Optional[List[str]] = None,
        webhook_events: Optional[List[str]] = None,
        agora_options: Optional[Config] = None,
        apn_config: Optional[APNConfig] = None,
        async_moderation_config: Optional[AsyncModerationConfiguration] = None,
        datadog_info: Optional[DataDogInfo] = None,
        file_upload_config: Optional[FileUploadConfig] = None,
        firebase_config: Optional[FirebaseConfig] = None,
        grants: Optional[Dict[str, List[str]]] = None,
        hms_options: Optional[Config] = None,
        huawei_config: Optional[HuaweiConfig] = None,
        image_upload_config: Optional[FileUploadConfig] = None,
        push_config: Optional[PushConfig] = None,
        xiaomi_config: Optional[XiaomiConfig] = None,
    ) -> StreamResponse[Response]:
        json = build_body_dict(
            async_url_enrich_enabled=async_url_enrich_enabled,
            auto_translation_enabled=auto_translation_enabled,
            before_message_send_hook_url=before_message_send_hook_url,
            cdn_expiration_seconds=cdn_expiration_seconds,
            channel_hide_members_only=channel_hide_members_only,
            custom_action_handler_url=custom_action_handler_url,
            disable_auth_checks=disable_auth_checks,
            disable_permissions_checks=disable_permissions_checks,
            enforce_unique_usernames=enforce_unique_usernames,
            image_moderation_enabled=image_moderation_enabled,
            migrate_permissions_to_v2=migrate_permissions_to_v2,
            multi_tenant_enabled=multi_tenant_enabled,
            permission_version=permission_version,
            reminders_interval=reminders_interval,
            reminders_max_members=reminders_max_members,
            revoke_tokens_issued_before=revoke_tokens_issued_before,
            sns_key=sns_key,
            sns_secret=sns_secret,
            sns_topic_arn=sns_topic_arn,
            sqs_key=sqs_key,
            sqs_secret=sqs_secret,
            sqs_url=sqs_url,
            video_provider=video_provider,
            webhook_url=webhook_url,
            image_moderation_block_labels=image_moderation_block_labels,
            image_moderation_labels=image_moderation_labels,
            user_search_disallowed_roles=user_search_disallowed_roles,
            webhook_events=webhook_events,
            agora_options=agora_options,
            apn_config=apn_config,
            async_moderation_config=async_moderation_config,
            datadog_info=datadog_info,
            file_upload_config=file_upload_config,
            firebase_config=firebase_config,
            grants=grants,
            hms_options=hms_options,
            huawei_config=huawei_config,
            image_upload_config=image_upload_config,
            push_config=push_config,
            xiaomi_config=xiaomi_config,
        )

        return self.patch("/api/v2/app", Response, json=json)

    def list_block_lists(self) -> StreamResponse[ListBlockListResponse]:
        return self.get("/api/v2/blocklists", ListBlockListResponse)

    def create_block_list(
        self, name: str, words: List[str], type: Optional[str] = None
    ) -> StreamResponse[Response]:
        json = build_body_dict(name=name, words=words, type=type)

        return self.post("/api/v2/blocklists", Response, json=json)

    def delete_block_list(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/blocklists/{name}", Response, path_params=path_params
        )

    def get_block_list(self, name: str) -> StreamResponse[GetBlockListResponse]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/blocklists/{name}", GetBlockListResponse, path_params=path_params
        )

    def update_block_list(
        self, name: str, words: Optional[List[str]] = None
    ) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(words=words)

        return self.put(
            "/api/v2/blocklists/{name}", Response, path_params=path_params, json=json
        )

    def check_push(
        self,
        apn_template: Optional[str] = None,
        firebase_data_template: Optional[str] = None,
        firebase_template: Optional[str] = None,
        message_id: Optional[str] = None,
        push_provider_name: Optional[str] = None,
        push_provider_type: Optional[str] = None,
        skip_devices: Optional[bool] = None,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[CheckPushResponse]:
        json = build_body_dict(
            apn_template=apn_template,
            firebase_data_template=firebase_data_template,
            firebase_template=firebase_template,
            message_id=message_id,
            push_provider_name=push_provider_name,
            push_provider_type=push_provider_type,
            skip_devices=skip_devices,
            user_id=user_id,
            user=user,
        )

        return self.post("/api/v2/check_push", CheckPushResponse, json=json)

    def check_sns(
        self,
        sns_key: Optional[str] = None,
        sns_secret: Optional[str] = None,
        sns_topic_arn: Optional[str] = None,
    ) -> StreamResponse[CheckSNSResponse]:
        json = build_body_dict(
            sns_key=sns_key, sns_secret=sns_secret, sns_topic_arn=sns_topic_arn
        )

        return self.post("/api/v2/check_sns", CheckSNSResponse, json=json)

    def check_sqs(
        self,
        sqs_key: Optional[str] = None,
        sqs_secret: Optional[str] = None,
        sqs_url: Optional[str] = None,
    ) -> StreamResponse[CheckSQSResponse]:
        json = build_body_dict(sqs_key=sqs_key, sqs_secret=sqs_secret, sqs_url=sqs_url)

        return self.post("/api/v2/check_sqs", CheckSQSResponse, json=json)

    def delete_device(
        self, id: str, user_id: Optional[str] = None
    ) -> StreamResponse[Response]:
        query_params = build_query_param(id=id, user_id=user_id)

        return self.delete("/api/v2/devices", Response, query_params=query_params)

    def list_devices(
        self, user_id: Optional[str] = None
    ) -> StreamResponse[ListDevicesResponse]:
        query_params = build_query_param(user_id=user_id)

        return self.get(
            "/api/v2/devices", ListDevicesResponse, query_params=query_params
        )

    def create_device(
        self,
        id: str,
        push_provider: str,
        push_provider_name: Optional[str] = None,
        user_id: Optional[str] = None,
        voip_token: Optional[bool] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[Response]:
        json = build_body_dict(
            id=id,
            push_provider=push_provider,
            push_provider_name=push_provider_name,
            user_id=user_id,
            voip_token=voip_token,
            user=user,
        )

        return self.post("/api/v2/devices", Response, json=json)

    def export_users(self, user_ids: List[str]) -> StreamResponse[ExportUsersResponse]:
        json = build_body_dict(user_ids=user_ids)

        return self.post("/api/v2/export/users", ExportUsersResponse, json=json)

    def list_external_storage(self) -> StreamResponse[ListExternalStorageResponse]:
        return self.get("/api/v2/external_storage", ListExternalStorageResponse)

    def create_external_storage(
        self,
        bucket: str,
        name: str,
        storage_type: str,
        gcs_credentials: Optional[str] = None,
        path: Optional[str] = None,
        aws_s3: Optional[S3Request] = None,
        azure_blob: Optional[AzureRequest] = None,
    ) -> StreamResponse[CreateExternalStorageResponse]:
        json = build_body_dict(
            bucket=bucket,
            name=name,
            storage_type=storage_type,
            gcs_credentials=gcs_credentials,
            path=path,
            aws_s3=aws_s3,
            azure_blob=azure_blob,
        )

        return self.post(
            "/api/v2/external_storage", CreateExternalStorageResponse, json=json
        )

    def delete_external_storage(
        self, name: str
    ) -> StreamResponse[DeleteExternalStorageResponse]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/external_storage/{name}",
            DeleteExternalStorageResponse,
            path_params=path_params,
        )

    def update_external_storage(
        self,
        name: str,
        bucket: str,
        storage_type: str,
        gcs_credentials: Optional[str] = None,
        path: Optional[str] = None,
        aws_s3: Optional[S3Request] = None,
        azure_blob: Optional[AzureRequest] = None,
    ) -> StreamResponse[UpdateExternalStorageResponse]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(
            bucket=bucket,
            storage_type=storage_type,
            gcs_credentials=gcs_credentials,
            path=path,
            aws_s3=aws_s3,
            azure_blob=azure_blob,
        )

        return self.put(
            "/api/v2/external_storage/{name}",
            UpdateExternalStorageResponse,
            path_params=path_params,
            json=json,
        )

    def check_external_storage(
        self, name: str
    ) -> StreamResponse[CheckExternalStorageResponse]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/external_storage/{name}/check",
            CheckExternalStorageResponse,
            path_params=path_params,
        )

    def create_guest(self, user: UserRequest) -> StreamResponse[CreateGuestResponse]:
        json = build_body_dict(user=user)

        return self.post("/api/v2/guest", CreateGuestResponse, json=json)

    def create_import_url(
        self, filename: Optional[str] = None
    ) -> StreamResponse[CreateImportURLResponse]:
        json = build_body_dict(filename=filename)

        return self.post("/api/v2/import_urls", CreateImportURLResponse, json=json)

    def list_imports(self) -> StreamResponse[ListImportsResponse]:
        return self.get("/api/v2/imports", ListImportsResponse)

    def create_import(
        self, mode: str, path: str
    ) -> StreamResponse[CreateImportResponse]:
        json = build_body_dict(mode=mode, path=path)

        return self.post("/api/v2/imports", CreateImportResponse, json=json)

    def get_import(self, id: str) -> StreamResponse[GetImportResponse]:
        path_params = {
            "id": id,
        }

        return self.get(
            "/api/v2/imports/{id}", GetImportResponse, path_params=path_params
        )

    def unban(
        self,
        target_user_id: str,
        channel_cid: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> StreamResponse[Response]:
        query_params = build_query_param(
            target_user_id=target_user_id,
            channel_cid=channel_cid,
            created_by=created_by,
        )

        return self.delete(
            "/api/v2/moderation/ban", Response, query_params=query_params
        )

    def ban(
        self,
        target_user_id: str,
        banned_by_id: Optional[str] = None,
        channel_cid: Optional[str] = None,
        ip_ban: Optional[bool] = None,
        reason: Optional[str] = None,
        shadow: Optional[bool] = None,
        timeout: Optional[int] = None,
        user_id: Optional[str] = None,
        banned_by: Optional[UserRequest] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[Response]:
        json = build_body_dict(
            target_user_id=target_user_id,
            banned_by_id=banned_by_id,
            channel_cid=channel_cid,
            ip_ban=ip_ban,
            reason=reason,
            shadow=shadow,
            timeout=timeout,
            user_id=user_id,
            banned_by=banned_by,
            user=user,
        )

        return self.post("/api/v2/moderation/ban", Response, json=json)

    def flag(
        self,
        reason: Optional[str] = None,
        target_message_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[FlagResponse]:
        json = build_body_dict(
            reason=reason,
            target_message_id=target_message_id,
            target_user_id=target_user_id,
            user_id=user_id,
            custom=custom,
            user=user,
        )

        return self.post("/api/v2/moderation/flag", FlagResponse, json=json)

    def mute_user(
        self,
        timeout: int,
        user_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MuteUserResponse]:
        json = build_body_dict(
            timeout=timeout, user_id=user_id, target_ids=target_ids, user=user
        )

        return self.post("/api/v2/moderation/mute", MuteUserResponse, json=json)

    def unmute_user(
        self,
        timeout: int,
        user_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UnmuteResponse]:
        json = build_body_dict(
            timeout=timeout, user_id=user_id, target_ids=target_ids, user=user
        )

        return self.post("/api/v2/moderation/unmute", UnmuteResponse, json=json)

    def get_og(self, url: str) -> StreamResponse[GetOGResponse]:
        query_params = build_query_param(url=url)

        return self.get("/api/v2/og", GetOGResponse, query_params=query_params)

    def list_permissions(self) -> StreamResponse[ListPermissionsResponse]:
        return self.get("/api/v2/permissions", ListPermissionsResponse)

    def get_permission(self, id: str) -> StreamResponse[GetCustomPermissionResponse]:
        path_params = {
            "id": id,
        }

        return self.get(
            "/api/v2/permissions/{id}",
            GetCustomPermissionResponse,
            path_params=path_params,
        )

    def list_push_providers(self) -> StreamResponse[ListPushProvidersResponse]:
        return self.get("/api/v2/push_providers", ListPushProvidersResponse)

    def upsert_push_provider(
        self, push_provider: Optional[PushProvider] = None
    ) -> StreamResponse[UpsertPushProviderResponse]:
        json = build_body_dict(push_provider=push_provider)

        return self.post(
            "/api/v2/push_providers", UpsertPushProviderResponse, json=json
        )

    def delete_push_provider(self, type: str, name: str) -> StreamResponse[Response]:
        path_params = {
            "type": type,
            "name": name,
        }

        return self.delete(
            "/api/v2/push_providers/{type}/{name}", Response, path_params=path_params
        )

    def get_rate_limits(
        self,
        server_side: Optional[bool] = None,
        android: Optional[bool] = None,
        ios: Optional[bool] = None,
        web: Optional[bool] = None,
        endpoints: Optional[str] = None,
    ) -> StreamResponse[GetRateLimitsResponse]:
        query_params = build_query_param(
            server_side=server_side,
            android=android,
            ios=ios,
            web=web,
            endpoints=endpoints,
        )

        return self.get(
            "/api/v2/rate_limits", GetRateLimitsResponse, query_params=query_params
        )

    def list_roles(self) -> StreamResponse[ListRolesResponse]:
        return self.get("/api/v2/roles", ListRolesResponse)

    def create_role(self, name: str) -> StreamResponse[CreateRoleResponse]:
        json = build_body_dict(name=name)

        return self.post("/api/v2/roles", CreateRoleResponse, json=json)

    def delete_role(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.delete("/api/v2/roles/{name}", Response, path_params=path_params)

    def get_task(self, id: str) -> StreamResponse[GetTaskResponse]:
        path_params = {
            "id": id,
        }

        return self.get("/api/v2/tasks/{id}", GetTaskResponse, path_params=path_params)

    def query_users(
        self, payload: Optional[QueryUsersPayload] = None
    ) -> StreamResponse[QueryUsersResponse]:
        query_params = build_query_param(payload=payload)

        return self.get("/api/v2/users", QueryUsersResponse, query_params=query_params)

    def update_users_partial(
        self, users: List[UpdateUserPartialRequest]
    ) -> StreamResponse[UpdateUsersResponse]:
        json = build_body_dict(users=users)

        return self.patch("/api/v2/users", UpdateUsersResponse, json=json)

    def update_users(
        self, users: Dict[str, UserRequest]
    ) -> StreamResponse[UpdateUsersResponse]:
        json = build_body_dict(users=users)

        return self.post("/api/v2/users", UpdateUsersResponse, json=json)

    def get_blocked_users(
        self, user_id: Optional[str] = None
    ) -> StreamResponse[GetBlockedUsersResponse]:
        query_params = build_query_param(user_id=user_id)

        return self.get(
            "/api/v2/users/block", GetBlockedUsersResponse, query_params=query_params
        )

    def block_users(
        self,
        blocked_user_id: str,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[BlockUsersResponse]:
        json = build_body_dict(
            blocked_user_id=blocked_user_id, user_id=user_id, user=user
        )

        return self.post("/api/v2/users/block", BlockUsersResponse, json=json)

    def deactivate_users(
        self,
        user_ids: List[str],
        created_by_id: Optional[str] = None,
        mark_channels_deleted: Optional[bool] = None,
        mark_messages_deleted: Optional[bool] = None,
    ) -> StreamResponse[DeactivateUsersResponse]:
        json = build_body_dict(
            user_ids=user_ids,
            created_by_id=created_by_id,
            mark_channels_deleted=mark_channels_deleted,
            mark_messages_deleted=mark_messages_deleted,
        )

        return self.post("/api/v2/users/deactivate", DeactivateUsersResponse, json=json)

    def delete_users(
        self,
        user_ids: List[str],
        calls: Optional[str] = None,
        conversations: Optional[str] = None,
        messages: Optional[str] = None,
        new_call_owner_id: Optional[str] = None,
        new_channel_owner_id: Optional[str] = None,
        user: Optional[str] = None,
    ) -> StreamResponse[DeleteUsersResponse]:
        json = build_body_dict(
            user_ids=user_ids,
            calls=calls,
            conversations=conversations,
            messages=messages,
            new_call_owner_id=new_call_owner_id,
            new_channel_owner_id=new_channel_owner_id,
            user=user,
        )

        return self.post("/api/v2/users/delete", DeleteUsersResponse, json=json)

    def reactivate_users(
        self,
        user_ids: List[str],
        created_by_id: Optional[str] = None,
        restore_channels: Optional[bool] = None,
        restore_messages: Optional[bool] = None,
    ) -> StreamResponse[ReactivateUsersResponse]:
        json = build_body_dict(
            user_ids=user_ids,
            created_by_id=created_by_id,
            restore_channels=restore_channels,
            restore_messages=restore_messages,
        )

        return self.post("/api/v2/users/reactivate", ReactivateUsersResponse, json=json)

    def restore_users(self, user_ids: List[str]) -> StreamResponse[Response]:
        json = build_body_dict(user_ids=user_ids)

        return self.post("/api/v2/users/restore", Response, json=json)

    def unblock_users(
        self,
        blocked_user_id: str,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UnblockUsersResponse]:
        json = build_body_dict(
            blocked_user_id=blocked_user_id, user_id=user_id, user=user
        )

        return self.post("/api/v2/users/unblock", UnblockUsersResponse, json=json)

    def deactivate_user(
        self,
        user_id: str,
        created_by_id: Optional[str] = None,
        mark_messages_deleted: Optional[bool] = None,
    ) -> StreamResponse[DeactivateUserResponse]:
        path_params = {
            "user_id": user_id,
        }
        json = build_body_dict(
            created_by_id=created_by_id, mark_messages_deleted=mark_messages_deleted
        )

        return self.post(
            "/api/v2/users/{user_id}/deactivate",
            DeactivateUserResponse,
            path_params=path_params,
            json=json,
        )

    def export_user(self, user_id: str) -> StreamResponse[ExportUserResponse]:
        path_params = {
            "user_id": user_id,
        }

        return self.get(
            "/api/v2/users/{user_id}/export",
            ExportUserResponse,
            path_params=path_params,
        )

    def reactivate_user(
        self,
        user_id: str,
        created_by_id: Optional[str] = None,
        name: Optional[str] = None,
        restore_messages: Optional[bool] = None,
    ) -> StreamResponse[ReactivateUserResponse]:
        path_params = {
            "user_id": user_id,
        }
        json = build_body_dict(
            created_by_id=created_by_id, name=name, restore_messages=restore_messages
        )

        return self.post(
            "/api/v2/users/{user_id}/reactivate",
            ReactivateUserResponse,
            path_params=path_params,
            json=json,
        )
