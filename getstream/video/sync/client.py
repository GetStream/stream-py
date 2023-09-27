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

    def call(self, type: str, id: str):
        """
        Returns a Call instance
        :param type: A string representing the call type
        :param id: A string representing the call id
        :return: A Call instance
        """
        return Call(client=self, type=type, id=id)

    def query_members(
        self, data: QueryMembersRequest
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Query call members
        """
        query_params = {}
        path_params = {}

        return self.post(
            "/call/members",
            QueryMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.get(
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

        return self.patch(
            "/call/{type}/{id}",
            UpdateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}",
            GetOrCreateCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def accept_call(self, type: str, id: str) -> StreamResponse[AcceptCallResponse]:
        """
        Accept Call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        return self.post(
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

        return self.post(
            "/call/{type}/{id}/block",
            BlockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/event",
            SendEventResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/go_live",
            GoLiveResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/join",
            JoinCallResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def end_call(self, type: str, id: str) -> StreamResponse[EndCallResponse]:
        """
        End call
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id

        return self.post(
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

        return self.post(
            "/call/{type}/{id}/members",
            UpdateCallMembersResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/mute_users",
            MuteUsersResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/pin",
            PinResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/reaction",
            SendReactionResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def list_recordings(
        self, type: str, id: str, session: Optional[str] = None
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        List recordings (type, id)
        """
        query_params = {}
        path_params = {}
        path_params["type"] = type
        path_params["id"] = id
        path_params["session"] = session

        path = "/call/{type}/{id}/recordings"
        if session is not None:
            path = "/call/{type}/{id}/{session}/recordings"

        return self.get(
            path,
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

        return self.post(
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

        return self.post(
            "/call/{type}/{id}/request_permission",
            RequestPermissionResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
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

        return self.post(
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

        return self.post(
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

        return self.post(
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

        return self.post(
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

        return self.post(
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

        return self.post(
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

        return self.post(
            "/call/{type}/{id}/unblock",
            UnblockUserResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/unpin",
            UnpinResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/call/{type}/{id}/user_permissions",
            UpdateUserPermissionsResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.post(
            "/calls",
            QueryCallsResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def list_call_types(self) -> StreamResponse[ListCallTypeResponse]:
        """
        List Call Type
        """
        query_params = {}
        path_params = {}

        return self.get(
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

        return self.post(
            "/calltypes",
            CreateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def delete_call_type(self, name: str) -> StreamResponse[Response]:
        """
        Delete Call Type
        """
        query_params = {}
        path_params = {}
        path_params["name"] = name

        return self.delete(
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

        return self.get(
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

        return self.put(
            "/calltypes/{name}",
            UpdateCallTypeResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
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

        return self.delete(
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

        return self.get(
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

        return self.post(
            "/devices",
            Response,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def get_edges(self) -> StreamResponse[GetEdgesResponse]:
        """
        Get Edges
        """
        query_params = {}
        path_params = {}

        return self.get(
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

        return self.post(
            "/guest",
            CreateGuestResponse,
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )

    def video_connect(self, data: WsauthMessageRequest):
        """
        Video Connect (WebSocket)
        """
        query_params = {}
        path_params = {}

        return self.get(
            "/video/connect",
            query_params=query_params,
            path_params=path_params,
            json=data.to_dict(),
        )


class Call:
    def __init__(self, client: VideoClient, call_type: str, call_id: str):
        """
        Initializes Call with VideoClient instance
        :param client: An instance of VideoClient class
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        """
        self._client = client
        self._call_type = call_type
        self._call_id = call_id

    def create(
        self, data: GetOrCreateCallRequest
    ) -> StreamResponse[GetOrCreateCallResponse]:
        """
        Creates a call with given data and members
        :param data: A dictionary with call details
        :param members: A list of members to be included in the call
        :return: Response from the create call API
        """
        return self._client.get_or_create_call(self._call_type, self._call_id, data)

    def get(self) -> StreamResponse[GetCallResponse]:
        """
        Retrieves the call based on call type and id
        :return: Response from the get call API
        """
        return self._client.get_call(self._call_type, self._call_id)

    def update(self, data: UpdateCallRequest) -> StreamResponse[UpdateCallResponse]:
        """
        Updates the call with given data
        :param data: A dictionary with updated call details
        :return: Response from the update call API
        """
        return self._client.update_call(self._call_type, self._call_id, data)

    def create_guest(
        self, data: CreateGuestRequest
    ) -> StreamResponse[CreateGuestResponse]:
        """
        Creates a guest with given data
        :param data: A dictionary with guest details
        :return: Response from the create guest API
        """
        return self._client.create_guest(self._call_type, self._call_id, data)

    def query_calls(
        self, data: QueryCallsRequest
    ) -> StreamResponse[QueryCallsResponse]:
        """
        Executes a query to retrieve calls
        :param data: A dictionary with query details
        :return: Response from the query calls API
        """
        return self._client.query_calls(self._call_type, self._call_id, data)

    def send_event(self, data: SendEventRequest) -> StreamResponse[SendEventResponse]:
        """
        Sends a custom event for the call
        :param data: A dictionary with event details
        :return: Response from the send custom event API
        """
        return self._client.send_event(self._call_type, self._call_id, data)

    def update_user_permissions(
        self, data: UpdateUserPermissionsRequest
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Updates permissions of the user in the call
        :param data: A dictionary with permission details
        :return: Response from the update user permissions API
        """
        return self._client.update_user_permissions(
            self._call_type, self._call_id, data
        )

    def pin(self, data: PinRequest) -> StreamResponse[PinResponse]:
        """
        Pins the call
        :param data: A dictionary with pin details
        :return: Response from the pin call API
        """
        return self._client.video_pin(self._call_type, self._call_id, data)

    def accept_call(self) -> StreamResponse[AcceptCallResponse]:
        """
        Accepts the call
        :param data: A dictionary with call details
        :return: Response from the accept call API
        """
        return self._client.accept_call(self._call_type, self._call_id)

    def list_devices(self) -> StreamResponse[ListDevicesResponse]:
        """
        Lists devices
        :return: Response from the list devices API
        """
        return self._client.list_devices(self._call_type, self._call_id)

    def create_device(self, data: CreateDeviceRequest) -> StreamResponse[Response]:
        """
        Creates device
        :param data: A dictionary with device details
        :return: Response from the create device API
        """
        return self._client.create_device(self._call_type, self._call_id, data)

    def unpin(self, data: UnpinRequest) -> StreamResponse[UnpinResponse]:
        """
        Unpins the call
        :param data: A dictionary with unpin details
        :return: Response from the unpin call API
        """
        return self._client.video_unpin(self._call_type, self._call_id, data)

    def reject_call(self) -> StreamResponse[RejectCallResponse]:
        """
        Rejects the call
        :param data: A dictionary with call details
        :return: Response from the reject call API
        """
        return self._client.reject_call(self._call_type, self._call_id)

    def go_live(self, data: GoLiveRequest) -> StreamResponse[GoLiveResponse]:
        """
        Makes the call go live
        :param data: A dictionary with call details
        :return: Response from the go live API
        """
        return self._client.go_live(self._call_type, self._call_id, data)

    def update_call_members(
        self, data: UpdateCallMembersRequest
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Updates members of the call
        :param members: A list of new members to be included in the call
        :return: Response from the update call members API
        """
        return self._client.update_call_members(self._call_type, self._call_id, data)

    def unblock_user(
        self, data: UnblockUserRequest
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks user from the call
        :param data: A dictionary with user details
        :return: Response from the unblock user API
        """
        return self._client.unblock_user(self._call_type, self._call_id, data)

    def stop_live(self) -> StreamResponse[StopLiveResponse]:
        """
        Stops live call
        :return: Response from the stop live API
        """
        return self._client.stop_live(self._call_type, self._call_id)

    def list_recordings(
        self, session_id: str = None
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        Executes a query to retrieve recordings of the call
        :param session_id: A string representing a unique session identifier
        :return: Response from the query recordings API
        """
        return self._client.list_recordings(self._call_type, self._call_id, session_id)

    #  we don't have delete recording yet
    # def delete_recording(
    #     self, session_id: str, recording_id: str
    # ) -> StreamResponse[Response]:
    #     """
    #     Deletes specific recording of the call
    #     :param session_id: A string representing a unique session identifier
    #     :param recording_id: A string representing a unique recording identifier
    #     :return: Response from the delete recording API
    #     """
    #     return self._client.delete_recording(
    #         self._call_type, self._call_id, session_id, recording_id
    #     )

    def mute_users(self, data: MuteUsersRequest) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users in the call
        :param data: A dictionary with user details
        :return: Response from the mute users API
        """
        return self._client.mute_users(self._call_type, self._call_id, data)

    def query_members(
        self, data: QueryMembersRequest
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Executes a query to retrieve members of the call
        :param data: A dictionary with query details
        :return: Response from the query members API
        """
        return self._client.query_members(self._call_type, self._call_id, data)

    def request_permission(
        self, data: RequestPermissionRequest
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Requests permissions for the call
        :param data: A dictionary with permission details
        :return: Response from the request permissions API
        """
        return self._client.request_permission(self._call_type, self._call_id, data)

    def send_event(self, data) -> StreamResponse[SendEventResponse]:
        """
        Sends a custom event for the call
        :param data: A dictionary with event details
        :return: Response from the send custom event API
        """
        return self._client.send_event(self._call_type, self._call_id, data)

    def send_video_reaction(
        self, data: SendReactionRequest
    ) -> StreamResponse[SendReactionResponse]:
        """
        Sends a reaction for the call
        :param data: A dictionary with reaction details
        :return: Response from the send
        """
        return self._client.send_video_reaction(self._call_type, self._call_id, data)

    def start_recording(self) -> StreamResponse[StartRecordingResponse]:
        """
        Starts recording for the call
        :return: Response from the start recording API
        """
        return self._client.start_recording(self._call_type, self._call_id)

    def start_transcription(self) -> StreamResponse[StartTranscriptionResponse]:
        """
        Starts transcription for the call
        :return: Response from the start transcription API
        """
        return self._client.start_transcription(self._call_type, self._call_id)

    def start_broadcasting(self) -> StreamResponse[StartBroadcastingResponse]:
        """
        Starts broadcasting for the call
        :return: Response from the start broadcasting API
        """
        return self._client.start_broadcasting(self._call_type, self._call_id)

    def stop_recording(self) -> StreamResponse[StopRecordingResponse]:
        """
        Stops recording for the call
        :return: Response from the stop recording API
        """
        return self._client.stop_recording(self._call_type, self._call_id)

    def stop_transcription(self) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stops transcription for the call
        :return: Response from the stop transcription API
        """
        return self._client.stop_transcription(self._call_type, self._call_id)

    def stop_broadcasting(self) -> StreamResponse[StopBroadcastingResponse]:
        """
        Stops broadcasting for the call
        :return: Response from the stop broadcasting API
        """
        return self._client.stop_broadcasting(self._call_type, self._call_id)

    def block_user(self, data: BlockUserRequest) -> StreamResponse[BlockUserResponse]:
        """
        Blocks user in the call
        :param data: A dictionary with user details
        :return: Response from the block user API
        """
        return self._client.block_user(self._call_type, self._call_id, data)

    def end_call(self) -> StreamResponse[EndCallResponse]:
        """
        Ends the call
        :return: Response from the end call API
        """
        return self._client.end_call(self._call_type, self._call_id)

    def go_live(self) -> StreamResponse[GoLiveResponse]:
        """
        Makes the call go live
        :return: Response from the go live API
        """
        return self._client.go_live(self._call_type, self._call_id)

    def join(self, data: JoinCallRequest) -> StreamResponse[JoinCallResponse]:
        """
        Joins the call
        :param data: A dictionary with user details
        :return: Response from the join call API
        """
        return self._client.join_call(self._call_type, self._call_id, data)
