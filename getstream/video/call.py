from getstream.models import *
from getstream.stream_response import StreamResponse


class Call:
    def __init__(
        self, client, call_type: str, call_id: str = None, custom_data: Dict = None
    ):
        self.id = call_id
        self.call_type = call_type
        self.client = client
        self.custom_data = custom_data or {}

    def _sync_from_response(self, data):
        if hasattr(data, "call") and isinstance(data.call, CallResponse):
            self.custom_data = data.call.custom

    def get(
        self,
        members_limit: Optional[int] = None,
        ring: Optional[bool] = None,
        notify: Optional[bool] = None,
    ) -> StreamResponse[GetCallResponse]:
        response = self.client.get_call(
            type=self.call_type,
            id=self.id,
            members_limit=members_limit,
            ring=ring,
            notify=notify,
        )
        self._sync_from_response(response.data)
        return response

    def update(
        self,
        starts_at: Optional[datetime] = None,
        custom: Optional[Dict[str, object]] = None,
        settings_override: Optional[CallSettingsRequest] = None,
    ) -> StreamResponse[UpdateCallResponse]:
        response = self.client.update_call(
            type=self.call_type,
            id=self.id,
            starts_at=starts_at,
            custom=custom,
            settings_override=settings_override,
        )
        self._sync_from_response(response.data)
        return response

    def get_or_create(
        self,
        members_limit: Optional[int] = None,
        notify: Optional[bool] = None,
        ring: Optional[bool] = None,
        data: Optional[CallRequest] = None,
    ) -> StreamResponse[GetOrCreateCallResponse]:
        response = self.client.get_or_create_call(
            type=self.call_type,
            id=self.id,
            members_limit=members_limit,
            notify=notify,
            ring=ring,
            data=data,
        )
        self._sync_from_response(response.data)
        return response

    def block_user(self, user_id: str) -> StreamResponse[BlockUserResponse]:
        response = self.client.block_user(
            type=self.call_type, id=self.id, user_id=user_id
        )
        self._sync_from_response(response.data)
        return response

    def send_call_event(
        self,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[SendCallEventResponse]:
        response = self.client.send_call_event(
            type=self.call_type, id=self.id, user_id=user_id, custom=custom, user=user
        )
        self._sync_from_response(response.data)
        return response

    def collect_user_feedback(
        self,
        session: str,
        rating: int,
        sdk: str,
        sdk_version: str,
        user_session_id: str,
        reason: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[CollectUserFeedbackResponse]:
        response = self.client.collect_user_feedback(
            type=self.call_type,
            id=self.id,
            session=session,
            rating=rating,
            sdk=sdk,
            sdk_version=sdk_version,
            user_session_id=user_session_id,
            reason=reason,
            custom=custom,
        )
        self._sync_from_response(response.data)
        return response

    def go_live(
        self,
        recording_storage_name: Optional[str] = None,
        start_hls: Optional[bool] = None,
        start_recording: Optional[bool] = None,
        start_transcription: Optional[bool] = None,
        transcription_storage_name: Optional[str] = None,
    ) -> StreamResponse[GoLiveResponse]:
        response = self.client.go_live(
            type=self.call_type,
            id=self.id,
            recording_storage_name=recording_storage_name,
            start_hls=start_hls,
            start_recording=start_recording,
            start_transcription=start_transcription,
            transcription_storage_name=transcription_storage_name,
        )
        self._sync_from_response(response.data)
        return response

    def end(self) -> StreamResponse[EndCallResponse]:
        response = self.client.end_call(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def update_call_members(
        self,
        remove_members: Optional[List[str]] = None,
        update_members: Optional[List[MemberRequest]] = None,
    ) -> StreamResponse[UpdateCallMembersResponse]:
        response = self.client.update_call_members(
            type=self.call_type,
            id=self.id,
            remove_members=remove_members,
            update_members=update_members,
        )
        self._sync_from_response(response.data)
        return response

    def mute_users(
        self,
        audio: Optional[bool] = None,
        mute_all_users: Optional[bool] = None,
        muted_by_id: Optional[str] = None,
        screenshare: Optional[bool] = None,
        screenshare_audio: Optional[bool] = None,
        video: Optional[bool] = None,
        user_ids: Optional[List[str]] = None,
        muted_by: Optional[UserRequest] = None,
    ) -> StreamResponse[MuteUsersResponse]:
        response = self.client.mute_users(
            type=self.call_type,
            id=self.id,
            audio=audio,
            mute_all_users=mute_all_users,
            muted_by_id=muted_by_id,
            screenshare=screenshare,
            screenshare_audio=screenshare_audio,
            video=video,
            user_ids=user_ids,
            muted_by=muted_by,
        )
        self._sync_from_response(response.data)
        return response

    def video_pin(self, session_id: str, user_id: str) -> StreamResponse[PinResponse]:
        response = self.client.video_pin(
            type=self.call_type, id=self.id, session_id=session_id, user_id=user_id
        )
        self._sync_from_response(response.data)
        return response

    def list_recordings(self) -> StreamResponse[ListRecordingsResponse]:
        response = self.client.list_recordings(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def start_hls_broadcasting(self) -> StreamResponse[StartHLSBroadcastingResponse]:
        response = self.client.start_hls_broadcasting(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def start_recording(
        self, recording_external_storage: Optional[str] = None
    ) -> StreamResponse[StartRecordingResponse]:
        response = self.client.start_recording(
            type=self.call_type,
            id=self.id,
            recording_external_storage=recording_external_storage,
        )
        self._sync_from_response(response.data)
        return response

    def start_transcription(
        self, transcription_external_storage: Optional[str] = None
    ) -> StreamResponse[StartTranscriptionResponse]:
        response = self.client.start_transcription(
            type=self.call_type,
            id=self.id,
            transcription_external_storage=transcription_external_storage,
        )
        self._sync_from_response(response.data)
        return response

    def get_call_stats(self, session: str) -> StreamResponse[GetCallStatsResponse]:
        response = self.client.get_call_stats(
            type=self.call_type, id=self.id, session=session
        )
        self._sync_from_response(response.data)
        return response

    def stop_hls_broadcasting(self) -> StreamResponse[StopHLSBroadcastingResponse]:
        response = self.client.stop_hls_broadcasting(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def stop_live(self) -> StreamResponse[StopLiveResponse]:
        response = self.client.stop_live(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def stop_recording(self) -> StreamResponse[StopRecordingResponse]:
        response = self.client.stop_recording(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def stop_transcription(self) -> StreamResponse[StopTranscriptionResponse]:
        response = self.client.stop_transcription(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def list_transcriptions(self) -> StreamResponse[ListTranscriptionsResponse]:
        response = self.client.list_transcriptions(type=self.call_type, id=self.id)
        self._sync_from_response(response.data)
        return response

    def unblock_user(self, user_id: str) -> StreamResponse[UnblockUserResponse]:
        response = self.client.unblock_user(
            type=self.call_type, id=self.id, user_id=user_id
        )
        self._sync_from_response(response.data)
        return response

    def video_unpin(
        self, session_id: str, user_id: str
    ) -> StreamResponse[UnpinResponse]:
        response = self.client.video_unpin(
            type=self.call_type, id=self.id, session_id=session_id, user_id=user_id
        )
        self._sync_from_response(response.data)
        return response

    def update_user_permissions(
        self,
        user_id: str,
        grant_permissions: Optional[List[str]] = None,
        revoke_permissions: Optional[List[str]] = None,
    ) -> StreamResponse[UpdateUserPermissionsResponse]:
        response = self.client.update_user_permissions(
            type=self.call_type,
            id=self.id,
            user_id=user_id,
            grant_permissions=grant_permissions,
            revoke_permissions=revoke_permissions,
        )
        self._sync_from_response(response.data)
        return response

    def delete_recording(
        self, session: str, filename: str
    ) -> StreamResponse[DeleteRecordingResponse]:
        response = self.client.delete_recording(
            type=self.call_type, id=self.id, session=session, filename=filename
        )
        self._sync_from_response(response.data)
        return response

    def delete_transcription(
        self, session: str, filename: str
    ) -> StreamResponse[DeleteTranscriptionResponse]:
        response = self.client.delete_transcription(
            type=self.call_type, id=self.id, session=session, filename=filename
        )
        self._sync_from_response(response.data)
        return response

    create = get_or_create
