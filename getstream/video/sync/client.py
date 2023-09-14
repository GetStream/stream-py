from dataclasses import asdict
from typing import Optional
from getstream.models.list_recordings_response import ListRecordingsResponse
from getstream.models.list_call_type_response import ListCallTypeResponse
from getstream.models.end_call_response import EndCallResponse
from getstream.models.start_recording_response import StartRecordingResponse
from getstream.models.request_permission_response import RequestPermissionResponse
from getstream.models.go_live_response import GoLiveResponse
from getstream.models.mute_users_request import MuteUsersRequest
from getstream.models.update_call_members_request import UpdateCallMembersRequest
from getstream.models.stop_recording_response import StopRecordingResponse
from getstream.models.create_call_type_response import CreateCallTypeResponse
from getstream.models.create_guest_request import CreateGuestRequest
from getstream.models.send_reaction_request import SendReactionRequest
from getstream.models.stop_broadcasting_response import StopBroadcastingResponse
from getstream.models.query_calls_response import QueryCallsResponse
from getstream.models.send_event_request import SendEventRequest
from getstream.models.update_call_members_response import UpdateCallMembersResponse
from getstream.models.query_calls_request import QueryCallsRequest
from getstream.models.ws_auth_message_request import WsauthMessageRequest
from getstream.models.create_call_type_request import CreateCallTypeRequest
from getstream.models.get_edges_response import GetEdgesResponse
from getstream.models.stop_transcription_response import StopTranscriptionResponse
from getstream.models.unblock_user_response import UnblockUserResponse
from getstream.models.send_event_response import SendEventResponse
from getstream.models.pin_request import PinRequest
from getstream.models.stop_live_response import StopLiveResponse
from getstream.models.get_or_create_call_response import GetOrCreateCallResponse
from getstream.models.accept_call_response import AcceptCallResponse
from getstream.models.go_live_request import GoLiveRequest
from getstream.models.join_call_response import JoinCallResponse
from getstream.models.query_members_response import QueryMembersResponse
from getstream.models.reject_call_response import RejectCallResponse
from getstream.models.start_broadcasting_response import StartBroadcastingResponse
from getstream.models.get_call_type_response import GetCallTypeResponse
from getstream.models.get_call_response import GetCallResponse
from getstream.models.get_or_create_call_request import GetOrCreateCallRequest
from getstream.models.block_user_request import BlockUserRequest
from getstream.models.block_user_response import BlockUserResponse
from getstream.models.query_members_request import QueryMembersRequest
from getstream.models.update_call_request import UpdateCallRequest
from getstream.models.list_devices_response import ListDevicesResponse
from getstream.models.create_device_request import CreateDeviceRequest
from getstream.models.update_call_response import UpdateCallResponse
from getstream.models.unpin_request import UnpinRequest
from getstream.models.create_guest_response import CreateGuestResponse
from getstream.models.start_transcription_response import StartTranscriptionResponse
from getstream.models.unpin_response import UnpinResponse
from getstream.models.pin_response import PinResponse
from getstream.models.update_user_permissions_response import (
    UpdateUserPermissionsResponse,
)
from getstream.models.mute_users_response import MuteUsersResponse
from getstream.models.send_reaction_response import SendReactionResponse
from getstream.models.update_call_type_response import UpdateCallTypeResponse
from getstream.models.request_permission_request import RequestPermissionRequest
from getstream.models.response import Response
from getstream.models.update_user_permissions_request import (
    UpdateUserPermissionsRequest,
)
from getstream.models.unblock_user_request import UnblockUserRequest
from getstream.models.update_call_type_request import UpdateCallTypeRequest
from getstream.models.join_call_request import JoinCallRequest
from getstream.stream_response import StreamResponse
from getstream.sync.base import BaseClient


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

    def query_members(
        self, data: QueryMembersRequest
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Query call members
        """
        query_params = {}
        path_params = {}

        self.post(
            "/call/members",
            QueryMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def get_call(
        self,
        type: str,
        id: str,
        connection_id: Optional[str] = None,
        members_limit: Optional[int] = None,
        ring: Optional[bool] = None,
        notify: Optional[bool] = None,
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

        self.get(
            "/call/{type}/{id}",
            GetCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call(
        self, type: str, id: str, data: UpdateCallRequest
    ) -> StreamResponse[UpdateCallResponse]:
        """
        Update Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.patch(
            "/call/{type}/{id}",
            UpdateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def get_or_create_call(
        self,
        type: str,
        id: str,
        data: GetOrCreateCallRequest,
        connection_id: Optional[str] = None,
    ) -> StreamResponse[GetOrCreateCallResponse]:
        """
        Get or create a call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        query_params["connection_id"] = connection_id

        self.post(
            "/call/{type}/{id}",
            GetOrCreateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def accept_call(self, type: str, id: str) -> StreamResponse[AcceptCallResponse]:
        """
        Accept Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/accept",
            AcceptCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def block_user(
        self, type: str, id: str, data: BlockUserRequest
    ) -> StreamResponse[BlockUserResponse]:
        """
        Block user on a call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/block",
            BlockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def send_event(
        self, type: str, id: str, data: SendEventRequest
    ) -> StreamResponse[SendEventResponse]:
        """
        Send custom event
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/event",
            SendEventResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def go_live(
        self, type: str, id: str, data: GoLiveRequest
    ) -> StreamResponse[GoLiveResponse]:
        """
        Set call as live
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/go_live",
            GoLiveResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def join_call(
        self,
        type: str,
        id: str,
        data: JoinCallRequest,
        connection_id: Optional[str] = None,
    ) -> StreamResponse[JoinCallResponse]:
        """
        Join call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        query_params["connection_id"] = connection_id

        self.post(
            "/call/{type}/{id}/join",
            JoinCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def end_call(self, type: str, id: str) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/mark_ended",
            EndCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call_members(
        self, type: str, id: str, data: UpdateCallMembersRequest
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Update Call Member
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/members",
            UpdateCallMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def mute_users(
        self, type: str, id: str, data: MuteUsersRequest
    ) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/mute_users",
            MuteUsersResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def video_pin(
        self, type: str, id: str, data: PinRequest
    ) -> StreamResponse[PinResponse]:
        """
        Pin
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/pin",
            PinResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def send_video_reaction(
        self, type: str, id: str, data: SendReactionRequest
    ) -> StreamResponse[SendReactionResponse]:
        """
        Send reaction to the call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/reaction",
            SendReactionResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def list_recordings_type_id_0(
        self, type: str, id: str
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings (type, id)
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.get(
            "/call/{type}/{id}/recordings",
            ListRecordingsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def reject_call(self, type: str, id: str) -> StreamResponse[RejectCallResponse]:
        """
        Reject Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/reject",
            RejectCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def request_permission(
        self, type: str, id: str, data: RequestPermissionRequest
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Request permission
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/request_permission",
            RequestPermissionResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def start_broadcasting(
        self, type: str, id: str
    ) -> StreamResponse[StartBroadcastingResponse]:
        """
        Start broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/start_broadcasting",
            StartBroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_recording(
        self, type: str, id: str
    ) -> StreamResponse[StartRecordingResponse]:
        """
        Start recording
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/start_recording",
            StartRecordingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def start_transcription(
        self, type: str, id: str
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Start transcription
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/start_transcription",
            StartTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_broadcasting(
        self, type: str, id: str
    ) -> StreamResponse[StopBroadcastingResponse]:
        """
        Stop broadcasting
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/stop_broadcasting",
            StopBroadcastingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_live(self, type: str, id: str) -> StreamResponse[StopLiveResponse]:
        """
        Set call as not live
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/stop_live",
            StopLiveResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_recording(
        self, type: str, id: str
    ) -> StreamResponse[StopRecordingResponse]:
        """
        Stop recording
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/stop_recording",
            StopRecordingResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def stop_transcription(
        self, type: str, id: str
    ) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stop transcription
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/stop_transcription",
            StopTranscriptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def unblock_user(
        self, type: str, id: str, data: UnblockUserRequest
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user on a call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/unblock",
            UnblockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def video_unpin(
        self, type: str, id: str, data: UnpinRequest
    ) -> StreamResponse[UnpinResponse]:
        """
        Unpin
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/unpin",
            UnpinResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def update_user_permissions(
        self, type: str, id: str, data: UpdateUserPermissionsRequest
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Update user permissions
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        self.post(
            "/call/{type}/{id}/user_permissions",
            UpdateUserPermissionsResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def list_recordings_type_id_session_1(
        self, type: str, id: str, session: str
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings (type, id, session)
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        path_params["session"] = session

        self.get(
            "/call/{type}/{id}/{session}/recordings",
            ListRecordingsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def query_calls(
        self, data: QueryCallsRequest, connection_id: Optional[str] = None
    ) -> StreamResponse[QueryCallsResponse]:
        """
        Query call
        """
        query_params = {}
        path_params = {}
        query_params["connection_id"] = connection_id

        self.post(
            "/calls",
            QueryCallsResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def list_call_types(self) -> StreamResponse[ListCallTypeResponse]:
        """
        List Call Type
        """
        query_params = {}
        path_params = {}

        self.get(
            "/calltypes",
            ListCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_call_type(
        self, data: CreateCallTypeRequest
    ) -> StreamResponse[CreateCallTypeResponse]:
        """
        Create Call Type
        """
        query_params = {}
        path_params = {}

        self.post(
            "/calltypes",
            CreateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def delete_call_type(self, name: str) -> StreamResponse[Response]:
        """
        Delete Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name

        self.delete(
            "/calltypes/{name}",
            Response,
            query_params=query_params,
            path_params=path_params,
        )

    def get_call_type(self, name: str) -> StreamResponse[GetCallTypeResponse]:
        """
        Get Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name

        self.get(
            "/calltypes/{name}",
            GetCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call_type(
        self, name: str, data: UpdateCallTypeRequest
    ) -> StreamResponse[UpdateCallTypeResponse]:
        """
        Update Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name

        self.put(
            "/calltypes/{name}",
            UpdateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def delete_device(
        self, id: Optional[str] = None, user_id: Optional[str] = None
    ) -> StreamResponse[Response]:
        """
        Delete device
        """
        query_params = {}
        path_params = {}
        query_params["id"] = id
        query_params["user_id"] = user_id

        self.delete(
            "/devices", Response, query_params=query_params, path_params=path_params
        )

    def list_devices(
        self, user_id: Optional[str] = None
    ) -> StreamResponse[ListDevicesResponse]:
        """
        List devices
        """
        query_params = {}
        path_params = {}
        query_params["user_id"] = user_id

        self.get(
            "/devices",
            ListDevicesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_device(self, data: CreateDeviceRequest) -> StreamResponse[Response]:
        """
        Create device
        """
        query_params = {}
        path_params = {}

        self.post(
            "/devices",
            Response,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def get_edges(self) -> StreamResponse[GetEdgesResponse]:
        """
        Get Edges
        """
        query_params = {}
        path_params = {}

        self.get(
            "/edges",
            GetEdgesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def create_guest(
        self, data: CreateGuestRequest
    ) -> StreamResponse[CreateGuestResponse]:
        """
        Create Guest
        """
        query_params = {}
        path_params = {}

        self.post(
            "/guest",
            CreateGuestResponse,
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )

    def video_connect(self, data: WsauthMessageRequest):
        """
        Video Connect (WebSocket)
        """
        query_params = {}
        path_params = {}

        self.get(
            "/video/connect",
            query_params=query_params,
            path_params=path_params,
            json=asdict(data),
        )