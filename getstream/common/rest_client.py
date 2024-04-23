from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import encode_query_param, request_to_dict


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
    
    def update_app(self, update_app_request: UpdateAppRequest = None) -> StreamResponse[Response]:
        return self.patch("/api/v2/app", Response, json=request_to_dict(update_app_request))
    
    def check_push(self, check_push_request: CheckPushRequest = None) -> StreamResponse[CheckPushResponse]:
        return self.post("/api/v2/check_push", CheckPushResponse, json=request_to_dict(check_push_request))
    
    def check_sns(self, check_snsrequest: CheckSNSRequest = None) -> StreamResponse[CheckSNSResponse]:
        return self.post("/api/v2/check_sns", CheckSNSResponse, json=request_to_dict(check_snsrequest))
    
    def check_sqs(self, check_sqsrequest: CheckSQSRequest = None) -> StreamResponse[CheckSQSResponse]:
        return self.post("/api/v2/check_sqs", CheckSQSResponse, json=request_to_dict(check_sqsrequest))
    
    def delete_device(self, id: str, user_id: Optional[str] = None) -> StreamResponse[Response]:
        query_params = {
            "id": encode_query_param(id), "user_id": encode_query_param(user_id), 
        }
        return self.delete("/api/v2/devices", Response, query_params=query_params)
    
    def list_devices(self, user_id: Optional[str] = None) -> StreamResponse[ListDevicesResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        return self.get("/api/v2/devices", ListDevicesResponse, query_params=query_params)
    
    def create_device(self, create_device_request: CreateDeviceRequest) -> StreamResponse[Response]:
        return self.post("/api/v2/devices", Response, json=request_to_dict(create_device_request))
    
    def export_users(self, export_users_request: ExportUsersRequest) -> StreamResponse[ExportUsersResponse]:
        return self.post("/api/v2/export/users", ExportUsersResponse, json=request_to_dict(export_users_request))
    
    def create_guest(self, create_guest_request: CreateGuestRequest) -> StreamResponse[CreateGuestResponse]:
        return self.post("/api/v2/guest", CreateGuestResponse, json=request_to_dict(create_guest_request))
    
    def create_import_url(self, create_import_urlrequest: CreateImportURLRequest = None) -> StreamResponse[CreateImportURLResponse]:
        return self.post("/api/v2/import_urls", CreateImportURLResponse, json=request_to_dict(create_import_urlrequest))
    
    def list_imports(self) -> StreamResponse[ListImportsResponse]:
        return self.get("/api/v2/imports", ListImportsResponse)
    
    def create_import(self, create_import_request: CreateImportRequest) -> StreamResponse[CreateImportResponse]:
        return self.post("/api/v2/imports", CreateImportResponse, json=request_to_dict(create_import_request))
    
    def get_import(self, id: str) -> StreamResponse[GetImportResponse]:
        path_params = {
            "id": id, 
        }
        return self.get("/api/v2/imports/{id}", GetImportResponse, path_params=path_params)
    
    def get_og(self, url: str) -> StreamResponse[GetOGResponse]:
        query_params = {
            "url": encode_query_param(url), 
        }
        return self.get("/api/v2/og", GetOGResponse, query_params=query_params)
    
    def list_permissions(self) -> StreamResponse[ListPermissionsResponse]:
        return self.get("/api/v2/permissions", ListPermissionsResponse)
    
    def get_permission(self, id: str) -> StreamResponse[GetCustomPermissionResponse]:
        path_params = {
            "id": id, 
        }
        return self.get("/api/v2/permissions/{id}", GetCustomPermissionResponse, path_params=path_params)
    
    def list_push_providers(self) -> StreamResponse[ListPushProvidersResponse]:
        return self.get("/api/v2/push_providers", ListPushProvidersResponse)
    
    def upsert_push_provider(self, upsert_push_provider_request: UpsertPushProviderRequest = None) -> StreamResponse[UpsertPushProviderResponse]:
        return self.post("/api/v2/push_providers", UpsertPushProviderResponse, json=request_to_dict(upsert_push_provider_request))
    
    def delete_push_provider(self, type: str, name: str) -> StreamResponse[Response]:
        path_params = {
            "type": type, "name": name, 
        }
        return self.delete("/api/v2/push_providers/{type}/{name}", Response, path_params=path_params)
    
    def get_rate_limits(self, server_side: Optional[bool] = None, android: Optional[bool] = None, ios: Optional[bool] = None, web: Optional[bool] = None, endpoints: Optional[str] = None) -> StreamResponse[GetRateLimitsResponse]:
        query_params = {
            "server_side": encode_query_param(server_side), "android": encode_query_param(android), "ios": encode_query_param(ios), "web": encode_query_param(web), "endpoints": encode_query_param(endpoints), 
        }
        return self.get("/api/v2/rate_limits", GetRateLimitsResponse, query_params=query_params)
    
    def list_roles(self) -> StreamResponse[ListRolesResponse]:
        return self.get("/api/v2/roles", ListRolesResponse)
    
    def create_role(self, create_role_request: CreateRoleRequest) -> StreamResponse[CreateRoleResponse]:
        return self.post("/api/v2/roles", CreateRoleResponse, json=request_to_dict(create_role_request))
    
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
    
    def query_users(self, payload: Optional[QueryUsersPayload] = None) -> StreamResponse[QueryUsersResponse]:
        query_params = {
            "payload": encode_query_param(payload), 
        }
        return self.get("/api/v2/users", QueryUsersResponse, query_params=query_params)
    
    def update_users_partial(self, update_users_partial_request: UpdateUsersPartialRequest) -> StreamResponse[UpdateUsersResponse]:
        return self.patch("/api/v2/users", UpdateUsersResponse, json=request_to_dict(update_users_partial_request))
    
    def update_users(self, update_users_request: UpdateUsersRequest) -> StreamResponse[UpdateUsersResponse]:
        return self.post("/api/v2/users", UpdateUsersResponse, json=request_to_dict(update_users_request))
    
    def deactivate_users(self, deactivate_users_request: DeactivateUsersRequest) -> StreamResponse[DeactivateUsersResponse]:
        return self.post("/api/v2/users/deactivate", DeactivateUsersResponse, json=request_to_dict(deactivate_users_request))
    
    def delete_users(self, delete_users_request: DeleteUsersRequest) -> StreamResponse[DeleteUsersResponse]:
        return self.post("/api/v2/users/delete", DeleteUsersResponse, json=request_to_dict(delete_users_request))
    
    def reactivate_users(self, reactivate_users_request: ReactivateUsersRequest) -> StreamResponse[ReactivateUsersResponse]:
        return self.post("/api/v2/users/reactivate", ReactivateUsersResponse, json=request_to_dict(reactivate_users_request))
    
    def restore_users(self, restore_users_request: RestoreUsersRequest) -> StreamResponse[Response]:
        return self.post("/api/v2/users/restore", Response, json=request_to_dict(restore_users_request))
    
    def deactivate_user(self, user_id: str, deactivate_user_request: DeactivateUserRequest = None) -> StreamResponse[DeactivateUserResponse]:
        path_params = {
            "user_id": user_id, 
        }
        return self.post("/api/v2/users/{user_id}/deactivate", DeactivateUserResponse, path_params=path_params, json=request_to_dict(deactivate_user_request))
    
    def export_user(self, user_id: str) -> StreamResponse[ExportUserResponse]:
        path_params = {
            "user_id": user_id, 
        }
        return self.get("/api/v2/users/{user_id}/export", ExportUserResponse, path_params=path_params)
    
    def reactivate_user(self, user_id: str, reactivate_user_request: ReactivateUserRequest) -> StreamResponse[ReactivateUserResponse]:
        path_params = {
            "user_id": user_id, 
        }
        return self.post("/api/v2/users/{user_id}/reactivate", ReactivateUserResponse, path_params=path_params, json=request_to_dict(reactivate_user_request))
    