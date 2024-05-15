from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import build_query_param, build_body_dict


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

    def query_call_members(
        self,
        id: str,
        type: str,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[QueryCallMembersResponse]:
        json = build_body_dict(
            id=id,
            type=type,
            limit=limit,
            next=next,
            prev=prev,
            sort=sort,
            filter_conditions=filter_conditions,
        )

        return self.post(
            "/api/v2/video/call/members", QueryCallMembersResponse, json=json
        )

    def query_call_stats(
        self,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[QueryCallStatsResponse]:
        json = build_body_dict(
            limit=limit,
            next=next,
            prev=prev,
            sort=sort,
            filter_conditions=filter_conditions,
        )

        return self.post("/api/v2/video/call/stats", QueryCallStatsResponse, json=json)

    def get_call(
        self,
        type: str,
        id: str,
        members_limit: Optional[int] = None,
        ring: Optional[bool] = None,
        notify: Optional[bool] = None,
    ) -> StreamResponse[GetCallResponse]:
        query_params = build_query_param(
            members_limit=members_limit, ring=ring, notify=notify
        )
        path_params = {
            "type": type,
            "id": id,
        }

        return self.get(
            "/api/v2/video/call/{type}/{id}",
            GetCallResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_call(
        self,
        type: str,
        id: str,
        starts_at: Optional[datetime] = None,
        custom: Optional[Dict[str, object]] = None,
        settings_override: Optional[CallSettingsRequest] = None,
    ) -> StreamResponse[UpdateCallResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            starts_at=starts_at, custom=custom, settings_override=settings_override
        )

        return self.patch(
            "/api/v2/video/call/{type}/{id}",
            UpdateCallResponse,
            path_params=path_params,
            json=json,
        )

    def get_or_create_call(
        self,
        type: str,
        id: str,
        members_limit: Optional[int] = None,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        data: Optional[CallRequest] = None,
    ) -> StreamResponse[GetOrCreateCallResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            members_limit=members_limit, notify=notify, ring=ring, data=data
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}",
            GetOrCreateCallResponse,
            path_params=path_params,
            json=json,
        )

    def block_user(
        self, type: str, id: str, user_id: str
    ) -> StreamResponse[BlockUserResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(user_id=user_id)

        return self.post(
            "/api/v2/video/call/{type}/{id}/block",
            BlockUserResponse,
            path_params=path_params,
            json=json,
        )

    def send_call_event(
        self,
        type: str,
        id: str,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[SendCallEventResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(user_id=user_id, custom=custom, user=user)

        return self.post(
            "/api/v2/video/call/{type}/{id}/event",
            SendCallEventResponse,
            path_params=path_params,
            json=json,
        )

    def collect_user_feedback(
        self,
        type: str,
        id: str,
        session: str,
        rating: int,
        sdk: str,
        sdk_version: str,
        user_session_id: str,
        reason: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[CollectUserFeedbackResponse]:
        path_params = {
            "type": type,
            "id": id,
            "session": session,
        }
        json = build_body_dict(
            rating=rating,
            sdk=sdk,
            sdk_version=sdk_version,
            user_session_id=user_session_id,
            reason=reason,
            custom=custom,
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/feedback/{session}",
            CollectUserFeedbackResponse,
            path_params=path_params,
            json=json,
        )

    def go_live(
        self,
        type: str,
        id: str,
        recording_storage_name: Optional[str] = None,
        start_hls: Optional[bool] = None,
        start_recording: Optional[bool] = None,
        start_transcription: Optional[bool] = None,
        transcription_storage_name: Optional[str] = None,
    ) -> StreamResponse[GoLiveResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            recording_storage_name=recording_storage_name,
            start_hls=start_hls,
            start_recording=start_recording,
            start_transcription=start_transcription,
            transcription_storage_name=transcription_storage_name,
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/go_live",
            GoLiveResponse,
            path_params=path_params,
            json=json,
        )

    def end_call(self, type: str, id: str) -> StreamResponse[EndCallResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/mark_ended",
            EndCallResponse,
            path_params=path_params,
        )

    def update_call_members(
        self,
        type: str,
        id: str,
        remove_members: Optional[List[str]] = None,
        update_members: Optional[List[MemberRequest]] = None,
    ) -> StreamResponse[UpdateCallMembersResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            remove_members=remove_members, update_members=update_members
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/members",
            UpdateCallMembersResponse,
            path_params=path_params,
            json=json,
        )

    def mute_users(
        self,
        type: str,
        id: str,
        audio: Optional[bool] = None,
        mute_all_users: Optional[bool] = None,
        muted_by_id: Optional[str] = None,
        screenshare: Optional[bool] = None,
        screenshare_audio: Optional[bool] = None,
        video: Optional[bool] = None,
        user_ids: Optional[List[str]] = None,
        muted_by: Optional[UserRequest] = None,
    ) -> StreamResponse[MuteUsersResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            audio=audio,
            mute_all_users=mute_all_users,
            muted_by_id=muted_by_id,
            screenshare=screenshare,
            screenshare_audio=screenshare_audio,
            video=video,
            user_ids=user_ids,
            muted_by=muted_by,
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/mute_users",
            MuteUsersResponse,
            path_params=path_params,
            json=json,
        )

    def video_pin(
        self, type: str, id: str, session_id: str, user_id: str
    ) -> StreamResponse[PinResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(session_id=session_id, user_id=user_id)

        return self.post(
            "/api/v2/video/call/{type}/{id}/pin",
            PinResponse,
            path_params=path_params,
            json=json,
        )

    def list_recordings(
        self, type: str, id: str
    ) -> StreamResponse[ListRecordingsResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.get(
            "/api/v2/video/call/{type}/{id}/recordings",
            ListRecordingsResponse,
            path_params=path_params,
        )

    def start_hls_broadcasting(
        self, type: str, id: str
    ) -> StreamResponse[StartHLSBroadcastingResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/start_broadcasting",
            StartHLSBroadcastingResponse,
            path_params=path_params,
        )

    def start_recording(
        self, type: str, id: str, recording_external_storage: Optional[str] = None
    ) -> StreamResponse[StartRecordingResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(recording_external_storage=recording_external_storage)

        return self.post(
            "/api/v2/video/call/{type}/{id}/start_recording",
            StartRecordingResponse,
            path_params=path_params,
            json=json,
        )

    def start_transcription(
        self, type: str, id: str, transcription_external_storage: Optional[str] = None
    ) -> StreamResponse[StartTranscriptionResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            transcription_external_storage=transcription_external_storage
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/start_transcription",
            StartTranscriptionResponse,
            path_params=path_params,
            json=json,
        )

    def get_call_stats(
        self, type: str, id: str, session: str
    ) -> StreamResponse[GetCallStatsResponse]:
        path_params = {
            "type": type,
            "id": id,
            "session": session,
        }

        return self.get(
            "/api/v2/video/call/{type}/{id}/stats/{session}",
            GetCallStatsResponse,
            path_params=path_params,
        )

    def stop_hls_broadcasting(
        self, type: str, id: str
    ) -> StreamResponse[StopHLSBroadcastingResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/stop_broadcasting",
            StopHLSBroadcastingResponse,
            path_params=path_params,
        )

    def stop_live(self, type: str, id: str) -> StreamResponse[StopLiveResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/stop_live",
            StopLiveResponse,
            path_params=path_params,
        )

    def stop_recording(
        self, type: str, id: str
    ) -> StreamResponse[StopRecordingResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/stop_recording",
            StopRecordingResponse,
            path_params=path_params,
        )

    def stop_transcription(
        self, type: str, id: str
    ) -> StreamResponse[StopTranscriptionResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.post(
            "/api/v2/video/call/{type}/{id}/stop_transcription",
            StopTranscriptionResponse,
            path_params=path_params,
        )

    def list_transcriptions(
        self, type: str, id: str
    ) -> StreamResponse[ListTranscriptionsResponse]:
        path_params = {
            "type": type,
            "id": id,
        }

        return self.get(
            "/api/v2/video/call/{type}/{id}/transcriptions",
            ListTranscriptionsResponse,
            path_params=path_params,
        )

    def unblock_user(
        self, type: str, id: str, user_id: str
    ) -> StreamResponse[UnblockUserResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(user_id=user_id)

        return self.post(
            "/api/v2/video/call/{type}/{id}/unblock",
            UnblockUserResponse,
            path_params=path_params,
            json=json,
        )

    def video_unpin(
        self, type: str, id: str, session_id: str, user_id: str
    ) -> StreamResponse[UnpinResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(session_id=session_id, user_id=user_id)

        return self.post(
            "/api/v2/video/call/{type}/{id}/unpin",
            UnpinResponse,
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
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            user_id=user_id,
            grant_permissions=grant_permissions,
            revoke_permissions=revoke_permissions,
        )

        return self.post(
            "/api/v2/video/call/{type}/{id}/user_permissions",
            UpdateUserPermissionsResponse,
            path_params=path_params,
            json=json,
        )

    def delete_recording(
        self, type: str, id: str, session: str, filename: str
    ) -> StreamResponse[DeleteRecordingResponse]:
        path_params = {
            "type": type,
            "id": id,
            "session": session,
            "filename": filename,
        }

        return self.delete(
            "/api/v2/video/call/{type}/{id}/{session}/recordings/{filename}",
            DeleteRecordingResponse,
            path_params=path_params,
        )

    def delete_transcription(
        self, type: str, id: str, session: str, filename: str
    ) -> StreamResponse[DeleteTranscriptionResponse]:
        path_params = {
            "type": type,
            "id": id,
            "session": session,
            "filename": filename,
        }

        return self.delete(
            "/api/v2/video/call/{type}/{id}/{session}/transcriptions/{filename}",
            DeleteTranscriptionResponse,
            path_params=path_params,
        )

    def query_calls(
        self,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[QueryCallsResponse]:
        json = build_body_dict(
            limit=limit,
            next=next,
            prev=prev,
            sort=sort,
            filter_conditions=filter_conditions,
        )

        return self.post("/api/v2/video/calls", QueryCallsResponse, json=json)

    def list_call_types(self) -> StreamResponse[ListCallTypeResponse]:
        return self.get("/api/v2/video/calltypes", ListCallTypeResponse)

    def create_call_type(
        self,
        name: str,
        external_storage: Optional[str] = None,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettings] = None,
        settings: Optional[CallSettingsRequest] = None,
    ) -> StreamResponse[CreateCallTypeResponse]:
        json = build_body_dict(
            name=name,
            external_storage=external_storage,
            grants=grants,
            notification_settings=notification_settings,
            settings=settings,
        )

        return self.post("/api/v2/video/calltypes", CreateCallTypeResponse, json=json)

    def delete_call_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/video/calltypes/{name}", Response, path_params=path_params
        )

    def get_call_type(self, name: str) -> StreamResponse[GetCallTypeResponse]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/video/calltypes/{name}",
            GetCallTypeResponse,
            path_params=path_params,
        )

    def update_call_type(
        self,
        name: str,
        external_storage: Optional[str] = None,
        grants: Optional[Dict[str, List[str]]] = None,
        notification_settings: Optional[NotificationSettings] = None,
        settings: Optional[CallSettingsRequest] = None,
    ) -> StreamResponse[UpdateCallTypeResponse]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(
            external_storage=external_storage,
            grants=grants,
            notification_settings=notification_settings,
            settings=settings,
        )

        return self.put(
            "/api/v2/video/calltypes/{name}",
            UpdateCallTypeResponse,
            path_params=path_params,
            json=json,
        )

    def get_edges(self) -> StreamResponse[GetEdgesResponse]:
        return self.get("/api/v2/video/edges", GetEdgesResponse)
