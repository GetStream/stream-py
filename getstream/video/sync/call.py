from typing import List
from getstream.models.call_request import CallRequest
from getstream.models.custom_video_event import CustomVideoEvent
from getstream.models.list_recordings_response import ListRecordingsResponse
from getstream.models.end_call_response import EndCallResponse
from getstream.models.member_request import MemberRequest
from getstream.models.response import Response
from getstream.models.start_recording_response import StartRecordingResponse
from getstream.models.request_permission_response import RequestPermissionResponse
from getstream.models.go_live_response import GoLiveResponse
from getstream.models.mute_users_request import MuteUsersRequest
from getstream.models.stop_recording_response import StopRecordingResponse
from getstream.models.send_reaction_request import SendReactionRequest
from getstream.models.stop_broadcasting_response import StopBroadcastingResponse
from getstream.models.update_call_members_response import UpdateCallMembersResponse
from getstream.models.stop_transcription_response import StopTranscriptionResponse
from getstream.models.unblock_user_response import UnblockUserResponse
from getstream.models.stop_live_response import StopLiveResponse
from getstream.models.get_or_create_call_response import GetOrCreateCallResponse
from getstream.models.join_call_response import JoinCallResponse
from getstream.models.query_members_response import QueryMembersResponse
from getstream.models.start_broadcasting_response import StartBroadcastingResponse
from getstream.models.get_call_response import GetCallResponse
from getstream.models.block_user_request import BlockUserRequest
from getstream.models.block_user_response import BlockUserResponse
from getstream.models.query_members_request import QueryMembersRequest
from getstream.models.update_call_request import UpdateCallRequest
from getstream.models.update_call_response import UpdateCallResponse
from getstream.models.start_transcription_response import StartTranscriptionResponse
from getstream.models.update_user_permissions_response import (
    UpdateUserPermissionsResponse,
)
from getstream.models.mute_users_response import MuteUsersResponse
from getstream.models.send_reaction_response import SendReactionResponse
from getstream.models.request_permission_request import RequestPermissionRequest
from getstream.models.update_user_permissions_request import (
    UpdateUserPermissionsRequest,
)
from getstream.models.unblock_user_request import UnblockUserRequest
from getstream.models.join_call_request import JoinCallRequest
from getstream.stream_response import StreamResponse
from getstream.video.sync.client import VideoClient


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

    def delete_recording(
        self, session_id: str, recording_id: str
    ) -> StreamResponse[Response]:
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
