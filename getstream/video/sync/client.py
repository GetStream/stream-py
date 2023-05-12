from getstream.model.block_user_request import BlockUserRequest
from getstream.model.block_user_response import BlockUserResponse
from getstream.model.create_call_type_request import CreateCallTypeRequest
from getstream.model.create_call_type_response import CreateCallTypeResponse
from getstream.model.end_call_response import EndCallResponse
from getstream.model.get_call_edge_server_request import GetCallEdgeServerRequest
from getstream.model.get_call_edge_server_response import GetCallEdgeServerResponse
from getstream.model.get_call_response import GetCallResponse
from getstream.model.get_call_type_response import GetCallTypeResponse
from getstream.model.get_edges_response import GetEdgesResponse
from getstream.model.get_or_create_call_request import GetOrCreateCallRequest
from getstream.model.get_or_create_call_response import GetOrCreateCallResponse
from getstream.model.go_live_response import GoLiveResponse
from getstream.model.join_call_request import JoinCallRequest
from getstream.model.join_call_response import JoinCallResponse
from getstream.model.list_call_type_response import ListCallTypeResponse
from getstream.model.list_recordings_response import ListRecordingsResponse
from getstream.model.mute_users_request import MuteUsersRequest
from getstream.model.mute_users_response import MuteUsersResponse
from getstream.model.query_calls_request import QueryCallsRequest
from getstream.model.query_calls_response import QueryCallsResponse
from getstream.model.query_members_request import QueryMembersRequest
from getstream.model.query_members_response import QueryMembersResponse
from getstream.model.request_permission_request import RequestPermissionRequest
from getstream.model.request_permission_response import RequestPermissionResponse
from getstream.model.send_event_request import SendEventRequest
from getstream.model.send_event_response import SendEventResponse
from getstream.model.send_reaction_request import SendReactionRequest
from getstream.model.send_reaction_response import SendReactionResponse
from getstream.model.unblock_user_request import UnblockUserRequest
from getstream.model.unblock_user_response import UnblockUserResponse
from getstream.model.update_call_members_request import UpdateCallMembersRequest
from getstream.model.update_call_members_response import UpdateCallMembersResponse
from getstream.model.update_call_request import UpdateCallRequest
from getstream.model.update_call_response import UpdateCallResponse
from getstream.model.update_call_type_request import UpdateCallTypeRequest
from getstream.model.update_call_type_response import UpdateCallTypeResponse
from getstream.model.update_user_permissions_request import UpdateUserPermissionsRequest
from getstream.model.update_user_permissions_response import UpdateUserPermissionsResponse
from getstream.sync.base import BaseClient


class VideoClient(BaseClient):
    def __init__(self, api_key: str, base_url, token):
        super().__init__(api_key=api_key, base_url=base_url, token=token)

    def edges(self) -> GetEdgesResponse:
        response = self.get("/edges")
        json = response.json()
        return GetEdgesResponse(json)

    def get_edge_server(
        self, calltype: str, callid: str, data: GetCallEdgeServerRequest
    ) -> GetCallEdgeServerResponse:
        response = self.get(f"/calls/{calltype}/{callid}/get_edge_server", data=data)
        json = response.json()
        return GetEdgesResponse(json)

    def create_call_type(self, data: CreateCallTypeRequest) -> CreateCallTypeResponse:
        response = self.post("/calltypes", data=data)
        return CreateCallTypeResponse(**response.json())

    def get_call_type(self, name: str) -> GetCallTypeResponse:
        response = self.get(f"/calltypes/{name}")
        return GetCallTypeResponse(**response.json())

    def list_call_types(self) -> ListCallTypeResponse:
        response = self.get("/calltypes")
        json = response.json()
        return json
        # return ListCallTypeResponse(json)

    def update_call_type(
        self, name: str, data: UpdateCallTypeRequest
    ) -> UpdateCallTypeResponse:
        response = self.put(f"/calltypes/{name}", data=data)
        return UpdateCallTypeResponse(**response.json())

    def query_calls(self, data: QueryCallsRequest) -> QueryCallsResponse:
        response = self.post("/calls", data=data)
        return QueryCallsResponse(**response.json())

    def block_user(
        self, calltype: str, callid: str, data: BlockUserRequest
    ) -> BlockUserResponse:
        response = self.post(f"/call/{calltype}/{callid}/block", data=data)
        return BlockUserResponse(**response.json())

    def end_call(self, calltype: str, callid: str) -> EndCallResponse:
        response = self.post(f"/call/{calltype}/{callid}/mark_ended")
        return EndCallResponse(**response.json())

    def get_call(self, calltype: str, callid: str) -> GetCallResponse:
        response = self.get(f"/call/{calltype}/{callid}")
        return GetCallResponse(**response.json())

    def go_live(self, calltype: str, callid: str) -> GoLiveResponse:
        response = self.post(f"/call/{calltype}/{callid}/go_live")
        return GoLiveResponse(**response.json())

    def join_call(
        self, calltype: str, callid: str, data: JoinCallRequest
    ) -> JoinCallResponse:
        response = self.post(f"/call/{calltype}/{callid}/join", data=data)
        return JoinCallResponse(**response.json())

    def delete_recording(
        self, calltype: str, callid: str, sessionid: str, recordingid: str
    ):
        response = self.delete(
            f"/call/{calltype}/{callid}/{sessionid}/recordings/{recordingid}"
        )
        return response.json()

    def list_recordings(
        self, calltype: str, callid: str, sessionid: str
    ) -> ListRecordingsResponse:
        response = self.get(f"/call/{calltype}/{callid}/{sessionid}/recordings")
        return ListRecordingsResponse(**response.json())

    def mute_users(
        self, calltype: str, callid: str, data: MuteUsersRequest
    ) -> MuteUsersResponse:
        response = self.post(f"/call/{calltype}/{callid}/mute_users", data=data)
        return MuteUsersResponse(**response.json())

    def query_members(
        self, calltype: str, callid: str, data: QueryMembersRequest
    ) -> QueryMembersResponse:
        response = self.post(f"/call/{calltype}/{callid}/members", data=data)
        return QueryMembersResponse(**response.json())

    def request_permission(
        self, calltype: str, callid: str, data: RequestPermissionRequest
    ) -> RequestPermissionResponse:
        response = self.post(f"/call/{calltype}/{callid}/request_permission", data=data)
        return RequestPermissionResponse(**response.json())

    def send_event(
        self, calltype: str, callid: str, data: SendEventRequest
    ) -> SendEventResponse:
        response = self.post(f"/call/{calltype}/{callid}/event", data=data)
        return SendEventResponse(**response.json())

    def send_reaction(
        self, calltype: str, callid: str, data: SendReactionRequest
    ) -> SendReactionResponse:
        response = self.post(f"/call/{calltype}/{callid}/reaction", data=data)
        return SendReactionResponse(**response.json())

    def start_recording(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_recording")
        return response.json()

    def start_trancription(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_transcription")
        return response.json()

    def start_broadcasting(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/start_broadcasting")
        return response.json()

    def stop_recording(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_recording")
        return response.json()

    def stop_transcription(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_transcription")
        return response.json()

    def stop_broadcasting(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_broadcasting")
        return response.json()

    def stop_live(self, calltype: str, callid: str):
        response = self.post(f"/call/{calltype}/{callid}/stop_live")
        return response.json()

    def unblock_user(
        self, calltype: str, callid: str, data: UnblockUserRequest
    ) -> UnblockUserResponse:
        response = self.post(f"/call/{calltype}/{callid}/unblock", data=data)
        return UnblockUserResponse(**response.json())

    def update_members(
        self, calltype: str, callid: str, data: UpdateCallMembersRequest
    ) -> UpdateCallMembersResponse:
        response = self.put(f"/call/{calltype}/{callid}/members", data=data)
        return UpdateCallMembersResponse(**response.json())

    def update_call(
        self, calltype: str, callid: str, data: UpdateCallRequest
    ) -> UpdateCallResponse:
        response = self.put(f"/call/{calltype}/{callid}", data=data)
        return UpdateCallResponse(**response.json())

    def update_user_permissions(
        self, calltype: str, callid: str, data: UpdateUserPermissionsRequest
    ) -> UpdateUserPermissionsResponse:
        response = self.put(f"/call/{calltype}/{callid}/permissions", data=data)
        return UpdateUserPermissionsResponse(**response.json())

    def get_or_create_call(
        self, calltype: str, callid: str, data: GetOrCreateCallRequest
    ) -> GetOrCreateCallResponse:
        response = self.post(f"/calls/{calltype}/{callid}", data=data)
        return GetOrCreateCallResponse(**response.json())

    # def call(self, calltype: str, callid: str, data: CallRequest)->Call:
    #     self.currentCall = Call(self.stream, calltype, callid, data)
    #     return self.currentCall
