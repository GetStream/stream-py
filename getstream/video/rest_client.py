from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import encode_query_param, request_to_dict


class VideoRestClient(BaseClient):

    def __init__(self, api_key: str, base_url: str, timeout: float, token: str):
        """
        Initializes VideoClient with BaseClient instance
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
    
    def query_call_members(self, query_call_members_request: QueryCallMembersRequest=None) -> StreamResponse[QueryCallMembersResponse]:
        return self.post("/api/v2/video/call/members", QueryCallMembersResponse, json=request_to_dict(query_call_members_request))
    
    def query_call_stats(self, query_call_stats_request: QueryCallStatsRequest=None) -> StreamResponse[QueryCallStatsResponse]:
        return self.post("/api/v2/video/call/stats", QueryCallStatsResponse, json=request_to_dict(query_call_stats_request))
    
    def get_call(self, type: str, id: str, connection_id: Optional[str]=None, members_limit: Optional[int]=None, ring: Optional[bool]=None, notify: Optional[bool]=None) -> StreamResponse[GetCallResponse]:
        query_params = {
            "connection_id": encode_query_param(connection_id), "members_limit": encode_query_param(members_limit), "ring": encode_query_param(ring), "notify": encode_query_param(notify), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.get("/api/v2/video/call/{type}/{id}", GetCallResponse, query_params=query_params, path_params=path_params)
    
    def update_call(self, type: str, id: str, update_call_request: UpdateCallRequest=None) -> StreamResponse[UpdateCallResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.patch("/api/v2/video/call/{type}/{id}", UpdateCallResponse, path_params=path_params, json=request_to_dict(update_call_request))
    
    def get_or_create_call(self, type: str, id: str, connection_id: Optional[str]=None, get_or_create_call_request: GetOrCreateCallRequest=None) -> StreamResponse[GetOrCreateCallResponse]:
        query_params = {
            "connection_id": encode_query_param(connection_id), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}", GetOrCreateCallResponse, query_params=query_params, path_params=path_params, json=request_to_dict(get_or_create_call_request))
    
    def block_user(self, type: str, id: str, block_user_request: BlockUserRequest=None) -> StreamResponse[BlockUserResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/block", BlockUserResponse, path_params=path_params, json=request_to_dict(block_user_request))
    
    def send_call_event(self, type: str, id: str, send_event_request: SendEventRequest=None) -> StreamResponse[SendEventResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/event", SendEventResponse, path_params=path_params, json=request_to_dict(send_event_request))
    
    def collect_user_feedback(self, type: str, id: str, session: str, collect_user_feedback_request: CollectUserFeedbackRequest=None) -> StreamResponse[CollectUserFeedbackResponse]:
        path_params = {
            "type": type, "id": id, "session": session, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/feedback/{session}", CollectUserFeedbackResponse, path_params=path_params, json=request_to_dict(collect_user_feedback_request))
    
    def go_live(self, type: str, id: str, go_live_request: GoLiveRequest=None) -> StreamResponse[GoLiveResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/go_live", GoLiveResponse, path_params=path_params, json=request_to_dict(go_live_request))
    
    def end_call(self, type: str, id: str) -> StreamResponse[EndCallResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/mark_ended", EndCallResponse, path_params=path_params)
    
    def update_call_members(self, type: str, id: str, update_call_members_request: UpdateCallMembersRequest=None) -> StreamResponse[UpdateCallMembersResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/members", UpdateCallMembersResponse, path_params=path_params, json=request_to_dict(update_call_members_request))
    
    def mute_users(self, type: str, id: str, mute_users_request: MuteUsersRequest=None) -> StreamResponse[MuteUsersResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/mute_users", MuteUsersResponse, path_params=path_params, json=request_to_dict(mute_users_request))
    
    def video_pin(self, type: str, id: str, pin_request: PinRequest=None) -> StreamResponse[PinResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/pin", PinResponse, path_params=path_params, json=request_to_dict(pin_request))
    
    def list_recordings(self, type: str, id: str) -> StreamResponse[ListRecordingsResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.get("/api/v2/video/call/{type}/{id}/recordings", ListRecordingsResponse, path_params=path_params)
    
    def start_hls_broadcasting(self, type: str, id: str) -> StreamResponse[StartHLSBroadcastingResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/start_broadcasting", StartHLSBroadcastingResponse, path_params=path_params)
    
    def start_recording(self, type: str, id: str, start_recording_request: StartRecordingRequest=None) -> StreamResponse[StartRecordingResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/start_recording", StartRecordingResponse, path_params=path_params, json=request_to_dict(start_recording_request))
    
    def start_transcription(self, type: str, id: str, start_transcription_request: StartTranscriptionRequest=None) -> StreamResponse[StartTranscriptionResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/start_transcription", StartTranscriptionResponse, path_params=path_params, json=request_to_dict(start_transcription_request))
    
    def get_call_stats(self, type: str, id: str, session: str) -> StreamResponse[GetCallStatsResponse]:
        path_params = {
            "type": type, "id": id, "session": session, 
        }
        return self.get("/api/v2/video/call/{type}/{id}/stats/{session}", GetCallStatsResponse, path_params=path_params)
    
    def stop_hls_broadcasting(self, type: str, id: str) -> StreamResponse[StopHLSBroadcastingResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/stop_broadcasting", StopHLSBroadcastingResponse, path_params=path_params)
    
    def stop_live(self, type: str, id: str) -> StreamResponse[StopLiveResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/stop_live", StopLiveResponse, path_params=path_params)
    
    def stop_recording(self, type: str, id: str) -> StreamResponse[StopRecordingResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/stop_recording", StopRecordingResponse, path_params=path_params)
    
    def stop_transcription(self, type: str, id: str) -> StreamResponse[StopTranscriptionResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/stop_transcription", StopTranscriptionResponse, path_params=path_params)
    
    def list_transcriptions(self, type: str, id: str) -> StreamResponse[ListTranscriptionsResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.get("/api/v2/video/call/{type}/{id}/transcriptions", ListTranscriptionsResponse, path_params=path_params)
    
    def unblock_user(self, type: str, id: str, unblock_user_request: UnblockUserRequest=None) -> StreamResponse[UnblockUserResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/unblock", UnblockUserResponse, path_params=path_params, json=request_to_dict(unblock_user_request))
    
    def video_unpin(self, type: str, id: str, unpin_request: UnpinRequest=None) -> StreamResponse[UnpinResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/unpin", UnpinResponse, path_params=path_params, json=request_to_dict(unpin_request))
    
    def update_user_permissions(self, type: str, id: str, update_user_permissions_request: UpdateUserPermissionsRequest=None) -> StreamResponse[UpdateUserPermissionsResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/video/call/{type}/{id}/user_permissions", UpdateUserPermissionsResponse, path_params=path_params, json=request_to_dict(update_user_permissions_request))
    
    def query_calls(self, connection_id: Optional[str]=None, query_calls_request: QueryCallsRequest=None) -> StreamResponse[QueryCallsResponse]:
        query_params = {
            "connection_id": encode_query_param(connection_id), 
        }
        return self.post("/api/v2/video/calls", QueryCallsResponse, query_params=query_params, json=request_to_dict(query_calls_request))
    
    def list_call_types(self) -> StreamResponse[ListCallTypeResponse]:
        return self.get("/api/v2/video/calltypes", ListCallTypeResponse)
    
    def create_call_type(self, create_call_type_request: CreateCallTypeRequest=None) -> StreamResponse[CreateCallTypeResponse]:
        return self.post("/api/v2/video/calltypes", CreateCallTypeResponse, json=request_to_dict(create_call_type_request))
    
    def delete_call_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name, 
        }
        return self.delete("/api/v2/video/calltypes/{name}", Response, path_params=path_params)
    
    def get_call_type(self, name: str) -> StreamResponse[GetCallTypeResponse]:
        path_params = {
            "name": name, 
        }
        return self.get("/api/v2/video/calltypes/{name}", GetCallTypeResponse, path_params=path_params)
    
    def update_call_type(self, name: str, update_call_type_request: UpdateCallTypeRequest=None) -> StreamResponse[UpdateCallTypeResponse]:
        path_params = {
            "name": name, 
        }
        return self.put("/api/v2/video/calltypes/{name}", UpdateCallTypeResponse, path_params=path_params, json=request_to_dict(update_call_type_request))
    
    def get_edges(self) -> StreamResponse[GetEdgesResponse]:
        return self.get("/api/v2/video/edges", GetEdgesResponse)
    
    def list_external_storage(self) -> StreamResponse[ListExternalStorageResponse]:
        return self.get("/api/v2/video/external_storage", ListExternalStorageResponse)
    
    def create_external_storage(self, create_external_storage_request: CreateExternalStorageRequest=None) -> StreamResponse[CreateExternalStorageResponse]:
        return self.post("/api/v2/video/external_storage", CreateExternalStorageResponse, json=request_to_dict(create_external_storage_request))
    
    def delete_external_storage(self, name: str) -> StreamResponse[DeleteExternalStorageResponse]:
        path_params = {
            "name": name, 
        }
        return self.delete("/api/v2/video/external_storage/{name}", DeleteExternalStorageResponse, path_params=path_params)
    
    def update_external_storage(self, name: str, update_external_storage_request: UpdateExternalStorageRequest=None) -> StreamResponse[UpdateExternalStorageResponse]:
        path_params = {
            "name": name, 
        }
        return self.put("/api/v2/video/external_storage/{name}", UpdateExternalStorageResponse, path_params=path_params, json=request_to_dict(update_external_storage_request))
    
    def check_external_storage(self, name: str) -> StreamResponse[CheckExternalStorageResponse]:
        path_params = {
            "name": name, 
        }
        return self.get("/api/v2/video/external_storage/{name}/check", CheckExternalStorageResponse, path_params=path_params)
    