from getstream.models.list_transcriptions_response import ListTranscriptionsResponse
from getstream.stream_response import StreamResponse
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
from getstream.video.sync.base_client import VideoBaseClient


class VideoClient(VideoBaseClient):
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

    def call(self, call_type: str, call_id: str):
        """
        Returns instance of Call class
        param type: A string representing the call type
        :param id: A string representing a unique call identifier
        :return: Instance of Call class
        """
        return Call(self, call_type=call_type, call_id=call_id)

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
        return super().query_members(
            type=type,
            id=id,
            next=next,
            prev=prev,
            sort=sort,
            filter_conditions=filter_conditions,
            limit=limit,
            **kwargs,
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
        return super().get_call(
            call_type=call_type,
            call_id=call_id,
            connection_id=connection_id,
            members_limit=members_limit,
            ring=ring,
            notify=notify,
            **kwargs,
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
        return super().update_call(
            call_type=call_type,
            call_id=call_id,
            custom=custom,
            settings_override=settings_override,
            starts_at=starts_at,
            **kwargs,
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
        return super().get_or_create_call(
            call_type=call_type,
            call_id=call_id,
            data=data,
            members_limit=members_limit,
            notify=notify,
            ring=ring,
            connection_id=connection_id,
            **kwargs,
        )

    def block_user(
        self, call_type: str, call_id: str, user_id: str, **kwargs
    ) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        return super().block_user(
            call_type=call_type,
            call_id=call_id,
            user_id=user_id,
            **kwargs,
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
        return super().send_event(
            call_type=call_type,
            call_id=call_id,
            custom=custom,
            **kwargs,
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
        return super().go_live(
            call_type=call_type,
            call_id=call_id,
            start_hls=start_hls,
            start_recording=start_recording,
            start_transcription=start_transcription,
            recording_storage_name=recording_storage_name,
            transcription_storage_name=transcription_storage_name,
            **kwargs,
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
        return super().join_call(
            call_type=call_type,
            call_id=call_id,
            location=location,
            data=data,
            members_limit=members_limit,
            migrating_from=migrating_from,
            notify=notify,
            ring=ring,
            create=create,
            connection_id=connection_id,
            **kwargs,
        )

    def end_call(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        return super().end_call(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
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
        return super().update_call_members(
            call_type=call_type,
            call_id=call_id,
            remove_members=remove_members,
            update_members=update_members,
            **kwargs,
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
        return super().mute_users(
            call_type=call_type,
            call_id=call_id,
            screenshare_audio=screenshare_audio,
            user_ids=user_ids,
            video=video,
            audio=audio,
            mute_all_users=mute_all_users,
            screenshare=screenshare,
            **kwargs,
        )

    def video_pin(
        self, call_type: str, call_id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        return super().video_pin(
            call_type=call_type,
            call_id=call_id,
            session_id=session_id,
            user_id=user_id,
            **kwargs,
        )

    def list_recordings(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings
        """
        return super().list_recordings(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def start_hls_broadcasting(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StartHlsbroadcastingResponse]:
        """
        Start HLS broadcasting
        """
        return super().start_hls_broadcasting(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def start_recording(
        self,
        call_type: str,
        call_id: str,
        recording_storage: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        return super().start_recording(
            call_type=call_type,
            call_id=call_id,
            recording_storage=recording_storage,
            **kwargs,
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
        return super().start_transcription(
            call_type=call_type,
            call_id=call_id,
            transcription_external_storage=transcription_external_storage,
            **kwargs,
        )

    # list_transcriptions
    def list_transcriptions(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[ListTranscriptionsResponse]:
        """
        List transcriptions
        """
        return super().list_transcriptions(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def stop_hls_broadcasting(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopHlsbroadcastingResponse]:
        """
        Stop HLS broadcasting
        """
        return super().stop_hls_broadcasting(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def stop_live(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        return super().stop_live(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def stop_recording(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        return super().stop_recording(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def stop_transcription(
        self, call_type: str, call_id: str, **kwargs
    ) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        return super().stop_transcription(
            call_type=call_type,
            call_id=call_id,
            **kwargs,
        )

    def unblock_user(
        self, call_type: str, call_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        return super().unblock_user(
            call_type=call_type,
            call_id=call_id,
            user_id=user_id,
            **kwargs,
        )

    def video_unpin(
        self, call_type: str, call_id: str, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        return super().video_unpin(
            call_type=call_type,
            call_id=call_id,
            session_id=session_id,
            user_id=user_id,
            **kwargs,
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
        return super().update_user_permissions(
            call_type=call_type,
            call_id=call_id,
            user_id=user_id,
            grant_permissions=grant_permissions,
            revoke_permissions=revoke_permissions,
            **kwargs,
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
        return super().query_calls(
            sort=sort,
            watch=watch,
            filter_conditions=filter_conditions,
            limit=limit,
            next=next,
            prev=prev,
            connection_id=connection_id,
            **kwargs,
        )

    def list_call_types(self, **kwargs) -> StreamResponse[ListCallTypeResponse]:
        """
        List Call Type
        """
        return super().list_call_types(
            **kwargs,
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
        return super().create_call_type(
            name=name,
            grants=grants,
            notification_settings=notification_settings,
            settings=settings,
            external_storage=external_storage,
            **kwargs,
        )

    def delete_call_type(self, name: str, **kwargs) -> StreamResponse[Response]:
        """
        Delete Call Type
        """
        return super().delete_call_type(
            name=name,
            **kwargs,
        )

    def get_call_type(self, name: str, **kwargs) -> StreamResponse[GetCallTypeResponse]:
        """
        Get Call Type
        """
        return super().get_call_type(
            name=name,
            **kwargs,
        )

    def update_call_type(
        self,
        name: str,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettingsRequest] = None,
        external_storage: Optional[str] = None,
        settings: Optional[CallSettingsRequest] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallTypeResponse]:
        """
        Update Call Type
        """
        return super().update_call_type(
            name=name,
            grants=grants,
            notification_settings=notification_settings,
            external_storage=external_storage,
            settings=settings,
            **kwargs,
        )

    def delete_device(
        self, id: Optional[str] = None, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[Response]:
        """
        Delete device
        """
        return super().delete_device(
            id=id,
            user_id=user_id,
            **kwargs,
        )

    def list_devices(
        self, user_id: Optional[str] = None, **kwargs
    ) -> StreamResponse[ListDevicesResponse]:
        """
        List devices
        """
        return super().list_devices(
            user_id=user_id,
            **kwargs,
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
        return super().create_device(
            user_id=user_id,
            voip_token=voip_token,
            id=id,
            push_provider=push_provider,
            push_provider_name=push_provider_name,
            user=user,
            **kwargs,
        )

    def get_edges(self, **kwargs) -> StreamResponse[GetEdgesResponse]:
        """
        Get Edges
        """
        return super().get_edges(
            **kwargs,
        )

    def create_guest(
        self, user: UserRequest, **kwargs
    ) -> StreamResponse[CreateGuestResponse]:
        """
        Create Guest
        """
        return super().create_guest(
            user=user,
            **kwargs,
        )

    def video_connect(
        self, token: str, user_details: ConnectUserDetailsRequest, **kwargs
    ):
        """
        Video Connect (WebSocket)
        """
        return super().video_connect(
            token=token,
            user_details=user_details,
            **kwargs,
        )


class Call:
    def __init__(self, client: VideoClient, call_type: str, call_id: str):
        """
        Initializes Call with BaseClient instance
        :param client: An instance of BaseClient class
        :param type: A string representing the call type
        :param id: A string representing a unique call identifier
        """
        self._client = client
        self._call_type = call_type
        self._call_id = call_id

    def query_members(
        self,
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
        return self._client.query_members(
            type=self._call_type,
            id=self._call_id,
            filter_conditions=filter_conditions,
            limit=limit,
            next=next,
            prev=prev,
            sort=sort,
            **kwargs,
        )

    def get(
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
            self._call_type,
            self._call_id,
            connection_id=connection_id,
            members_limit=members_limit,
            ring=ring,
            notify=notify,
            **kwargs,
        )

    def update(
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
            self._call_type,
            self._call_id,
            custom=custom,
            settings_override=settings_override,
            starts_at=starts_at,
            **kwargs,
        )

    def create(
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
            self._call_type,
            self._call_id,
            connection_id=connection_id,
            data=data,
            members_limit=members_limit,
            notify=notify,
            ring=ring,
            **kwargs,
        )

    def block_user(self, user_id: str, **kwargs) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        return self._client.block_user(
            self._call_type, self._call_id, user_id=user_id, **kwargs
        )

    def send_event(
        self, custom: Optional[Dict[str, object]] = None, **kwargs
    ) -> StreamResponse[SendEventResponse]:
        """
        Send custom event
        """
        return self._client.send_event(
            self._call_type, self._call_id, custom=custom, **kwargs
        )

    def go_live(
        self,
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
        return self._client.go_live(
            self._call_type,
            self._call_id,
            start_hls=start_hls,
            start_recording=start_recording,
            start_transcription=start_transcription,
            recording_storage_name=recording_storage_name,
            transcription_storage_name=transcription_storage_name,
            **kwargs,
        )

    def join(
        self,
        location: str,
        create: Optional[bool] = None,
        data: Optional[CallRequest] = None,
        members_limit: Optional[int] = None,
        migrating_from: Optional[str] = None,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        connection_id: Optional[str] = None,
        **kwargs
    ) -> StreamResponse[JoinCallResponse]:
        """
        Join call
        """
        return self._client.join_call(
            self._call_type,
            self._call_id,
            connection_id=connection_id,
            location=location,
            create=create,
            data=data,
            members_limit=members_limit,
            migrating_from=migrating_from,
            notify=notify,
            ring=ring,
            **kwargs,
        )

    def end(self, **kwargs) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        return self._client.end_call(self._call_type, self._call_id, **kwargs)

    def update_members(
        self,
        remove_members: Optional[List[str]] = None,
        update_members: Optional[List[MemberRequest]] = None,
        **kwargs
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Update Call Member
        """
        return self._client.update_call_members(
            self._call_type,
            self._call_id,
            remove_members=remove_members,
            update_members=update_members,
            **kwargs,
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
            self._call_type,
            self._call_id,
            screenshare=screenshare,
            screenshare_audio=screenshare_audio,
            user_ids=user_ids,
            video=video,
            audio=audio,
            mute_all_users=mute_all_users,
            **kwargs,
        )

    def video_pin(
        self, session_id: str, user_id: str, **kwargs
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        return self._client.video_pin(
            self._call_type,
            self._call_id,
            session_id=session_id,
            user_id=user_id,
            **kwargs,
        )

    def list_recordings(self, **kwargs) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings
        """
        return self._client.list_recordings(self._call_type, self._call_id, **kwargs)

    def start_hls_broadcasting(
        self, **kwargs
    ) -> StreamResponse[StartHlsbroadcastingResponse]:
        """
        Start HLS broadcasting
        """
        return self._client.start_hls_broadcasting(
            self._call_type, self._call_id, **kwargs
        )

    def start_recording(self, **kwargs) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        return self._client.start_recording(self._call_type, self._call_id, **kwargs)

    def list_transcriptions(
        self, **kwargs
    ) -> StreamResponse[ListTranscriptionsResponse]:
        """
        List transcriptions
        """
        return self._client.list_transcriptions(self._type, self._id, **kwargs)

    def start_transcription(
        self, transcription_external_storage: Optional[str] = None, **kwargs
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Start transcription
        """
        return self._client.start_transcription(
            self._call_type,
            self._call_id,
            transcription_external_storage=transcription_external_storage,
            **kwargs,
        )

    def stop_hls_broadcasting(
        self, **kwargs
    ) -> StreamResponse[StopHlsbroadcastingResponse]:
        """
        Stop HLS broadcasting
        """
        return self._client.stop_hls_broadcasting(
            self._call_type, self._call_id, **kwargs
        )

    def stop_live(self, **kwargs) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        return self._client.stop_live(self._call_type, self._call_id, **kwargs)

    def stop_recording(self, **kwargs) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        return self._client.stop_recording(self._call_type, self._call_id, **kwargs)

    def stop_transcription(self, **kwargs) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        return self._client.stop_transcription(self._call_type, self._call_id, **kwargs)

    def unblock_user(
        self, user_id: str, **kwargs
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        return self._client.unblock_user(
            self._call_type, self._call_id, user_id=user_id, **kwargs
        )

    def video_unpin(
        self, user_id: str, session_id: str, **kwargs
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        return self._client.video_unpin(
            self._call_type,
            self._call_id,
            user_id=user_id,
            session_id=session_id,
            **kwargs,
        )

    def update_user_permissions(
        self,
        user_id: str,
        grant_permissions: Optional[List[str]] = None,
        revoke_permissions: Optional[List[str]] = None,
        **kwargs
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Update user permissions
        """
        return self._client.update_user_permissions(
            self._call_type,
            self._call_id,
            user_id=user_id,
            grant_permissions=grant_permissions,
            revoke_permissions=revoke_permissions,
            **kwargs,
        )
