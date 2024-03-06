# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/client.tmpl
from getstream.models.azure_request import AzureRequest
from getstream.models.check_external_storage_response import (
    CheckExternalStorageResponse,
)
from getstream.models.create_external_storage_response import (
    CreateExternalStorageResponse,
)
from getstream.models.delete_external_storage_response import (
    DeleteExternalStorageResponse,
)
from getstream.models.list_external_storage_response import ListExternalStorageResponse
from getstream.models.list_transcriptions_response import ListTranscriptionsResponse
from getstream.models.s_3_request import S3Request
from getstream.models.update_external_storage_response import (
    UpdateExternalStorageResponse,
)
from getstream.stream_response import StreamResponse
from getstream.sync.base import BaseClient
from typing import Optional, List, Dict
from datetime import datetime
from getstream.models.update_user_permissions_response import (
    UpdateUserPermissionsResponse,
)
from getstream.models.stop_recording_response import StopRecordingResponse
from getstream.models.list_recordings_response import ListRecordingsResponse
from getstream.models.block_user_response import BlockUserResponse
from getstream.models.send_event_response import SendEventResponse
from getstream.models.get_call_type_response import GetCallTypeResponse
from getstream.models.stop_live_response import StopLiveResponse
from getstream.models.update_call_response import UpdateCallResponse
from getstream.models.update_call_members_response import UpdateCallMembersResponse
from getstream.models.get_edges_response import GetEdgesResponse
from getstream.models.start_hls_broadcasting_response import (
    StartHlsbroadcastingResponse,
)
from getstream.models.get_or_create_call_response import GetOrCreateCallResponse
from getstream.models.query_members_response import QueryMembersResponse
from getstream.models.list_devices_response import ListDevicesResponse
from getstream.models.create_guest_response import CreateGuestResponse
from getstream.models.end_call_response import EndCallResponse
from getstream.models.stop_transcription_response import StopTranscriptionResponse
from getstream.models.create_call_type_response import CreateCallTypeResponse
from getstream.models.stop_hls_broadcasting_response import StopHlsbroadcastingResponse
from getstream.models.start_recording_response import StartRecordingResponse
from getstream.models.unpin_response import UnpinResponse
from getstream.models.list_call_type_response import ListCallTypeResponse
from getstream.models.join_call_response import JoinCallResponse
from getstream.models.mute_users_response import MuteUsersResponse
from getstream.models.get_call_response import GetCallResponse
from getstream.models.start_transcription_response import StartTranscriptionResponse
from getstream.models.response import Response
from getstream.models.unblock_user_response import UnblockUserResponse
from getstream.models.update_call_type_response import UpdateCallTypeResponse
from getstream.models.query_calls_response import QueryCallsResponse
from getstream.models.pin_response import PinResponse
from getstream.models.go_live_response import GoLiveResponse


from getstream.models.sort_param_request import SortParamRequest
from getstream.models.call_settings_request import CallSettingsRequest
from getstream.models.call_request import CallRequest
from getstream.models.member_request import MemberRequest
from getstream.models.notification_settings_request import NotificationSettingsRequest

# TODO: generator make imports a set because we have duplicate imports
from getstream.models.user_request import UserRequest
from getstream.models.connect_user_details_request import ConnectUserDetailsRequest


class VideoBaseClient(BaseClient):
    def __init__(self, api_key: str, base_url, token, timeout, user_agent):
        """
        Initializes VideoClient with BaseClient instance
        :param api_key: A string representing the client's API key
        :param base_url: A string representing the base uniform resource locator
        :param token: A string instance representing the client's token
        :param timeout: A number representing the time limit for a request
        :param user_agent: A string representing the user agent
        """
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            token=token,
            timeout=timeout,
            user_agent=user_agent,
        )

    def query_members(
        self,
        type: str,
        id: str,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[SortParamRequest]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
        limit: Optional[int] = None,
        **kwargs
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Query call members
        """
        query_params = {}
        path_params = {}
        json = {}
        json["type"] = type
        json["id"] = id
        if next is not None:
            json["next"] = next
        if prev is not None:
            json["prev"] = prev
        if sort is not None:
            json["sort"] = sort.to_dict()
        if filter_conditions is not None:
            json["filter_conditions"] = filter_conditions
        if limit is not None:
            json["limit"] = limit
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/members",
            QueryMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def get_call(
        self,
        call_type: str,
        call_id: str,
        connection_id: Optional[str] = None,
        members_limit: Optional[int] = None,
        ring: Optional[bool] = None,
        notify: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[GetCallResponse]:
        """
        Get Call
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        query_params["connection_id"] = connection_id
        query_params["members_limit"] = members_limit
        query_params["ring"] = ring
        query_params["notify"] = notify
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/call/{call_type}/{call_id}",
            GetCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call(
        self,
        call_type: str,
        call_id: str,
        custom: Optional[Dict[str, object]] = None,
        settings_override: Optional[CallSettingsRequest] = None,
        starts_at: Optional[datetime] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallResponse]:
        """
        Update Call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if custom is not None:
            json["custom"] = custom
        if settings_override is not None:
            json["settings_override"] = settings_override.to_dict()
        if starts_at is not None:
            json["starts_at"] = starts_at
        for key, value in kwargs.items():
            json[key] = value

        return self.patch(
            "/call/{call_type}/{call_id}",
            UpdateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def get_or_create_call(
        self,
        call_type: str,
        call_id: str,
        data: Optional[CallRequest] = None,
        members_limit: Optional[int] = None,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[GetOrCreateCallResponse]:
        """
        Get or create a call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        query_params["connection_id"] = connection_id
        if data is not None:
            json["data"] = data.to_dict()
        if members_limit is not None:
            json["members_limit"] = members_limit
        if notify is not None:
            json["notify"] = notify
        if ring is not None:
            json["ring"] = ring
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}",
            GetOrCreateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def block_user(
        self, call_type: str, call_id: str, user_id: str, **kwargs
    ) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/block",
            BlockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def send_event(
        self,
        call_type: str,
        call_id: str,
        custom: Optional[Dict[str, object]] = None,
        **kwargs
    ) -> StreamResponse[SendEventResponse]:
        """
        Send custom event
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if custom is not None:
            json["custom"] = custom
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/event",
            SendEventResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def go_live(
        self,
        call_type: str,
        call_id: str,
        start_hls: Optional[bool] = None,
        start_recording: Optional[bool] = None,
        start_transcription: Optional[bool] = None,
        recording_storage_name: Optional[str] = None,
        transcription_storage_name: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[GoLiveResponse]:
        """
        Set call as live
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if start_hls is not None:
            json["start_hls"] = start_hls
        if recording_storage_name is not None:
            json["recording_storage_name"] = recording_storage_name
        if transcription_storage_name is not None:
            json["transcription_storage_name"] = transcription_storage_name
        if start_recording is not None:
            json["start_recording"] = start_recording
        if start_transcription is not None:
            json["start_transcription"] = start_transcription
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/go_live",
            GoLiveResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def join_call(
        self,
        call_type: str,
        call_id: str,
        location: str,
        data: Optional[CallRequest] = None,
        members_limit: Optional[int] = None,
        migrating_from: Optional[str] = None,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        create: Optional[bool] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[JoinCallResponse]:
        """
        Join call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        query_params["connection_id"] = connection_id
        json["location"] = location
        if data is not None:
            json["data"] = data.to_dict()
        if members_limit is not None:
            json["members_limit"] = members_limit
        if migrating_from is not None:
            json["migrating_from"] = migrating_from
        if notify is not None:
            json["notify"] = notify
        if ring is not None:
            json["ring"] = ring
        if create is not None:
            json["create"] = create
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/join",
            JoinCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def list_external_storage(
        self, **kwargs
    ) -> StreamResponse[ListExternalStorageResponse]:
        """
        List external storage
        """
        query_params = {}
        path_params = {}
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/external_storage",
            ListExternalStorageResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_external_storage(
        self,
        name: str,
        storage_type: str,
        bucket: str,
        path: Optional[str] = None,
        aws_s3: Optional[S3Request] = None,
        azure_blob: Optional[AzureRequest] = None,
        gcs_credentials: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[CreateExternalStorageResponse]:
        """
        Create external storage
        """
        query_params = {}
        path_params = {}
        json = {}
        json["name"] = name
        json["storage_type"] = storage_type
        json["bucket"] = bucket
        if path is not None:
            json["path"] = path
        if aws_s3 is not None:
            json["aws_s3"] = aws_s3.to_dict()
        if azure_blob is not None:
            json["azure_blob"] = azure_blob.to_dict()
        if gcs_credentials is not None:
            json["gcs_credentials"] = gcs_credentials
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/external_storage",
            CreateExternalStorageResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def delete_external_storage(
        self, name: str, **kwargs
    ) -> StreamResponse[DeleteExternalStorageResponse]:
        """
        Delete external storage
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name
        for key, value in kwargs.items():
            query_params[key] = value

        return self.delete(
            "/external_storage/{name}",
            DeleteExternalStorageResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_external_storage(
        self,
        name: str,
        storage_type: str,
        bucket: str,
        path: Optional[str] = None,
        aws_s3: Optional[S3Request] = None,
        azure_blob: Optional[AzureRequest] = None,
        gcs_credentials: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[UpdateExternalStorageResponse]:
        """
        Update External Storage
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["name"] = name
        json["storage_type"] = storage_type
        json["bucket"] = bucket
        if path is not None:
            json["path"] = path
        if aws_s3 is not None:
            json["aws_s3"] = aws_s3.to_dict()
        if azure_blob is not None:
            json["azure_blob"] = azure_blob.to_dict()
        if gcs_credentials is not None:
            json["gcs_credentials"] = gcs_credentials
        for key, value in kwargs.items():
            query_params[key] = value

        return self.put(
            "/external_storage/{name}",
            UpdateExternalStorageResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def check_external_storage(
        self, name: str, **kwargs
    ) -> StreamResponse[CheckExternalStorageResponse]:
        """
        Check External Storage
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/external_storage/{name}/check",
            CheckExternalStorageResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def end_call(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/mark_ended",
            EndCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call_members(
        self,
        call_type: str,
        call_id: str,
        remove_members: Optional[List[str]] = None,
        update_members: Optional[List[MemberRequest]] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Update Call Member
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if remove_members is not None:
            json["remove_members"] = remove_members
        if update_members is not None:
            json["update_members"] = update_members.to_dict()
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/members",
            UpdateCallMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def mute_users(
        self,
        call_type: str,
        call_id: str,
        screenshare_audio: Optional[bool] = None,
        user_ids: Optional[List[str]] = None,
        video: Optional[bool] = None,
        audio: Optional[bool] = None,
        mute_all_users: Optional[bool] = None,
        screenshare: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if screenshare_audio is not None:
            json["screenshare_audio"] = screenshare_audio
        if user_ids is not None:
            json["user_ids"] = user_ids
        if video is not None:
            json["video"] = video
        if audio is not None:
            json["audio"] = audio
        if mute_all_users is not None:
            json["mute_all_users"] = mute_all_users
        if screenshare is not None:
            json["screenshare"] = screenshare
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/mute_users",
            MuteUsersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def video_pin(
        self, call_type: str, call_id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["session_id"] = session_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/pin",
            PinResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def list_recordings(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/call/{call_type}/{call_id}/recordings",
            ListRecordingsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_hls_broadcasting(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StartHlsbroadcastingResponse]:
        """
        Start HLS broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/start_broadcasting",
            StartHlsbroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_recording(
        self,
        call_type: str,
        call_id: str,
        recording_external_storage: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        if recording_external_storage is not None:
            json["recording_storage_name"] = recording_external_storage

        return self.post(
            "/call/{call_type}/{call_id}/start_recording",
            StartRecordingResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def list_transcriptions(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[ListTranscriptionsResponse]:
        """
        List transcriptions
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/video/call/{type}/{id}/transcriptions",
            ListTranscriptionsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_transcription(
        self,
        call_type: str,
        call_id: str,
        transcription_external_storage: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Start transcription
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        if transcription_external_storage is not None:
            json["transcription_external_storage"] = transcription_external_storage
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/start_transcription",
            StartTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def stop_hls_broadcasting(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopHlsbroadcastingResponse]:
        """
        Stop HLS broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/stop_broadcasting",
            StopHlsbroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_live(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/stop_live",
            StopLiveResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_recording(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/stop_recording",
            StopRecordingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_transcription(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        query_params = {}
        path_params = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/stop_transcription",
            StopTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def unblock_user(
        self, call_type: str, call_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/unblock",
            UnblockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def video_unpin(
        self, call_type: str, call_id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["session_id"] = session_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/unpin",
            UnpinResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def update_user_permissions(
        self,
        call_type: str,
        call_id: str,
        user_id: str,
        grant_permissions: Optional[List[str]] = None,
        revoke_permissions: Optional[List[str]] = None,
        **kwargs
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Update user permissions
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["user_id"] = user_id
        if grant_permissions is not None:
            json["grant_permissions"] = grant_permissions
        if revoke_permissions is not None:
            json["revoke_permissions"] = revoke_permissions
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/user_permissions",
            UpdateUserPermissionsResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def query_calls(
        self,
        sort: Optional[List[SortParamRequest]] = None,
        watch: Optional[bool] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[QueryCallsResponse]:
        """
        Query call
        """
        query_params = {}
        path_params = {}
        json = {}
        query_params["connection_id"] = connection_id
        if sort is not None:
            json["sort"] = sort.to_dict()
        if watch is not None:
            json["watch"] = watch
        if filter_conditions is not None:
            json["filter_conditions"] = filter_conditions
        if limit is not None:
            json["limit"] = limit
        if next is not None:
            json["next"] = next
        if prev is not None:
            json["prev"] = prev
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/calls",
            QueryCallsResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def list_call_types(self, **kwargs) -> StreamResponse[ListCallTypeResponse]:
        """
        List Call Type
        """
        query_params = {}
        path_params = {}
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/calltypes",
            ListCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_call_type(
        self,
        name: str,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettingsRequest] = None,
        settings: Optional[CallSettingsRequest] = None,
        external_storage: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[CreateCallTypeResponse]:
        """
        Create Call Type
        """
        query_params = {}
        path_params = {}
        json = {}
        json["name"] = name
        if external_storage is not None:
            json["external_storage"] = external_storage
        if grants is not None:
            json["grants"] = grants
        if notification_settings is not None:
            json["notification_settings"] = notification_settings.to_dict()
        if settings is not None:
            json["settings"] = settings.to_dict()
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/calltypes",
            CreateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def delete_call_type(self, name: str, **kwargs) -> StreamResponse[Response]:
        """
        Delete Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name
        for key, value in kwargs.items():
            query_params[key] = value

        return self.delete(
            "/calltypes/{name}",
            Response,
            query_params=query_params,
            path_params=path_params,
        )

    def get_call_type(self, name: str, **kwargs) -> StreamResponse[GetCallTypeResponse]:
        """
        Get Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/calltypes/{name}",
            GetCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call_type(
        self,
        name: str,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettingsRequest] = None,
        settings: Optional[CallSettingsRequest] = None,
        external_storage: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallTypeResponse]:
        """
        Update Call Type
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["name"] = name
        if grants is not None:
            json["grants"] = grants
        if notification_settings is not None:
            json["notification_settings"] = notification_settings.to_dict()
        if settings is not None:
            json["settings"] = settings.to_dict()
        if external_storage is not None:
            json["external_storage"] = external_storage
        for key, value in kwargs.items():
            json[key] = value

        return self.put(
            "/calltypes/{name}",
            UpdateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def delete_device(
        self, id: Optional[str] = None, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[Response]:
        """
        Delete device
        """
        query_params = {}
        path_params = {}
        query_params["id"] = id
        query_params["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.delete(
            "/devices", Response, query_params=query_params, path_params=path_params
        )

    def list_devices(
        self, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[ListDevicesResponse]:
        """
        List devices
        """
        query_params = {}
        path_params = {}
        query_params["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/devices",
            ListDevicesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_device(
        self,
        user_id: Optional[str] = None,
        voip_token: Optional[bool] = None,
        id: Optional[str] = None,
        push_provider: Optional[str] = None,
        push_provider_name: Optional[str] = None,
        user: Optional[UserRequest] = None,
        **kwargs
    ) -> StreamResponse[Response]:
        """
        Create device
        """
        query_params = {}
        path_params = {}
        json = {}
        if user_id is not None:
            json["user_id"] = user_id
        if voip_token is not None:
            json["voip_token"] = voip_token
        if id is not None:
            json["id"] = id
        if push_provider is not None:
            json["push_provider"] = push_provider
        if push_provider_name is not None:
            json["push_provider_name"] = push_provider_name
        if user is not None:
            json["user"] = user.to_dict()
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/devices",
            Response,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def get_edges(self, **kwargs) -> StreamResponse[GetEdgesResponse]:
        """
        Get Edges
        """
        query_params = {}
        path_params = {}
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/edges",
            GetEdgesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_guest(
        self, user: UserRequest, **kwargs
    ) -> StreamResponse[CreateGuestResponse]:
        """
        Create Guest
        """
        query_params = {}
        path_params = {}
        json = {}
        json["user"] = user
        for key, value in kwargs.items():
            json[key] = value

        return self.post(
            "/guest",
            CreateGuestResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def video_connect(
        self, token: str, user_details: ConnectUserDetailsRequest, **kwargs
    ):
        """
        Video Connect (WebSocket)
        """
        query_params = {}
        path_params = {}
        json = {}
        json["token"] = token
        json["user_details"] = user_details
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/video/connect",
            query_params=query_params,
            path_params=path_params,
            json=json,
        )
