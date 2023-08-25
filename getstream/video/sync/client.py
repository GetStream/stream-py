from typing import List
from dataclasses import asdict
from getstream.models.model_block_user_request import BlockUserRequest
from getstream.models.model_block_user_response import BlockUserResponse
from getstream.models.model_call_request import CallRequest
from getstream.models.model_create_call_type_request import CreateCallTypeRequest
from getstream.models.model_create_call_type_response import CreateCallTypeResponse
from getstream.models.model_custom_video_event import CustomVideoEvent
from getstream.models.model_end_call_response import EndCallResponse
from getstream.models.model_get_call_response import GetCallResponse
from getstream.models.model_get_call_type_response import GetCallTypeResponse
from getstream.models.model_get_edges_response import GetEdgesResponse
from getstream.models.model_get_or_create_call_response import GetOrCreateCallResponse
from getstream.models.model_go_live_response import GoLiveResponse
from getstream.models.model_join_call_request import JoinCallRequest
from getstream.models.model_join_call_response import JoinCallResponse
from getstream.models.model_list_call_type_response import ListCallTypeResponse
from getstream.models.model_list_devices_response import ListDevicesResponse
from getstream.models.model_list_recordings_response import ListRecordingsResponse
from getstream.models.model_member_request import MemberRequest
from getstream.models.model_mute_users_request import MuteUsersRequest
from getstream.models.model_mute_users_response import MuteUsersResponse
from getstream.models.model_query_calls_request import QueryCallsRequest
from getstream.models.model_query_calls_response import QueryCallsResponse
from getstream.models.model_query_members_request import QueryMembersRequest
from getstream.models.model_query_members_response import QueryMembersResponse
from getstream.models.model_request_permission_request import RequestPermissionRequest
from getstream.models.model_request_permission_response import RequestPermissionResponse
from getstream.models.model_send_reaction_request import SendReactionRequest
from getstream.models.model_send_reaction_response import SendReactionResponse
from getstream.models.model_start_broadcasting_response import StartBroadcastingResponse
from getstream.models.model_start_recording_response import StartRecordingResponse
from getstream.models.model_start_transcription_response import (
    StartTranscriptionResponse,
)
from getstream.models.model_stop_broadcasting_response import StopBroadcastingResponse
from getstream.models.model_stop_live_response import StopLiveResponse
from getstream.models.model_stop_recording_response import StopRecordingResponse
from getstream.models.model_stop_transcription_response import StopTranscriptionResponse
from getstream.models.model_unblock_user_request import UnblockUserRequest
from getstream.models.model_unblock_user_response import UnblockUserResponse
from getstream.models.model_update_call_members_response import (
    UpdateCallMembersResponse,
)
from getstream.models.model_update_call_request import UpdateCallRequest
from getstream.models.model_update_call_response import UpdateCallResponse
from getstream.models.model_update_call_type_request import UpdateCallTypeRequest
from getstream.models.model_update_call_type_response import UpdateCallTypeResponse
from getstream.models.model_update_user_permissions_request import (
    UpdateUserPermissionsRequest,
)
from getstream.models.model_update_user_permissions_response import (
    UpdateUserPermissionsResponse,
)
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

    def call(self, call_type: str, call_id: str):
        """
        Returns instance of Call class
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: Instance of Call class
        """
        return Call(self, call_type, call_id)

    def edges(self) -> StreamResponse[GetEdgesResponse]:
        """
        Retrieves edges from the server
        :return: json object with response
        """
        response = self.get("/edges", GetEdgesResponse)

        return response

    def get_edge_server(self, call_type: str, call_id: str, data) -> StreamResponse:
        """
        Retrieves specific edge server
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.get(
            f"/calls/{call_type}/{call_id}/get_edge_server", json=asdict(data)
        )
        return response

    def create_call_type(
        self, data: CreateCallTypeRequest
    ) -> StreamResponse[CreateCallTypeResponse]:
        """
        Creates a new call type
        :param data: A dictionary with details about the call type
        :return: json object with response
        """
        response = self.post("/calltypes", CreateCallTypeResponse, json=asdict(data))
        return response

    def get_call_type(self, name: str) -> StreamResponse[GetCallTypeResponse]:
        """
        Retrieves specific call type
        :param name: A string representing the name of the call type
        :return: json object with response
        """
        response = self.get(f"/calltypes/{name}", GetCallTypeResponse)
        return response

    def list_call_types(self) -> StreamResponse[ListCallTypeResponse]:
        """
        Returns a list with all call types of the client
        :return: json object with response
        """
        response = self.get("/calltypes", ListCallTypeResponse)
        return response

    def update_call_type(
        self, name: str, data: UpdateCallTypeRequest
    ) -> StreamResponse[UpdateCallTypeResponse]:
        """
        Updates specific call type
        :param name: A string representing the name of the call type
        :param data: A dictionary with details about the call type
        :return: json object with response
        """
        response = self.put(
            f"/calltypes/{name}", UpdateCallTypeResponse, json=asdict(data)
        )
        return response

    def query_calls(
        self, data: QueryCallsRequest
    ) -> StreamResponse[QueryCallsResponse]:
        """
        Executes a query about specific call
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        response = self.post("/calls", QueryCallsResponse, json=asdict(data))

        return response

    def block_user(
        self, call_type: str, call_id: str, data: BlockUserRequest
    ) -> StreamResponse[BlockUserResponse]:
        """
        Blocks user in the call
        :param data: A dictionary with user details
        :return: Response from the block user API
        """
        path = f"/call/{call_type}/{call_id}/block"
        response = self.post(path, BlockUserResponse, json=asdict(data))

        return response

    def end_call(self, call_type: str, call_id: str) -> StreamResponse[EndCallResponse]:
        """
        Ends the call
        :return: Response from the end call API
        """
        path = f"/call/{call_type}/{call_id}/mark_ended"
        response = self.post(path, BlockUserResponse)

        return response

    def get_call(self, call_type: str, call_id: str) -> StreamResponse[GetCallResponse]:
        """
        Retrieves specific call type
        :param name: A string representing the name of the call type
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}"
        response = self.get(path, GetCallResponse)

        return response

    def go_live(self, call_type: str, call_id: str) -> StreamResponse[GoLiveResponse]:
        """
        Makes specific call go live
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/go_live"
        response = self.post(path, GoLiveResponse)

        return response

    def join_call(
        self, call_type: str, call_id: str, data: JoinCallRequest
    ) -> StreamResponse[JoinCallResponse]:
        """
        Joins specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/join"
        response = self.post(path, JoinCallResponse, data=asdict(data))

        return response

    def delete_call_type(self, name: str) -> StreamResponse:
        """
        Deletes specific call type
        :param name: A string representing the name of the call type
        :return: json object with response
        """
        response = self.delete(f"/calltypes/{name}")
        return response

    def delete_recording(
        self, call_type: str, call_id: str, session_id: str, recording_id: str
    ) -> StreamResponse:
        """
        Deletes specific recording of the call
        :param session_id: A string representing a unique session identifier
        :param recording_id: A string representing a unique recording identifier
        :return: Response from the delete recording API
        """
        path = f"/call/{call_type}/{call_id}/{session_id}/recordings/{recording_id}"
        response = self.delete(path)
        return response

    def add_device(
        self, id, push_provider, push_provider_name=None, user_id=None, voip_token=None
    ) -> StreamResponse:
        """
        Adds device to the client
        :param id: A string representing device identifier
        :param push_provider: An instance representing the push provider
        :param push_provider_name: A string representing the name of the push provider
        :param user_id: A string representing a unique user identifier
        :param voip_token: A string representing the Voice Over IP token
        :return: json object with response
        """
        data = {"id": id, "push_provider": push_provider, "voip_token": voip_token}
        if user_id is not None:
            data.update({"user_id": user_id})
        if push_provider_name is not None:
            data.update({"push_provider_name": push_provider_name})
        response = self.post("/devices", json=asdict(data))
        return response

    def add_voip_device(
        self, id, push_provider, push_provider_name=None, user_id=None
    ) -> StreamResponse:
        """
        Adds Voice Over IP device to the client
        :param id: A string representing device identifier
        :param push_provider: An instance representing the push provider
        :param push_provider_name: A string representing the name of the push provider
        :param user_id: A string representing a unique user identifier
        """
        return self.add_device(
            id, push_provider, push_provider_name, user_id, voip_token=True
        )

    def get_devices(self) -> StreamResponse[ListDevicesResponse]:
        """
        Retrieves all devices of the client
        :return: json object with response
        """
        response = self.get("/devices", ListDevicesResponse)
        return response

    def remove_device(self, data) -> StreamResponse:
        """
        Removes specific device from the client
        :param data: A dictionary with additional details about the device
        :return: json object with response
        """
        response = self.delete("/devices", json=asdict(data))
        return response

    def query_recordings(
        self, call_type: str, call_id: str, session_id: str = None
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        Executes a query to retrieve specific call recordings
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param session_id: A string representing a unique session identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/recordings"
        if session_id is None:
            path = f"/call/{call_type}/{call_id}/{session_id}/recordings"
        response = self.get(path, ListRecordingsResponse)
        return response

    def mute_users(
        self, call_type: str, call_id: str, data: MuteUsersRequest
    ) -> StreamResponse[MuteUsersResponse]:
        """
        Mute users in a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/mute_users"
        response = self.post(path, MuteUsersResponse, data=data)
        return response

    def query_members(
        self, call_type: str, call_id: str, data: QueryMembersRequest
    ) -> StreamResponse[QueryMembersResponse]:
        """
        Executes a query to retrieve specific call members
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/members"
        response = self.post(path, QueryMembersResponse, json=asdict(data))
        return response

    def request_permissions(
        self, call_type: str, call_id: str, data: RequestPermissionRequest
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Requests permissions for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/request_permission"
        response = self.post(path, RequestPermissionResponse, json=asdict(data))
        return response

    def send_custom_event(
        self, call_type: str, call_id: str, data
    ) -> StreamResponse[CustomVideoEvent]:
        """
        Sends a custom event for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/event"
        response = self.post(path, CustomVideoEvent, json=asdict(data))
        return response

    def send_reaction(
        self, call_type: str, call_id: str, data: SendReactionRequest
    ) -> StreamResponse[SendReactionResponse]:
        """
        Sends a reaction for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/reaction"
        response = self.post(path, SendReactionResponse, json=asdict(data))
        return response

    def start_recording(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StartRecordingResponse]:
        """
        Starts recording for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/start_recording"
        response = self.post(path, StartRecordingResponse)
        return response

    def start_trancription(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StartTranscriptionResponse]:
        """
        Starts transcription for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/start_transcription"
        response = self.post(path, StartTranscriptionResponse)
        return response

    def start_broadcasting(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StartBroadcastingResponse]:
        """
        Starts broadcasting for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/start_broadcasting"
        response = self.post(path, StartBroadcastingResponse)

        return response

    def stop_recording(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StopRecordingResponse]:
        """
        Stops recording for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/stop_recording"
        response = self.post(path, StopRecordingResponse)

        return response

    def stop_transcription(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StopTranscriptionResponse]:
        """
        Stops transcription for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/stop_transcription"
        response = self.post(path, StopTranscriptionResponse)

        return response

    def stop_broadcasting(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StopBroadcastingResponse]:
        """
        Stops broadcasting for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/stop_broadcasting"
        response = self.post(path, StopBroadcastingResponse)

        return response

    def stop_live(
        self, call_type: str, call_id: str
    ) -> StreamResponse[StopLiveResponse]:
        """
        Stops the live status of a call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/stop_live"
        response = self.post(path, StopLiveResponse)

        return response

    def unblock_user(
        self, call_type: str, call_id: str, data: UnblockUserRequest
    ) -> StreamResponse[UnblockUserResponse]:
        """
        Unblocks a user from a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/unblock"
        response = self.post(path, UnblockUserResponse, json=asdict(data))

        return response

    def update_call_members(
        self, call_type: str, call_id: str, members: List[MemberRequest] = None
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Updates the members of a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param members: A list with the members' details
        :return: json object with response
        """
        data = {"update_members": members}
        path = f"/call/{call_type}/{call_id}/members"
        response = self.put(path, UpdateCallMembersResponse, json=asdict(data))

        return response

    def update_call(
        self, call_type: str, call_id: str, data
    ) -> StreamResponse[UpdateCallResponse]:
        """
        Updates a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        request_data = {"data": data}
        path = f"/call/{call_type}/{call_id}"
        response = self.put(path, UpdateCallResponse, json=request_data)

        return response

    def update_user_permissions(
        self, call_type: str, call_id: str, data: UpdateUserPermissionsRequest
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        """
        Updates user permissions for a specific call
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :return: json object with response
        """
        path = f"/call/{call_type}/{call_id}/permissions"
        response = self.put(path, UpdateUserPermissionsResponse, json=asdict(data))

        return response

    def get_or_create_call(
        self,
        call_type: str,
        call_id: str,
        data: CallRequest,
        members: List[MemberRequest] = None,
    ) -> StreamResponse[GetOrCreateCallResponse]:
        """
        Returns a specific call and creates one if it does not exist
        :param call_type: A string representing the call type
        :param call_id: A string representing a unique call identifier
        :param data: A dictionary with additional call details
        :param members: A list with the call members' details
        :return: json object with response
        """
        request_data = {"data": asdict(data)}
        if members is not None:
            request_data.update({"members": [asdict(member) for member in members]})
        path = f"/call/{call_type}/{call_id}"
        response = self.post(path, GetOrCreateCallResponse, json=request_data)

        return response


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
        self, data: CallRequest, members: List[MemberRequest] = None
    ) -> StreamResponse[GetOrCreateCallResponse]:
        """
        Creates a call with given data and members
        :param data: A dictionary with call details
        :param members: A list of members to be included in the call
        :return: Response from the create call API
        """
        return self._client.get_or_create_call(
            self._call_type, self._call_id, data, members
        )

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

    def update_call_members(
        self, members: List[MemberRequest] = None
    ) -> StreamResponse[UpdateCallMembersResponse]:
        """
        Updates members of the call
        :param members: A list of new members to be included in the call
        :return: Response from the update call members API
        """
        return self._client.update_call_members(self._call_type, self._call_id, members)

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

    def query_recordings(
        self, session_id: str = None
    ) -> StreamResponse[ListRecordingsResponse]:
        """
        Executes a query to retrieve recordings of the call
        :param session_id: A string representing a unique session identifier
        :return: Response from the query recordings API
        """
        return self._client.query_recordings(self._call_type, self._call_id, session_id)

    def delete_recording(self, session_id: str, recording_id: str) -> StreamResponse:
        """
        Deletes specific recording of the call
        :param session_id: A string representing a unique session identifier
        :param recording_id: A string representing a unique recording identifier
        :return: Response from the delete recording API
        """
        return self._client.delete_recording(
            self._call_type, self._call_id, session_id, recording_id
        )

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

    def request_permissions(
        self, data: RequestPermissionRequest
    ) -> StreamResponse[RequestPermissionResponse]:
        """
        Requests permissions for the call
        :param data: A dictionary with permission details
        :return: Response from the request permissions API
        """
        return self._client.request_permissions(self._call_type, self._call_id, data)

    def send_custom_event(self, data) -> StreamResponse[CustomVideoEvent]:
        """
        Sends a custom event for the call
        :param data: A dictionary with event details
        :return: Response from the send custom event API
        """
        return self._client.send_custom_event(self._call_type, self._call_id, data)

    def send_reaction(
        self, data: SendReactionRequest
    ) -> StreamResponse[SendReactionResponse]:
        """
        Sends a reaction for the call
        :param data: A dictionary with reaction details
        :return: Response from the send
        """
        return self._client.send_reaction(self._call_type, self._call_id, data)

    def start_recording(self) -> StreamResponse[StartRecordingResponse]:
        """
        Starts recording for the call
        :return: Response from the start recording API
        """
        return self._client.start_recording(self._call_type, self._call_id)

    def start_trancription(self) -> StreamResponse[StartTranscriptionResponse]:
        """
        Starts transcription for the call
        :return: Response from the start transcription API
        """
        return self._client.start_trancription(self._call_type, self._call_id)

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
