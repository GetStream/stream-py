# THIS FILE IS GENERATED FROM github.com/GetStream/protocol/tree/main/openapi-gen/templates/python/client.tmpl
from getstream.stream_response import StreamResponse
from getstream.sync.base import BaseClient
from typing import Optional, List, Dict
from datetime import datetime
from getstream.models.send_reaction_response import SendReactionResponse
from getstream.models.reject_call_response import RejectCallResponse
from getstream.models.get_edges_response import GetEdgesResponse
from getstream.models.request_permission_response import RequestPermissionResponse
from getstream.models.list_devices_response import ListDevicesResponse
from getstream.models.accept_call_response import AcceptCallResponse
from getstream.models.stop_live_response import StopLiveResponse
from getstream.models.start_recording_response import StartRecordingResponse
from getstream.models.stop_transcription_response import StopTranscriptionResponse
from getstream.models.join_call_response import JoinCallResponse
from getstream.models.get_call_type_response import GetCallTypeResponse
from getstream.models.get_call_response import GetCallResponse
from getstream.models.go_live_response import GoLiveResponse
from getstream.models.list_call_type_response import ListCallTypeResponse
from getstream.models.end_call_response import EndCallResponse
from getstream.models.start_hls_broadcasting_response import (
    StartHlsbroadcastingResponse,
)
from getstream.models.get_or_create_call_response import GetOrCreateCallResponse
from getstream.models.response import Response
from getstream.models.update_call_response import UpdateCallResponse
from getstream.models.stop_hls_broadcasting_response import StopHlsbroadcastingResponse
from getstream.models.pin_response import PinResponse
from getstream.models.create_call_type_response import CreateCallTypeResponse
from getstream.models.query_members_response import QueryMembersResponse
from getstream.models.block_user_response import BlockUserResponse
from getstream.models.create_guest_response import CreateGuestResponse
from getstream.models.mute_users_response import MuteUsersResponse
from getstream.models.send_event_response import SendEventResponse
from getstream.models.unblock_user_response import UnblockUserResponse
from getstream.models.unpin_response import UnpinResponse
from getstream.models.update_call_type_response import UpdateCallTypeResponse
from getstream.models.list_recordings_response import ListRecordingsResponse
from getstream.models.update_user_permissions_response import (
    UpdateUserPermissionsResponse,
)
from getstream.models.query_calls_response import QueryCallsResponse
from getstream.models.stop_recording_response import StopRecordingResponse
from getstream.models.start_transcription_response import StartTranscriptionResponse
from getstream.models.update_call_members_response import UpdateCallMembersResponse


from getstream.models.sort_param_request import SortParamRequest


from getstream.models.call_settings_request import CallSettingsRequest


from getstream.models.call_request import CallRequest


from getstream.models.call_request import CallRequest


from getstream.models.member_request import MemberRequest


from getstream.models.sort_param_request import SortParamRequest


from getstream.models.notification_settings_request import NotificationSettingsRequest
from getstream.models.call_settings_request import CallSettingsRequest


from getstream.models.notification_settings_request import NotificationSettingsRequest
from getstream.models.call_settings_request import CallSettingsRequest


from getstream.models.user_request import UserRequest


from getstream.models.user_request import UserRequest


from getstream.models.connect_user_details_request import ConnectUserDetailsRequest


class VideoClient(BaseClient):
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

    def call(self, type: str, id: str):
        """
        Returns instance of Call class
        param type: A string representing the call type
        :param id: A string representing a unique call identifier
        :return: Instance of Call class
        """
        return Call(self, type, id)

    def query_members(
        self,
        id: str,
        type: str,
        filter_conditions: Optional[Dict[str, object]] = None,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[SortParamRequest]] = None,
        **kwargs
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Query call members
        """
        query_params = {}
        path_params = {}
        json = {}
        json["id"] = id
        json["type"] = type
        if filter_conditions is not None:
            json["filter_conditions"] = filter_conditions
        if limit is not None:
            json["limit"] = limit
        if next is not None:
            json["next"] = next
        if prev is not None:
            json["prev"] = prev
        if sort is not None:
            json["sort"] = sort.to_dict()
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/members",
            QueryMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def get_call(
        self,
        type: str,
        id: str,
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
        path_params["type"] = type
        path_params["id"] = id
        query_params["connection_id"] = connection_id
        query_params["members_limit"] = members_limit
        query_params["ring"] = ring
        query_params["notify"] = notify
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/call/{type}/{id}",
            GetCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call(
        self,
        type: str,
        id: str,
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
        path_params["type"] = type
        path_params["id"] = id
        if custom is not None:
            json["custom"] = custom
        if settings_override is not None:
            json["settings_override"] = settings_override.to_dict()
        if starts_at is not None:
            json["starts_at"] = starts_at
        for key, value in kwargs.items():
            json[key] = value

        return self.patch(
            "/call/{type}/{id}",
            UpdateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def get_or_create_call(
        self,
        type: str,
        id: str,
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
        path_params["type"] = type
        path_params["id"] = id
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
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}",
            GetOrCreateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def accept_call(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[AcceptCallResponse]:
        """
        Accept Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/accept",
            AcceptCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def block_user(
        self, type: str, id: str, user_id: str, **kwargs
    ) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/block",
            BlockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def send_event(
        self, type: str, id: str, custom: Optional[Dict[str, object]] = None, **kwargs
    ) -> StreamResponse[SendEventResponse]:
        """
        Send custom event
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        if custom is not None:
            json["custom"] = custom
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/event",
            SendEventResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def go_live(
        self,
        type: str,
        id: str,
        start_recording: Optional[bool] = None,
        start_transcription: Optional[bool] = None,
        start_hls: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[GoLiveResponse]:
        """
        Set call as live
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        if start_recording is not None:
            json["start_recording"] = start_recording
        if start_transcription is not None:
            json["start_transcription"] = start_transcription
        if start_hls is not None:
            json["start_hls"] = start_hls
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/go_live",
            GoLiveResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def join_call(
        self,
        type: str,
        id: str,
        location: str,
        ring: Optional[bool] = None,
        create: Optional[bool] = None,
        data: Optional[CallRequest] = None,
        members_limit: Optional[int] = None,
        migrating_from: Optional[str] = None,
        notify: Optional[bool] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[JoinCallResponse]:
        """
        Join call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        query_params["connection_id"] = connection_id
        json["location"] = location
        if ring is not None:
            json["ring"] = ring
        if create is not None:
            json["create"] = create
        if data is not None:
            json["data"] = data.to_dict()
        if members_limit is not None:
            json["members_limit"] = members_limit
        if migrating_from is not None:
            json["migrating_from"] = migrating_from
        if notify is not None:
            json["notify"] = notify
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/join",
            JoinCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def end_call(self, type: str, id: str, **kwargs) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/mark_ended",
            EndCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call_members(
        self,
        type: str,
        id: str,
        update_members: Optional[List[MemberRequest]] = None,
        remove_members: Optional[List[str]] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Update Call Member
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        if update_members is not None:
            json["update_members"] = update_members.to_dict()
        if remove_members is not None:
            json["remove_members"] = remove_members
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/members",
            UpdateCallMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def mute_users(
        self,
        type: str,
        id: str,
        mute_all_users: Optional[bool] = None,
        screenshare: Optional[bool] = None,
        screenshare_audio: Optional[bool] = None,
        user_ids: Optional[List[str]] = None,
        video: Optional[bool] = None,
        audio: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        if mute_all_users is not None:
            json["mute_all_users"] = mute_all_users
        if screenshare is not None:
            json["screenshare"] = screenshare
        if screenshare_audio is not None:
            json["screenshare_audio"] = screenshare_audio
        if user_ids is not None:
            json["user_ids"] = user_ids
        if video is not None:
            json["video"] = video
        if audio is not None:
            json["audio"] = audio
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/mute_users",
            MuteUsersResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def video_pin(
        self, type: str, id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        json["session_id"] = session_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/pin",
            PinResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def send_video_reaction(
        self,
        call_type: str,
        call_id: str,
        type: str,
        custom: Optional[Dict[str, object]] = None,
        emoji_code: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[SendReactionResponse]:
        """
        Send reaction to the call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["call_type"] = call_type
        path_params["call_id"] = call_id
        json["type"] = type
        if custom is not None:
            json["custom"] = custom
        if emoji_code is not None:
            json["emoji_code"] = emoji_code
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{call_type}/{call_id}/reaction",
            SendReactionResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def list_recordings(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.get(
            "/call/{type}/{id}/recordings",
            ListRecordingsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def reject_call(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[RejectCallResponse]:
        """
        Reject Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/reject",
            RejectCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def request_permission(
        self, type: str, id: str, permissions: List[str], **kwargs
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Request permission
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        json["permissions"] = permissions
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/request_permission",
            RequestPermissionResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def start_hls_broadcasting(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StartHlsbroadcastingResponse]:
        """
        Start HLS broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/start_broadcasting",
            StartHlsbroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_recording(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/start_recording",
            StartRecordingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_transcription(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Start transcription
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/start_transcription",
            StartTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_hls_broadcasting(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StopHlsbroadcastingResponse]:
        """
        Stop HLS broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/stop_broadcasting",
            StopHlsbroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_live(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/stop_live",
            StopLiveResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_recording(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/stop_recording",
            StopRecordingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_transcription(
        self, type: str, id: str, **kwargs
    ) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/stop_transcription",
            StopTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def unblock_user(
        self, type: str, id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/unblock",
            UnblockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def video_unpin(
        self, type: str, id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        query_params = {}
        path_params = {}
        json = {}
        path_params["type"] = type
        path_params["id"] = id
        json["session_id"] = session_id
        json["user_id"] = user_id
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/unpin",
            UnpinResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def update_user_permissions(
        self,
        type: str,
        id: str,
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
        path_params["type"] = type
        path_params["id"] = id
        json["user_id"] = user_id
        if grant_permissions is not None:
            json["grant_permissions"] = grant_permissions
        if revoke_permissions is not None:
            json["revoke_permissions"] = revoke_permissions
        for key, value in kwargs.items():
            query_params[key] = value

        return self.post(
            "/call/{type}/{id}/user_permissions",
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
            query_params[key] = value

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
        **kwargs
    ) -> StreamResponse[CreateCallTypeResponse]:
        """
        Create Call Type
        """
        query_params = {}
        path_params = {}
        json = {}
        json["name"] = name
        if grants is not None:
            json["grants"] = grants
        if notification_settings is not None:
            json["notification_settings"] = notification_settings.to_dict()
        if settings is not None:
            json["settings"] = settings.to_dict()
        for key, value in kwargs.items():
            query_params[key] = value

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
        for key, value in kwargs.items():
            query_params[key] = value

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
        user: Optional[UserRequest] = None,
        user_id: Optional[str] = None,
        voip_token: Optional[bool] = None,
        id: Optional[str] = None,
        push_provider: Optional[str] = None,
        push_provider_name: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[Response]:
        """
        Create device
        """
        query_params = {}
        path_params = {}
        json = {}
        if user is not None:
            json["user"] = user.to_dict()
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
        for key, value in kwargs.items():
            query_params[key] = value

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
            query_params[key] = value

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


class Call:
    def __init__(self, client: VideoClient, type: str, id: str):
        """
        Initializes Call with BaseClient instance
        :param client: An instance of BaseClient class
        :param type: A string representing the call type
        :param id: A string representing a unique call identifier
        """
        self._client = client
        self._type = type
        self._id = id

    def query_members(
        self,
        type: str,
        id: str,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[SortParamRequest]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
        **kwargs
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Query call members
        """
        return self._client.query_members(
            self._type,
            self._id,
            type=type,
            id=id,
            limit=limit,
            next=next,
            prev=prev,
            sort=sort,
            filter_conditions=filter_conditions,
            **kwargs
        )

    def get_call(
        self,
        connection_id: Optional[str] = None,
        members_limit: Optional[int] = None,
        ring: Optional[bool] = None,
        notify: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[GetCallResponse]:
        """
        Get Call
        """
        return self._client.get_call(
            self._type, self._idconnection_idmembers_limitringnotify**kwargs
        )

    def update_call(
        self,
        custom: Optional[Dict[str, object]] = None,
        settings_override: Optional[CallSettingsRequest] = None,
        starts_at: Optional[datetime] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallResponse]:
        """
        Update Call
        """
        return self._client.update_call(
            self._type,
            self._id,
            custom=custom,
            settings_override=settings_override,
            starts_at=starts_at,
            **kwargs
        )

    def get_or_create_call(
        self,
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
        return self._client.get_or_create_call(
            self._type,
            self._id,
            connection_iddata=data,
            members_limit=members_limit,
            notify=notify,
            ring=ring,
            **kwargs
        )

    def accept_call(self, **kwargs) -> StreamResponse[AcceptCallResponse]:
        """
        Accept Call
        """
        return self._client.accept_call(self._type, self._id**kwargs)

    def block_user(self, user_id: str, **kwargs) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        return self._client.block_user(self._type, self._id, user_id=user_id, **kwargs)

    def send_event(
        self, custom: Optional[Dict[str, object]] = None, **kwargs
    ) -> StreamResponse[SendEventResponse]:
        """
        Send custom event
        """
        return self._client.send_event(self._type, self._id, custom=custom, **kwargs)

    def go_live(
        self,
        start_hls: Optional[bool] = None,
        start_recording: Optional[bool] = None,
        start_transcription: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[GoLiveResponse]:
        """
        Set call as live
        """
        return self._client.go_live(
            self._type,
            self._id,
            start_hls=start_hls,
            start_recording=start_recording,
            start_transcription=start_transcription,
            **kwargs
        )

    def join_call(
        self,
        location: str,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        create: Optional[bool] = None,
        data: Optional[CallRequest] = None,
        members_limit: Optional[int] = None,
        migrating_from: Optional[str] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[JoinCallResponse]:
        """
        Join call
        """
        return self._client.join_call(
            self._type,
            self._id,
            connection_idlocation=location,
            notify=notify,
            ring=ring,
            create=create,
            data=data,
            members_limit=members_limit,
            migrating_from=migrating_from,
            **kwargs
        )

    def end_call(self, **kwargs) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        return self._client.end_call(self._type, self._id**kwargs)

    def update_call_members(
        self,
        remove_members: Optional[List[str]] = None,
        update_members: Optional[List[MemberRequest]] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Update Call Member
        """
        return self._client.update_call_members(
            self._type,
            self._id,
            remove_members=remove_members,
            update_members=update_members,
            **kwargs
        )

    def mute_users(
        self,
        screenshare: Optional[bool] = None,
        screenshare_audio: Optional[bool] = None,
        user_ids: Optional[List[str]] = None,
        video: Optional[bool] = None,
        audio: Optional[bool] = None,
        mute_all_users: Optional[bool] = None,
        **kwargs
    ) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users
        """
        return self._client.mute_users(
            self._type,
            self._id,
            screenshare=screenshare,
            screenshare_audio=screenshare_audio,
            user_ids=user_ids,
            video=video,
            audio=audio,
            mute_all_users=mute_all_users,
            **kwargs
        )

    def video_pin(
        self, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        return self._client.video_pin(
            self._type, self._id, session_id=session_id, user_id=user_id, **kwargs
        )

    def send_video_reaction(
        self,
        type: str,
        custom: Optional[Dict[str, object]] = None,
        emoji_code: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[SendReactionResponse]:
        """
        Send reaction to the call
        """
        return self._client.send_video_reaction(
            self._type,
            self._id,
            type=type,
            custom=custom,
            emoji_code=emoji_code,
            **kwargs
        )

    def list_recordings(self, **kwargs) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings
        """
        return self._client.list_recordings(self._type, self._id**kwargs)

    def reject_call(self, **kwargs) -> StreamResponse[RejectCallResponse]:
        """
        Reject Call
        """
        return self._client.reject_call(self._type, self._id**kwargs)

    def request_permission(
        self, permissions: List[str], **kwargs
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Request permission
        """
        return self._client.request_permission(
            self._type, self._id, permissions=permissions, **kwargs
        )

    def start_hls_broadcasting(
        self, **kwargs
    ) -> StreamResponse[StartHlsbroadcastingResponse]:
        """
        Start HLS broadcasting
        """
        return self._client.start_hls_broadcasting(self._type, self._id**kwargs)

    def start_recording(self, **kwargs) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        return self._client.start_recording(self._type, self._id**kwargs)

    def start_transcription(
        self, **kwargs
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Start transcription
        """
        return self._client.start_transcription(self._type, self._id**kwargs)

    def stop_hls_broadcasting(
        self, **kwargs
    ) -> StreamResponse[StopHlsbroadcastingResponse]:
        """
        Stop HLS broadcasting
        """
        return self._client.stop_hls_broadcasting(self._type, self._id**kwargs)

    def stop_live(self, **kwargs) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        return self._client.stop_live(self._type, self._id**kwargs)

    def stop_recording(self, **kwargs) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        return self._client.stop_recording(self._type, self._id**kwargs)

    def stop_transcription(self, **kwargs) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        return self._client.stop_transcription(self._type, self._id**kwargs)

    def unblock_user(
        self, user_id: str, **kwargs
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        return self._client.unblock_user(
            self._type, self._id, user_id=user_id, **kwargs
        )

    def video_unpin(
        self, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        return self._client.video_unpin(
            self._type, self._id, session_id=session_id, user_id=user_id, **kwargs
        )

    def update_user_permissions(
        self,
        user_id: str,
        revoke_permissions: Optional[List[str]] = None,
        grant_permissions: Optional[List[str]] = None,
        **kwargs
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Update user permissions
        """
        return self._client.update_user_permissions(
            self._type,
            self._id,
            user_id=user_id,
            revoke_permissions=revoke_permissions,
            grant_permissions=grant_permissions,
            **kwargs
        )

    def query_calls(
        self,
        prev: Optional[str] = None,
        sort: Optional[List[SortParamRequest]] = None,
        watch: Optional[bool] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[QueryCallsResponse]:
        """
        Query call
        """
        return self._client.query_calls(
            self._type,
            self._id,
            connection_idprev=prev,
            sort=sort,
            watch=watch,
            filter_conditions=filter_conditions,
            limit=limit,
            next=next,
            **kwargs
        )

    def list_call_types(self, **kwargs) -> StreamResponse[ListCallTypeResponse]:
        """
        List Call Type
        """
        return self._client.list_call_types(self._type, self._id**kwargs)

    def create_call_type(
        self,
        name: str,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettingsRequest] = None,
        settings: Optional[CallSettingsRequest] = None,
        **kwargs
    ) -> StreamResponse[CreateCallTypeResponse]:
        """
        Create Call Type
        """
        return self._client.create_call_type(
            self._type,
            self._id,
            name=name,
            grants=grants,
            notification_settings=notification_settings,
            settings=settings,
            **kwargs
        )

    def delete_call_type(self, **kwargs) -> StreamResponse[Response]:
        """
        Delete Call Type
        """
        return self._client.delete_call_type(self._type, self._id**kwargs)

    def get_call_type(self, **kwargs) -> StreamResponse[GetCallTypeResponse]:
        """
        Get Call Type
        """
        return self._client.get_call_type(self._type, self._id**kwargs)

    def update_call_type(
        self,
        settings: Optional[CallSettingsRequest] = None,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettingsRequest] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallTypeResponse]:
        """
        Update Call Type
        """
        return self._client.update_call_type(
            self._type,
            self._id,
            settings=settings,
            grants=grants,
            notification_settings=notification_settings,
            **kwargs
        )

    def delete_device(
        self, id: Optional[str] = None, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[Response]:
        """
        Delete device
        """
        return self._client.delete_device(self._type, self._ididuser_id**kwargs)

    def list_devices(
        self, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[ListDevicesResponse]:
        """
        List devices
        """
        return self._client.list_devices(self._type, self._iduser_id**kwargs)

    def create_device(
        self,
        user: Optional[UserRequest] = None,
        user_id: Optional[str] = None,
        voip_token: Optional[bool] = None,
        id: Optional[str] = None,
        push_provider: Optional[str] = None,
        push_provider_name: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[Response]:
        """
        Create device
        """
        return self._client.create_device(
            self._type,
            self._id,
            user=user,
            user_id=user_id,
            voip_token=voip_token,
            id=id,
            push_provider=push_provider,
            push_provider_name=push_provider_name,
            **kwargs
        )

    def get_edges(self, **kwargs) -> StreamResponse[GetEdgesResponse]:
        """
        Get Edges
        """
        return self._client.get_edges(self._type, self._id**kwargs)

    def create_guest(
        self, user: UserRequest, **kwargs
    ) -> StreamResponse[CreateGuestResponse]:
        """
        Create Guest
        """
        return self._client.create_guest(self._type, self._id, user=user, **kwargs)

    def video_connect(
        self, token: str, user_details: ConnectUserDetailsRequest, **kwargs
    ):
        """
        Video Connect (WebSocket)
        """
        return self._client.video_connect(
            self._type, self._id, token=token, user_details=user_details, **kwargs
        )
