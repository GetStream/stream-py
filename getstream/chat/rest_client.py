from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import encode_query_param, request_to_dict


class ChatRestClient(BaseClient):

    def __init__(self, api_key: str, base_url: str, timeout: float, token: str):
        """
        Initializes ChatClient with BaseClient instance
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
    
    def list_block_lists(self) -> StreamResponse[ListBlockListResponse]:
        return self.get("/api/v2/chat/blocklists", ListBlockListResponse)
    
    def create_block_list(self, create_block_list_request: CreateBlockListRequest) -> StreamResponse[Response]:
        return self.post("/api/v2/chat/blocklists", Response, json=request_to_dict(create_block_list_request))
    
    def delete_block_list(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name, 
        }
        return self.delete("/api/v2/chat/blocklists/{name}", Response, path_params=path_params)
    
    def get_block_list(self, name: str) -> StreamResponse[GetBlockListResponse]:
        path_params = {
            "name": name, 
        }
        return self.get("/api/v2/chat/blocklists/{name}", GetBlockListResponse, path_params=path_params)
    
    def update_block_list(self, name: str, update_block_list_request: UpdateBlockListRequest = None) -> StreamResponse[Response]:
        path_params = {
            "name": name, 
        }
        return self.put("/api/v2/chat/blocklists/{name}", Response, path_params=path_params, json=request_to_dict(update_block_list_request))
    
    def query_channels(self, query_channels_request: QueryChannelsRequest = None) -> StreamResponse[QueryChannelsResponse]:
        return self.post("/api/v2/chat/channels", QueryChannelsResponse, json=request_to_dict(query_channels_request))
    
    def delete_channels(self, delete_channels_request: DeleteChannelsRequest) -> StreamResponse[DeleteChannelsResponse]:
        return self.post("/api/v2/chat/channels/delete", DeleteChannelsResponse, json=request_to_dict(delete_channels_request))
    
    def mark_channels_read(self, mark_channels_read_request: MarkChannelsReadRequest = None) -> StreamResponse[MarkReadResponse]:
        return self.post("/api/v2/chat/channels/read", MarkReadResponse, json=request_to_dict(mark_channels_read_request))
    
    def get_or_create_distinct_channel(self, type: str, channel_get_or_create_request: ChannelGetOrCreateRequest = None) -> StreamResponse[ChannelStateResponse]:
        path_params = {
            "type": type, 
        }
        return self.post("/api/v2/chat/channels/{type}/query", ChannelStateResponse, path_params=path_params, json=request_to_dict(channel_get_or_create_request))
    
    def delete_channel(self, type: str, id: str, hard_delete: Optional[bool] = None) -> StreamResponse[DeleteChannelResponse]:
        query_params = {
            "hard_delete": encode_query_param(hard_delete), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.delete("/api/v2/chat/channels/{type}/{id}", DeleteChannelResponse, query_params=query_params, path_params=path_params)
    
    def update_channel_partial(self, type: str, id: str, update_channel_partial_request: UpdateChannelPartialRequest = None) -> StreamResponse[UpdateChannelPartialResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.patch("/api/v2/chat/channels/{type}/{id}", UpdateChannelPartialResponse, path_params=path_params, json=request_to_dict(update_channel_partial_request))
    
    def update_channel(self, type: str, id: str, update_channel_request: UpdateChannelRequest = None) -> StreamResponse[UpdateChannelResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}", UpdateChannelResponse, path_params=path_params, json=request_to_dict(update_channel_request))
    
    def send_event(self, type: str, id: str, send_event_request: SendEventRequest) -> StreamResponse[EventResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/event", EventResponse, path_params=path_params, json=request_to_dict(send_event_request))
    
    def delete_file(self, type: str, id: str, url: Optional[str] = None) -> StreamResponse[FileDeleteResponse]:
        query_params = {
            "url": encode_query_param(url), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.delete("/api/v2/chat/channels/{type}/{id}/file", FileDeleteResponse, query_params=query_params, path_params=path_params)
    
    def upload_file(self, type: str, id: str, file_upload_request: FileUploadRequest = None) -> StreamResponse[FileUploadResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/file", FileUploadResponse, path_params=path_params, json=request_to_dict(file_upload_request))
    
    def hide_channel(self, type: str, id: str, hide_channel_request: HideChannelRequest = None) -> StreamResponse[HideChannelResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/hide", HideChannelResponse, path_params=path_params, json=request_to_dict(hide_channel_request))
    
    def delete_image(self, type: str, id: str, url: Optional[str] = None) -> StreamResponse[FileDeleteResponse]:
        query_params = {
            "url": encode_query_param(url), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.delete("/api/v2/chat/channels/{type}/{id}/image", FileDeleteResponse, query_params=query_params, path_params=path_params)
    
    def upload_image(self, type: str, id: str, image_upload_request: ImageUploadRequest = None) -> StreamResponse[ImageUploadResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/image", ImageUploadResponse, path_params=path_params, json=request_to_dict(image_upload_request))
    
    def send_message(self, type: str, id: str, send_message_request: SendMessageRequest) -> StreamResponse[SendMessageResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/message", SendMessageResponse, path_params=path_params, json=request_to_dict(send_message_request))
    
    def get_many_messages(self, type: str, id: str, ids: List[str]) -> StreamResponse[GetManyMessagesResponse]:
        query_params = {
            "ids": encode_query_param(ids), 
        }
        path_params = {
            "type": type, "id": id, 
        }
        return self.get("/api/v2/chat/channels/{type}/{id}/messages", GetManyMessagesResponse, query_params=query_params, path_params=path_params)
    
    def get_or_create_channel(self, type: str, id: str, channel_get_or_create_request: ChannelGetOrCreateRequest = None) -> StreamResponse[ChannelStateResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/query", ChannelStateResponse, path_params=path_params, json=request_to_dict(channel_get_or_create_request))
    
    def mark_read(self, type: str, id: str, mark_read_request: MarkReadRequest = None) -> StreamResponse[MarkReadResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/read", MarkReadResponse, path_params=path_params, json=request_to_dict(mark_read_request))
    
    def show_channel(self, type: str, id: str, show_channel_request: ShowChannelRequest = None) -> StreamResponse[ShowChannelResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/show", ShowChannelResponse, path_params=path_params, json=request_to_dict(show_channel_request))
    
    def truncate_channel(self, type: str, id: str, truncate_channel_request: TruncateChannelRequest = None) -> StreamResponse[TruncateChannelResponse]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/truncate", TruncateChannelResponse, path_params=path_params, json=request_to_dict(truncate_channel_request))
    
    def mark_unread(self, type: str, id: str, mark_unread_request: MarkUnreadRequest = None) -> StreamResponse[Response]:
        path_params = {
            "type": type, "id": id, 
        }
        return self.post("/api/v2/chat/channels/{type}/{id}/unread", Response, path_params=path_params, json=request_to_dict(mark_unread_request))
    
    def list_channel_types(self) -> StreamResponse[ListChannelTypesResponse]:
        return self.get("/api/v2/chat/channeltypes", ListChannelTypesResponse)
    
    def create_channel_type(self, create_channel_type_request: CreateChannelTypeRequest) -> StreamResponse[CreateChannelTypeResponse]:
        return self.post("/api/v2/chat/channeltypes", CreateChannelTypeResponse, json=request_to_dict(create_channel_type_request))
    
    def delete_channel_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name, 
        }
        return self.delete("/api/v2/chat/channeltypes/{name}", Response, path_params=path_params)
    
    def get_channel_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name, 
        }
        return self.get("/api/v2/chat/channeltypes/{name}", Response, path_params=path_params)
    
    def update_channel_type(self, name: str, update_channel_type_request: UpdateChannelTypeRequest) -> StreamResponse[UpdateChannelTypeResponse]:
        path_params = {
            "name": name, 
        }
        return self.put("/api/v2/chat/channeltypes/{name}", UpdateChannelTypeResponse, path_params=path_params, json=request_to_dict(update_channel_type_request))
    
    def list_commands(self) -> StreamResponse[ListCommandsResponse]:
        return self.get("/api/v2/chat/commands", ListCommandsResponse)
    
    def create_command(self, create_command_request: CreateCommandRequest) -> StreamResponse[CreateCommandResponse]:
        return self.post("/api/v2/chat/commands", CreateCommandResponse, json=request_to_dict(create_command_request))
    
    def delete_command(self, name: str) -> StreamResponse[DeleteCommandResponse]:
        path_params = {
            "name": name, 
        }
        return self.delete("/api/v2/chat/commands/{name}", DeleteCommandResponse, path_params=path_params)
    
    def get_command(self, name: str) -> StreamResponse[GetCommandResponse]:
        path_params = {
            "name": name, 
        }
        return self.get("/api/v2/chat/commands/{name}", GetCommandResponse, path_params=path_params)
    
    def update_command(self, name: str, update_command_request: UpdateCommandRequest) -> StreamResponse[UpdateCommandResponse]:
        path_params = {
            "name": name, 
        }
        return self.put("/api/v2/chat/commands/{name}", UpdateCommandResponse, path_params=path_params, json=request_to_dict(update_command_request))
    
    def export_channels(self, export_channels_request: ExportChannelsRequest) -> StreamResponse[ExportChannelsResponse]:
        return self.post("/api/v2/chat/export_channels", ExportChannelsResponse, json=request_to_dict(export_channels_request))
    
    def get_export_channels_status(self, id: str) -> StreamResponse[GetExportChannelsStatusResponse]:
        path_params = {
            "id": id, 
        }
        return self.get("/api/v2/chat/export_channels/{id}", GetExportChannelsStatusResponse, path_params=path_params)
    
    def query_members(self, payload: Optional[QueryMembersRequest] = None) -> StreamResponse[MembersResponse]:
        query_params = {
            "payload": encode_query_param(payload), 
        }
        return self.get("/api/v2/chat/members", MembersResponse, query_params=query_params)
    
    def delete_message(self, id: str, hard: Optional[bool] = None, deleted_by: Optional[str] = None) -> StreamResponse[DeleteMessageResponse]:
        query_params = {
            "hard": encode_query_param(hard), "deleted_by": encode_query_param(deleted_by), 
        }
        path_params = {
            "id": id, 
        }
        return self.delete("/api/v2/chat/messages/{id}", DeleteMessageResponse, query_params=query_params, path_params=path_params)
    
    def get_message(self, id: str, show_deleted_message: Optional[bool] = None) -> StreamResponse[GetMessageResponse]:
        query_params = {
            "show_deleted_message": encode_query_param(show_deleted_message), 
        }
        path_params = {
            "id": id, 
        }
        return self.get("/api/v2/chat/messages/{id}", GetMessageResponse, query_params=query_params, path_params=path_params)
    
    def update_message(self, id: str, update_message_request: UpdateMessageRequest) -> StreamResponse[UpdateMessageResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}", UpdateMessageResponse, path_params=path_params, json=request_to_dict(update_message_request))
    
    def update_message_partial(self, id: str, update_message_partial_request: UpdateMessagePartialRequest = None) -> StreamResponse[UpdateMessagePartialResponse]:
        path_params = {
            "id": id, 
        }
        return self.put("/api/v2/chat/messages/{id}", UpdateMessagePartialResponse, path_params=path_params, json=request_to_dict(update_message_partial_request))
    
    def run_message_action(self, id: str, message_action_request: MessageActionRequest) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}/action", MessageResponse, path_params=path_params, json=request_to_dict(message_action_request))
    
    def commit_message(self, id: str, commit_message_request: CommitMessageRequest = None) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}/commit", MessageResponse, path_params=path_params, json=request_to_dict(commit_message_request))
    
    def send_reaction(self, id: str, send_reaction_request: SendReactionRequest) -> StreamResponse[SendReactionResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}/reaction", SendReactionResponse, path_params=path_params, json=request_to_dict(send_reaction_request))
    
    def delete_reaction(self, id: str, type: str, user_id: Optional[str] = None) -> StreamResponse[ReactionRemovalResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "id": id, "type": type, 
        }
        return self.delete("/api/v2/chat/messages/{id}/reaction/{type}", ReactionRemovalResponse, query_params=query_params, path_params=path_params)
    
    def get_reactions(self, id: str, limit: Optional[int] = None, offset: Optional[int] = None) -> StreamResponse[GetReactionsResponse]:
        query_params = {
            "limit": encode_query_param(limit), "offset": encode_query_param(offset), 
        }
        path_params = {
            "id": id, 
        }
        return self.get("/api/v2/chat/messages/{id}/reactions", GetReactionsResponse, query_params=query_params, path_params=path_params)
    
    def translate_message(self, id: str, translate_message_request: TranslateMessageRequest) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}/translate", MessageResponse, path_params=path_params, json=request_to_dict(translate_message_request))
    
    def undelete_message(self, id: str, update_message_request: UpdateMessageRequest) -> StreamResponse[UpdateMessageResponse]:
        path_params = {
            "id": id, 
        }
        return self.post("/api/v2/chat/messages/{id}/undelete", UpdateMessageResponse, path_params=path_params, json=request_to_dict(update_message_request))
    
    def cast_poll_vote(self, message_id: str, poll_id: str, cast_poll_vote_request: CastPollVoteRequest) -> StreamResponse[PollVoteResponse]:
        path_params = {
            "message_id": message_id, "poll_id": poll_id, 
        }
        return self.post("/api/v2/chat/messages/{message_id}/polls/{poll_id}/vote", PollVoteResponse, path_params=path_params, json=request_to_dict(cast_poll_vote_request))
    
    def remove_poll_vote(self, message_id: str, poll_id: str, vote_id: str, user_id: Optional[str] = None) -> StreamResponse[PollVoteResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "message_id": message_id, "poll_id": poll_id, "vote_id": vote_id, 
        }
        return self.delete("/api/v2/chat/messages/{message_id}/polls/{poll_id}/vote/{vote_id}", PollVoteResponse, query_params=query_params, path_params=path_params)
    
    def get_replies(self, parent_id: str, id_gte: Optional[str] = None, id_gt: Optional[str] = None, id_lte: Optional[str] = None, id_lt: Optional[str] = None, created_at_after_or_equal: Optional[datetime] = None, created_at_after: Optional[datetime] = None, created_at_before_or_equal: Optional[datetime] = None, created_at_before: Optional[datetime] = None, id_around: Optional[str] = None, created_at_around: Optional[datetime] = None) -> StreamResponse[GetRepliesResponse]:
        query_params = {
            "id_gte": encode_query_param(id_gte), "id_gt": encode_query_param(id_gt), "id_lte": encode_query_param(id_lte), "id_lt": encode_query_param(id_lt), "created_at_after_or_equal": encode_query_param(created_at_after_or_equal), "created_at_after": encode_query_param(created_at_after), "created_at_before_or_equal": encode_query_param(created_at_before_or_equal), "created_at_before": encode_query_param(created_at_before), "id_around": encode_query_param(id_around), "created_at_around": encode_query_param(created_at_around), 
        }
        path_params = {
            "parent_id": parent_id, 
        }
        return self.get("/api/v2/chat/messages/{parent_id}/replies", GetRepliesResponse, query_params=query_params, path_params=path_params)
    
    def unban(self, target_user_id: str, type: Optional[str] = None, id: Optional[str] = None, created_by: Optional[str] = None) -> StreamResponse[Response]:
        query_params = {
            "target_user_id": encode_query_param(target_user_id), "type": encode_query_param(type), "id": encode_query_param(id), "created_by": encode_query_param(created_by), 
        }
        return self.delete("/api/v2/chat/moderation/ban", Response, query_params=query_params)
    
    def ban(self, ban_request: BanRequest) -> StreamResponse[Response]:
        return self.post("/api/v2/chat/moderation/ban", Response, json=request_to_dict(ban_request))
    
    def flag(self, flag_request: FlagRequest = None) -> StreamResponse[FlagResponse]:
        return self.post("/api/v2/chat/moderation/flag", FlagResponse, json=request_to_dict(flag_request))
    
    def query_message_flags(self, payload: Optional[QueryMessageFlagsRequest] = None) -> StreamResponse[QueryMessageFlagsResponse]:
        query_params = {
            "payload": encode_query_param(payload), 
        }
        return self.get("/api/v2/chat/moderation/flags/message", QueryMessageFlagsResponse, query_params=query_params)
    
    def mute_user(self, mute_user_request: MuteUserRequest) -> StreamResponse[MuteUserResponse]:
        return self.post("/api/v2/chat/moderation/mute", MuteUserResponse, json=request_to_dict(mute_user_request))
    
    def mute_channel(self, mute_channel_request: MuteChannelRequest = None) -> StreamResponse[MuteChannelResponse]:
        return self.post("/api/v2/chat/moderation/mute/channel", MuteChannelResponse, json=request_to_dict(mute_channel_request))
    
    def unmute_user(self, unmute_user_request: UnmuteUserRequest) -> StreamResponse[UnmuteResponse]:
        return self.post("/api/v2/chat/moderation/unmute", UnmuteResponse, json=request_to_dict(unmute_user_request))
    
    def unmute_channel(self, unmute_channel_request: UnmuteChannelRequest = None) -> StreamResponse[UnmuteResponse]:
        return self.post("/api/v2/chat/moderation/unmute/channel", UnmuteResponse, json=request_to_dict(unmute_channel_request))
    
    def create_poll(self, create_poll_request: CreatePollRequest) -> StreamResponse[PollResponse]:
        return self.post("/api/v2/chat/polls", PollResponse, json=request_to_dict(create_poll_request))
    
    def update_poll(self, update_poll_request: UpdatePollRequest) -> StreamResponse[PollResponse]:
        return self.put("/api/v2/chat/polls", PollResponse, json=request_to_dict(update_poll_request))
    
    def query_polls(self, user_id: Optional[str] = None, query_polls_request: QueryPollsRequest = None) -> StreamResponse[QueryPollsResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        return self.post("/api/v2/chat/polls/query", QueryPollsResponse, query_params=query_params, json=request_to_dict(query_polls_request))
    
    def delete_poll(self, poll_id: str, user_id: Optional[str] = None) -> StreamResponse[Response]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "poll_id": poll_id, 
        }
        return self.delete("/api/v2/chat/polls/{poll_id}", Response, query_params=query_params, path_params=path_params)
    
    def get_poll(self, poll_id: str, user_id: Optional[str] = None) -> StreamResponse[PollResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "poll_id": poll_id, 
        }
        return self.get("/api/v2/chat/polls/{poll_id}", PollResponse, query_params=query_params, path_params=path_params)
    
    def update_poll_partial(self, poll_id: str, update_poll_partial_request: UpdatePollPartialRequest) -> StreamResponse[PollResponse]:
        path_params = {
            "poll_id": poll_id, 
        }
        return self.patch("/api/v2/chat/polls/{poll_id}", PollResponse, path_params=path_params, json=request_to_dict(update_poll_partial_request))
    
    def create_poll_option(self, poll_id: str, create_poll_option_request: CreatePollOptionRequest) -> StreamResponse[PollOptionResponse]:
        path_params = {
            "poll_id": poll_id, 
        }
        return self.post("/api/v2/chat/polls/{poll_id}/options", PollOptionResponse, path_params=path_params, json=request_to_dict(create_poll_option_request))
    
    def update_poll_option(self, poll_id: str, update_poll_option_request: UpdatePollOptionRequest) -> StreamResponse[PollOptionResponse]:
        path_params = {
            "poll_id": poll_id, 
        }
        return self.put("/api/v2/chat/polls/{poll_id}/options", PollOptionResponse, path_params=path_params, json=request_to_dict(update_poll_option_request))
    
    def delete_poll_option(self, poll_id: str, option_id: str, user_id: Optional[str] = None) -> StreamResponse[Response]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "poll_id": poll_id, "option_id": option_id, 
        }
        return self.delete("/api/v2/chat/polls/{poll_id}/options/{option_id}", Response, query_params=query_params, path_params=path_params)
    
    def get_poll_option(self, poll_id: str, option_id: str, user_id: Optional[str] = None) -> StreamResponse[PollOptionResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "poll_id": poll_id, "option_id": option_id, 
        }
        return self.get("/api/v2/chat/polls/{poll_id}/options/{option_id}", PollOptionResponse, query_params=query_params, path_params=path_params)
    
    def query_poll_votes(self, poll_id: str, query_poll_votes_request: QueryPollVotesRequest, user_id: Optional[str] = None) -> StreamResponse[PollVotesResponse]:
        query_params = {
            "user_id": encode_query_param(user_id), 
        }
        path_params = {
            "poll_id": poll_id, 
        }
        return self.post("/api/v2/chat/polls/{poll_id}/votes", PollVotesResponse, query_params=query_params, path_params=path_params, json=request_to_dict(query_poll_votes_request))
    
    def query_banned_users(self, payload: Optional[QueryBannedUsersRequest] = None) -> StreamResponse[QueryBannedUsersResponse]:
        query_params = {
            "payload": encode_query_param(payload), 
        }
        return self.get("/api/v2/chat/query_banned_users", QueryBannedUsersResponse, query_params=query_params)
    
    def search(self, payload: Optional[SearchRequest] = None) -> StreamResponse[SearchResponse]:
        query_params = {
            "payload": encode_query_param(payload), 
        }
        return self.get("/api/v2/chat/search", SearchResponse, query_params=query_params)
    
    def query_threads(self, connection_id: Optional[str] = None, query_threads_request: QueryThreadsRequest = None) -> StreamResponse[QueryThreadsResponse]:
        query_params = {
            "connection_id": encode_query_param(connection_id), 
        }
        return self.post("/api/v2/chat/threads", QueryThreadsResponse, query_params=query_params, json=request_to_dict(query_threads_request))
    
    def get_thread(self, message_id: str, watch: Optional[bool] = None, connection_id: Optional[str] = None, reply_limit: Optional[int] = None, participant_limit: Optional[int] = None) -> StreamResponse[GetThreadResponse]:
        query_params = {
            "watch": encode_query_param(watch), "connection_id": encode_query_param(connection_id), "reply_limit": encode_query_param(reply_limit), "participant_limit": encode_query_param(participant_limit), 
        }
        path_params = {
            "message_id": message_id, 
        }
        return self.get("/api/v2/chat/threads/{message_id}", GetThreadResponse, query_params=query_params, path_params=path_params)
    
    def update_thread_partial(self, message_id: str, update_thread_partial_request: UpdateThreadPartialRequest = None) -> StreamResponse[UpdateThreadPartialResponse]:
        path_params = {
            "message_id": message_id, 
        }
        return self.patch("/api/v2/chat/threads/{message_id}", UpdateThreadPartialResponse, path_params=path_params, json=request_to_dict(update_thread_partial_request))
    
    def unread_counts(self) -> StreamResponse[WrappedUnreadCountsResponse]:
        return self.get("/api/v2/chat/unread", WrappedUnreadCountsResponse)
    
    def unread_counts_batch(self, unread_counts_batch_request: UnreadCountsBatchRequest) -> StreamResponse[UnreadCountsBatchResponse]:
        return self.post("/api/v2/chat/unread_batch", UnreadCountsBatchResponse, json=request_to_dict(unread_counts_batch_request))
    
    def send_user_custom_event(self, user_id: str, send_user_custom_event_request: SendUserCustomEventRequest) -> StreamResponse[Response]:
        path_params = {
            "user_id": user_id, 
        }
        return self.post("/api/v2/chat/users/{user_id}/event", Response, path_params=path_params, json=request_to_dict(send_user_custom_event_request))
    