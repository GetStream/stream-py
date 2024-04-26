from getstream.base import BaseClient
from getstream.models import *
from getstream.stream_response import StreamResponse
from getstream.utils import build_query_param, build_body_dict


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

    def create_block_list(
        self, name: str, words: List[str], type: Optional[str] = None
    ) -> StreamResponse[Response]:
        json = build_body_dict(name=name, words=words, type=type)

        return self.post("/api/v2/chat/blocklists", Response, json=json)

    def delete_block_list(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/chat/blocklists/{name}", Response, path_params=path_params
        )

    def get_block_list(self, name: str) -> StreamResponse[GetBlockListResponse]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/chat/blocklists/{name}",
            GetBlockListResponse,
            path_params=path_params,
        )

    def update_block_list(
        self, name: str, words: Optional[List[str]] = None
    ) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(words=words)

        return self.put(
            "/api/v2/chat/blocklists/{name}",
            Response,
            path_params=path_params,
            json=json,
        )

    def query_channels(
        self,
        limit: Optional[int] = None,
        member_limit: Optional[int] = None,
        message_limit: Optional[int] = None,
        offset: Optional[int] = None,
        state: Optional[bool] = None,
        user_id: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter_conditions: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[QueryChannelsResponse]:
        json = build_body_dict(
            limit=limit,
            member_limit=member_limit,
            message_limit=message_limit,
            offset=offset,
            state=state,
            user_id=user_id,
            sort=sort,
            filter_conditions=filter_conditions,
            user=user,
        )

        return self.post("/api/v2/chat/channels", QueryChannelsResponse, json=json)

    def delete_channels(
        self, cids: List[str], hard_delete: Optional[bool] = None
    ) -> StreamResponse[DeleteChannelsResponse]:
        json = build_body_dict(cids=cids, hard_delete=hard_delete)

        return self.post(
            "/api/v2/chat/channels/delete", DeleteChannelsResponse, json=json
        )

    def mark_channels_read(
        self,
        user_id: Optional[str] = None,
        read_by_channel: Optional[Dict[str, str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MarkReadResponse]:
        json = build_body_dict(
            user_id=user_id, read_by_channel=read_by_channel, user=user
        )

        return self.post("/api/v2/chat/channels/read", MarkReadResponse, json=json)

    def get_or_create_distinct_channel(
        self,
        type: str,
        hide_for_creator: Optional[bool] = None,
        state: Optional[bool] = None,
        thread_unread_counts: Optional[bool] = None,
        data: Optional[ChannelInput] = None,
        members: Optional[PaginationParams] = None,
        messages: Optional[MessagePaginationParams] = None,
        watchers: Optional[PaginationParams] = None,
    ) -> StreamResponse[ChannelStateResponse]:
        path_params = {
            "type": type,
        }
        json = build_body_dict(
            hide_for_creator=hide_for_creator,
            state=state,
            thread_unread_counts=thread_unread_counts,
            data=data,
            members=members,
            messages=messages,
            watchers=watchers,
        )

        return self.post(
            "/api/v2/chat/channels/{type}/query",
            ChannelStateResponse,
            path_params=path_params,
            json=json,
        )

    def delete_channel(
        self, type: str, id: str, hard_delete: Optional[bool] = None
    ) -> StreamResponse[DeleteChannelResponse]:
        query_params = build_query_param(hard_delete=hard_delete)
        path_params = {
            "type": type,
            "id": id,
        }

        return self.delete(
            "/api/v2/chat/channels/{type}/{id}",
            DeleteChannelResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_channel_partial(
        self,
        type: str,
        id: str,
        user_id: Optional[str] = None,
        unset: Optional[List[str]] = None,
        set: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UpdateChannelPartialResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(user_id=user_id, unset=unset, set=set, user=user)

        return self.patch(
            "/api/v2/chat/channels/{type}/{id}",
            UpdateChannelPartialResponse,
            path_params=path_params,
            json=json,
        )

    def update_channel(
        self,
        type: str,
        id: str,
        accept_invite: Optional[bool] = None,
        cooldown: Optional[int] = None,
        hide_history: Optional[bool] = None,
        reject_invite: Optional[bool] = None,
        skip_push: Optional[bool] = None,
        user_id: Optional[str] = None,
        add_members: Optional[List[Optional[ChannelMember]]] = None,
        add_moderators: Optional[List[str]] = None,
        assign_roles: Optional[List[Optional[ChannelMember]]] = None,
        demote_moderators: Optional[List[str]] = None,
        invites: Optional[List[Optional[ChannelMember]]] = None,
        remove_members: Optional[List[str]] = None,
        data: Optional[ChannelInput] = None,
        message: Optional[MessageRequest] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UpdateChannelResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            accept_invite=accept_invite,
            cooldown=cooldown,
            hide_history=hide_history,
            reject_invite=reject_invite,
            skip_push=skip_push,
            user_id=user_id,
            add_members=add_members,
            add_moderators=add_moderators,
            assign_roles=assign_roles,
            demote_moderators=demote_moderators,
            invites=invites,
            remove_members=remove_members,
            data=data,
            message=message,
            user=user,
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}",
            UpdateChannelResponse,
            path_params=path_params,
            json=json,
        )

    def send_event(
        self, type: str, id: str, event: EventRequest
    ) -> StreamResponse[EventResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(event=event)

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/event",
            EventResponse,
            path_params=path_params,
            json=json,
        )

    def delete_file(
        self, type: str, id: str, url: Optional[str] = None
    ) -> StreamResponse[FileDeleteResponse]:
        query_params = build_query_param(url=url)
        path_params = {
            "type": type,
            "id": id,
        }

        return self.delete(
            "/api/v2/chat/channels/{type}/{id}/file",
            FileDeleteResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def upload_file(
        self,
        type: str,
        id: str,
        file: Optional[str] = None,
        user: Optional[OnlyUserID] = None,
    ) -> StreamResponse[FileUploadResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(file=file, user=user)

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/file",
            FileUploadResponse,
            path_params=path_params,
            json=json,
        )

    def hide_channel(
        self,
        type: str,
        id: str,
        clear_history: Optional[bool] = None,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[HideChannelResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(clear_history=clear_history, user_id=user_id, user=user)

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/hide",
            HideChannelResponse,
            path_params=path_params,
            json=json,
        )

    def delete_image(
        self, type: str, id: str, url: Optional[str] = None
    ) -> StreamResponse[FileDeleteResponse]:
        query_params = build_query_param(url=url)
        path_params = {
            "type": type,
            "id": id,
        }

        return self.delete(
            "/api/v2/chat/channels/{type}/{id}/image",
            FileDeleteResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def upload_image(
        self,
        type: str,
        id: str,
        file: Optional[str] = None,
        upload_sizes: Optional[List[ImageSize]] = None,
        user: Optional[OnlyUserID] = None,
    ) -> StreamResponse[ImageUploadResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(file=file, upload_sizes=upload_sizes, user=user)

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/image",
            ImageUploadResponse,
            path_params=path_params,
            json=json,
        )

    def send_message(
        self,
        type: str,
        id: str,
        message: MessageRequest,
        force_moderation: Optional[bool] = None,
        keep_channel_hidden: Optional[bool] = None,
        pending: Optional[bool] = None,
        skip_enrich_url: Optional[bool] = None,
        skip_push: Optional[bool] = None,
        pending_message_metadata: Optional[Dict[str, str]] = None,
    ) -> StreamResponse[SendMessageResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            message=message,
            force_moderation=force_moderation,
            keep_channel_hidden=keep_channel_hidden,
            pending=pending,
            skip_enrich_url=skip_enrich_url,
            skip_push=skip_push,
            pending_message_metadata=pending_message_metadata,
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/message",
            SendMessageResponse,
            path_params=path_params,
            json=json,
        )

    def get_many_messages(
        self, type: str, id: str, ids: List[str]
    ) -> StreamResponse[GetManyMessagesResponse]:
        query_params = build_query_param(ids=ids)
        path_params = {
            "type": type,
            "id": id,
        }

        return self.get(
            "/api/v2/chat/channels/{type}/{id}/messages",
            GetManyMessagesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def get_or_create_channel(
        self,
        type: str,
        id: str,
        hide_for_creator: Optional[bool] = None,
        state: Optional[bool] = None,
        thread_unread_counts: Optional[bool] = None,
        data: Optional[ChannelInput] = None,
        members: Optional[PaginationParams] = None,
        messages: Optional[MessagePaginationParams] = None,
        watchers: Optional[PaginationParams] = None,
    ) -> StreamResponse[ChannelStateResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            hide_for_creator=hide_for_creator,
            state=state,
            thread_unread_counts=thread_unread_counts,
            data=data,
            members=members,
            messages=messages,
            watchers=watchers,
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/query",
            ChannelStateResponse,
            path_params=path_params,
            json=json,
        )

    def mark_read(
        self,
        type: str,
        id: str,
        message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MarkReadResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            message_id=message_id, thread_id=thread_id, user_id=user_id, user=user
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/read",
            MarkReadResponse,
            path_params=path_params,
            json=json,
        )

    def show_channel(
        self,
        type: str,
        id: str,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[ShowChannelResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(user_id=user_id, user=user)

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/show",
            ShowChannelResponse,
            path_params=path_params,
            json=json,
        )

    def truncate_channel(
        self,
        type: str,
        id: str,
        hard_delete: Optional[bool] = None,
        skip_push: Optional[bool] = None,
        truncated_at: Optional[datetime] = None,
        user_id: Optional[str] = None,
        message: Optional[MessageRequest] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[TruncateChannelResponse]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            hard_delete=hard_delete,
            skip_push=skip_push,
            truncated_at=truncated_at,
            user_id=user_id,
            message=message,
            user=user,
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/truncate",
            TruncateChannelResponse,
            path_params=path_params,
            json=json,
        )

    def mark_unread(
        self,
        type: str,
        id: str,
        message_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[Response]:
        path_params = {
            "type": type,
            "id": id,
        }
        json = build_body_dict(
            message_id=message_id, thread_id=thread_id, user_id=user_id, user=user
        )

        return self.post(
            "/api/v2/chat/channels/{type}/{id}/unread",
            Response,
            path_params=path_params,
            json=json,
        )

    def list_channel_types(self) -> StreamResponse[ListChannelTypesResponse]:
        return self.get("/api/v2/chat/channeltypes", ListChannelTypesResponse)

    def create_channel_type(
        self,
        automod: str,
        automod_behavior: str,
        max_message_length: int,
        name: str,
        blocklist: Optional[str] = None,
        blocklist_behavior: Optional[str] = None,
        connect_events: Optional[bool] = None,
        custom_events: Optional[bool] = None,
        mark_messages_pending: Optional[bool] = None,
        message_retention: Optional[str] = None,
        mutes: Optional[bool] = None,
        polls: Optional[bool] = None,
        push_notifications: Optional[bool] = None,
        reactions: Optional[bool] = None,
        read_events: Optional[bool] = None,
        replies: Optional[bool] = None,
        search: Optional[bool] = None,
        typing_events: Optional[bool] = None,
        uploads: Optional[bool] = None,
        url_enrichment: Optional[bool] = None,
        blocklists: Optional[List[BlockListOptions]] = None,
        commands: Optional[List[str]] = None,
        permissions: Optional[List[PolicyRequest]] = None,
        grants: Optional[Dict[str, List[str]]] = None,
    ) -> StreamResponse[CreateChannelTypeResponse]:
        json = build_body_dict(
            automod=automod,
            automod_behavior=automod_behavior,
            max_message_length=max_message_length,
            name=name,
            blocklist=blocklist,
            blocklist_behavior=blocklist_behavior,
            connect_events=connect_events,
            custom_events=custom_events,
            mark_messages_pending=mark_messages_pending,
            message_retention=message_retention,
            mutes=mutes,
            polls=polls,
            push_notifications=push_notifications,
            reactions=reactions,
            read_events=read_events,
            replies=replies,
            search=search,
            typing_events=typing_events,
            uploads=uploads,
            url_enrichment=url_enrichment,
            blocklists=blocklists,
            commands=commands,
            permissions=permissions,
            grants=grants,
        )

        return self.post(
            "/api/v2/chat/channeltypes", CreateChannelTypeResponse, json=json
        )

    def delete_channel_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/chat/channeltypes/{name}", Response, path_params=path_params
        )

    def get_channel_type(self, name: str) -> StreamResponse[Response]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/chat/channeltypes/{name}", Response, path_params=path_params
        )

    def update_channel_type(
        self,
        name: str,
        automod: str,
        automod_behavior: str,
        max_message_length: int,
        blocklist: Optional[str] = None,
        blocklist_behavior: Optional[str] = None,
        connect_events: Optional[bool] = None,
        custom_events: Optional[bool] = None,
        mark_messages_pending: Optional[bool] = None,
        mutes: Optional[bool] = None,
        polls: Optional[bool] = None,
        push_notifications: Optional[bool] = None,
        quotes: Optional[bool] = None,
        reactions: Optional[bool] = None,
        read_events: Optional[bool] = None,
        reminders: Optional[bool] = None,
        replies: Optional[bool] = None,
        search: Optional[bool] = None,
        typing_events: Optional[bool] = None,
        uploads: Optional[bool] = None,
        url_enrichment: Optional[bool] = None,
        allowed_flag_reasons: Optional[List[str]] = None,
        blocklists: Optional[List[BlockListOptions]] = None,
        commands: Optional[List[str]] = None,
        permissions: Optional[List[PolicyRequest]] = None,
        automod_thresholds: Optional[Thresholds] = None,
        grants: Optional[Dict[str, List[str]]] = None,
    ) -> StreamResponse[UpdateChannelTypeResponse]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(
            automod=automod,
            automod_behavior=automod_behavior,
            max_message_length=max_message_length,
            blocklist=blocklist,
            blocklist_behavior=blocklist_behavior,
            connect_events=connect_events,
            custom_events=custom_events,
            mark_messages_pending=mark_messages_pending,
            mutes=mutes,
            polls=polls,
            push_notifications=push_notifications,
            quotes=quotes,
            reactions=reactions,
            read_events=read_events,
            reminders=reminders,
            replies=replies,
            search=search,
            typing_events=typing_events,
            uploads=uploads,
            url_enrichment=url_enrichment,
            allowed_flag_reasons=allowed_flag_reasons,
            blocklists=blocklists,
            commands=commands,
            permissions=permissions,
            automod_thresholds=automod_thresholds,
            grants=grants,
        )

        return self.put(
            "/api/v2/chat/channeltypes/{name}",
            UpdateChannelTypeResponse,
            path_params=path_params,
            json=json,
        )

    def list_commands(self) -> StreamResponse[ListCommandsResponse]:
        return self.get("/api/v2/chat/commands", ListCommandsResponse)

    def create_command(
        self,
        description: str,
        name: str,
        args: Optional[str] = None,
        set: Optional[str] = None,
    ) -> StreamResponse[CreateCommandResponse]:
        json = build_body_dict(description=description, name=name, args=args, set=set)

        return self.post("/api/v2/chat/commands", CreateCommandResponse, json=json)

    def delete_command(self, name: str) -> StreamResponse[DeleteCommandResponse]:
        path_params = {
            "name": name,
        }

        return self.delete(
            "/api/v2/chat/commands/{name}",
            DeleteCommandResponse,
            path_params=path_params,
        )

    def get_command(self, name: str) -> StreamResponse[GetCommandResponse]:
        path_params = {
            "name": name,
        }

        return self.get(
            "/api/v2/chat/commands/{name}", GetCommandResponse, path_params=path_params
        )

    def update_command(
        self,
        name: str,
        description: str,
        args: Optional[str] = None,
        set: Optional[str] = None,
    ) -> StreamResponse[UpdateCommandResponse]:
        path_params = {
            "name": name,
        }
        json = build_body_dict(description=description, args=args, set=set)

        return self.put(
            "/api/v2/chat/commands/{name}",
            UpdateCommandResponse,
            path_params=path_params,
            json=json,
        )

    def export_channels(
        self,
        channels: List[ChannelExport],
        clear_deleted_message_text: Optional[bool] = None,
        export_users: Optional[bool] = None,
        include_truncated_messages: Optional[bool] = None,
        version: Optional[str] = None,
    ) -> StreamResponse[ExportChannelsResponse]:
        json = build_body_dict(
            channels=channels,
            clear_deleted_message_text=clear_deleted_message_text,
            export_users=export_users,
            include_truncated_messages=include_truncated_messages,
            version=version,
        )

        return self.post(
            "/api/v2/chat/export_channels", ExportChannelsResponse, json=json
        )

    def get_export_channels_status(
        self, id: str
    ) -> StreamResponse[GetExportChannelsStatusResponse]:
        path_params = {
            "id": id,
        }

        return self.get(
            "/api/v2/chat/export_channels/{id}",
            GetExportChannelsStatusResponse,
            path_params=path_params,
        )

    def query_members(
        self, payload: Optional[QueryMembersRequest] = None
    ) -> StreamResponse[MembersResponse]:
        query_params = build_query_param(payload=payload)

        return self.get(
            "/api/v2/chat/members", MembersResponse, query_params=query_params
        )

    def delete_message(
        self, id: str, hard: Optional[bool] = None, deleted_by: Optional[str] = None
    ) -> StreamResponse[DeleteMessageResponse]:
        query_params = build_query_param(hard=hard, deleted_by=deleted_by)
        path_params = {
            "id": id,
        }

        return self.delete(
            "/api/v2/chat/messages/{id}",
            DeleteMessageResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def get_message(
        self, id: str, show_deleted_message: Optional[bool] = None
    ) -> StreamResponse[GetMessageResponse]:
        query_params = build_query_param(show_deleted_message=show_deleted_message)
        path_params = {
            "id": id,
        }

        return self.get(
            "/api/v2/chat/messages/{id}",
            GetMessageResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_message(
        self, id: str, message: MessageRequest, skip_enrich_url: Optional[bool] = None
    ) -> StreamResponse[UpdateMessageResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(message=message, skip_enrich_url=skip_enrich_url)

        return self.post(
            "/api/v2/chat/messages/{id}",
            UpdateMessageResponse,
            path_params=path_params,
            json=json,
        )

    def update_message_partial(
        self,
        id: str,
        skip_enrich_url: Optional[bool] = None,
        user_id: Optional[str] = None,
        unset: Optional[List[str]] = None,
        set: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UpdateMessagePartialResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(
            skip_enrich_url=skip_enrich_url,
            user_id=user_id,
            unset=unset,
            set=set,
            user=user,
        )

        return self.put(
            "/api/v2/chat/messages/{id}",
            UpdateMessagePartialResponse,
            path_params=path_params,
            json=json,
        )

    def run_message_action(
        self,
        id: str,
        form_data: Dict[str, str],
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(form_data=form_data, user_id=user_id, user=user)

        return self.post(
            "/api/v2/chat/messages/{id}/action",
            MessageResponse,
            path_params=path_params,
            json=json,
        )

    def commit_message(
        self,
        id: str,
    ) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict()

        return self.post(
            "/api/v2/chat/messages/{id}/commit",
            MessageResponse,
            path_params=path_params,
            json=json,
        )

    def send_reaction(
        self,
        id: str,
        reaction: ReactionRequest,
        enforce_unique: Optional[bool] = None,
        skip_push: Optional[bool] = None,
    ) -> StreamResponse[SendReactionResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(
            reaction=reaction, enforce_unique=enforce_unique, skip_push=skip_push
        )

        return self.post(
            "/api/v2/chat/messages/{id}/reaction",
            SendReactionResponse,
            path_params=path_params,
            json=json,
        )

    def delete_reaction(
        self, id: str, type: str, user_id: Optional[str] = None
    ) -> StreamResponse[ReactionRemovalResponse]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "id": id,
            "type": type,
        }

        return self.delete(
            "/api/v2/chat/messages/{id}/reaction/{type}",
            ReactionRemovalResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def get_reactions(
        self, id: str, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> StreamResponse[GetReactionsResponse]:
        query_params = build_query_param(limit=limit, offset=offset)
        path_params = {
            "id": id,
        }

        return self.get(
            "/api/v2/chat/messages/{id}/reactions",
            GetReactionsResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def query_reactions(
        self,
        id: str,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        user_id: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[QueryReactionsResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(
            limit=limit,
            next=next,
            prev=prev,
            user_id=user_id,
            sort=sort,
            filter=filter,
            user=user,
        )

        return self.post(
            "/api/v2/chat/messages/{id}/reactions",
            QueryReactionsResponse,
            path_params=path_params,
            json=json,
        )

    def translate_message(
        self, id: str, language: str
    ) -> StreamResponse[MessageResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(language=language)

        return self.post(
            "/api/v2/chat/messages/{id}/translate",
            MessageResponse,
            path_params=path_params,
            json=json,
        )

    def undelete_message(
        self, id: str, message: MessageRequest, skip_enrich_url: Optional[bool] = None
    ) -> StreamResponse[UpdateMessageResponse]:
        path_params = {
            "id": id,
        }
        json = build_body_dict(message=message, skip_enrich_url=skip_enrich_url)

        return self.post(
            "/api/v2/chat/messages/{id}/undelete",
            UpdateMessageResponse,
            path_params=path_params,
            json=json,
        )

    def cast_poll_vote(
        self,
        message_id: str,
        poll_id: str,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
        vote: Optional[VoteData] = None,
    ) -> StreamResponse[PollVoteResponse]:
        path_params = {
            "message_id": message_id,
            "poll_id": poll_id,
        }
        json = build_body_dict(user_id=user_id, user=user, vote=vote)

        return self.post(
            "/api/v2/chat/messages/{message_id}/polls/{poll_id}/vote",
            PollVoteResponse,
            path_params=path_params,
            json=json,
        )

    def remove_poll_vote(
        self, message_id: str, poll_id: str, vote_id: str, user_id: Optional[str] = None
    ) -> StreamResponse[PollVoteResponse]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "message_id": message_id,
            "poll_id": poll_id,
            "vote_id": vote_id,
        }

        return self.delete(
            "/api/v2/chat/messages/{message_id}/polls/{poll_id}/vote/{vote_id}",
            PollVoteResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def get_replies(
        self,
        parent_id: str,
        id_gte: Optional[str] = None,
        id_gt: Optional[str] = None,
        id_lte: Optional[str] = None,
        id_lt: Optional[str] = None,
        created_at_after_or_equal: Optional[datetime] = None,
        created_at_after: Optional[datetime] = None,
        created_at_before_or_equal: Optional[datetime] = None,
        created_at_before: Optional[datetime] = None,
        id_around: Optional[str] = None,
        created_at_around: Optional[datetime] = None,
    ) -> StreamResponse[GetRepliesResponse]:
        query_params = build_query_param(
            id_gte=id_gte,
            id_gt=id_gt,
            id_lte=id_lte,
            id_lt=id_lt,
            created_at_after_or_equal=created_at_after_or_equal,
            created_at_after=created_at_after,
            created_at_before_or_equal=created_at_before_or_equal,
            created_at_before=created_at_before,
            id_around=id_around,
            created_at_around=created_at_around,
        )
        path_params = {
            "parent_id": parent_id,
        }

        return self.get(
            "/api/v2/chat/messages/{parent_id}/replies",
            GetRepliesResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def unban(
        self,
        target_user_id: str,
        type: Optional[str] = None,
        id: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> StreamResponse[Response]:
        query_params = build_query_param(
            target_user_id=target_user_id, type=type, id=id, created_by=created_by
        )

        return self.delete(
            "/api/v2/chat/moderation/ban", Response, query_params=query_params
        )

    def ban(
        self,
        target_user_id: str,
        banned_by_id: Optional[str] = None,
        id: Optional[str] = None,
        ip_ban: Optional[bool] = None,
        reason: Optional[str] = None,
        shadow: Optional[bool] = None,
        timeout: Optional[int] = None,
        type: Optional[str] = None,
        user_id: Optional[str] = None,
        banned_by: Optional[UserRequest] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[Response]:
        json = build_body_dict(
            target_user_id=target_user_id,
            banned_by_id=banned_by_id,
            id=id,
            ip_ban=ip_ban,
            reason=reason,
            shadow=shadow,
            timeout=timeout,
            type=type,
            user_id=user_id,
            banned_by=banned_by,
            user=user,
        )

        return self.post("/api/v2/chat/moderation/ban", Response, json=json)

    def flag(
        self,
        reason: Optional[str] = None,
        target_message_id: Optional[str] = None,
        target_user_id: Optional[str] = None,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[FlagResponse]:
        json = build_body_dict(
            reason=reason,
            target_message_id=target_message_id,
            target_user_id=target_user_id,
            user_id=user_id,
            custom=custom,
            user=user,
        )

        return self.post("/api/v2/chat/moderation/flag", FlagResponse, json=json)

    def query_message_flags(
        self, payload: Optional[QueryMessageFlagsRequest] = None
    ) -> StreamResponse[QueryMessageFlagsResponse]:
        query_params = build_query_param(payload=payload)

        return self.get(
            "/api/v2/chat/moderation/flags/message",
            QueryMessageFlagsResponse,
            query_params=query_params,
        )

    def mute_user(
        self,
        timeout: int,
        user_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MuteUserResponse]:
        json = build_body_dict(
            timeout=timeout, user_id=user_id, target_ids=target_ids, user=user
        )

        return self.post("/api/v2/chat/moderation/mute", MuteUserResponse, json=json)

    def mute_channel(
        self,
        expiration: Optional[int] = None,
        user_id: Optional[str] = None,
        channel_cids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[MuteChannelResponse]:
        json = build_body_dict(
            expiration=expiration, user_id=user_id, channel_cids=channel_cids, user=user
        )

        return self.post(
            "/api/v2/chat/moderation/mute/channel", MuteChannelResponse, json=json
        )

    def unmute_user(
        self,
        timeout: int,
        user_id: Optional[str] = None,
        target_ids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UnmuteResponse]:
        json = build_body_dict(
            timeout=timeout, user_id=user_id, target_ids=target_ids, user=user
        )

        return self.post("/api/v2/chat/moderation/unmute", UnmuteResponse, json=json)

    def unmute_channel(
        self,
        expiration: Optional[int] = None,
        user_id: Optional[str] = None,
        channel_cids: Optional[List[str]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UnmuteResponse]:
        json = build_body_dict(
            expiration=expiration, user_id=user_id, channel_cids=channel_cids, user=user
        )

        return self.post(
            "/api/v2/chat/moderation/unmute/channel", UnmuteResponse, json=json
        )

    def create_poll(
        self,
        name: str,
        allow_answers: Optional[bool] = None,
        allow_user_suggested_options: Optional[bool] = None,
        description: Optional[str] = None,
        enforce_unique_vote: Optional[bool] = None,
        id: Optional[str] = None,
        is_closed: Optional[bool] = None,
        max_votes_allowed: Optional[int] = None,
        user_id: Optional[str] = None,
        voting_visibility: Optional[str] = None,
        options: Optional[List[Optional[PollOptionInput]]] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[PollResponse]:
        json = build_body_dict(
            name=name,
            allow_answers=allow_answers,
            allow_user_suggested_options=allow_user_suggested_options,
            description=description,
            enforce_unique_vote=enforce_unique_vote,
            id=id,
            is_closed=is_closed,
            max_votes_allowed=max_votes_allowed,
            user_id=user_id,
            voting_visibility=voting_visibility,
            options=options,
            custom=custom,
            user=user,
        )

        return self.post("/api/v2/chat/polls", PollResponse, json=json)

    def update_poll(
        self,
        id: str,
        name: str,
        allow_answers: Optional[bool] = None,
        allow_user_suggested_options: Optional[bool] = None,
        description: Optional[str] = None,
        enforce_unique_vote: Optional[bool] = None,
        is_closed: Optional[bool] = None,
        max_votes_allowed: Optional[int] = None,
        user_id: Optional[str] = None,
        voting_visibility: Optional[str] = None,
        options: Optional[List[Optional[PollOption]]] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[PollResponse]:
        json = build_body_dict(
            id=id,
            name=name,
            allow_answers=allow_answers,
            allow_user_suggested_options=allow_user_suggested_options,
            description=description,
            enforce_unique_vote=enforce_unique_vote,
            is_closed=is_closed,
            max_votes_allowed=max_votes_allowed,
            user_id=user_id,
            voting_visibility=voting_visibility,
            options=options,
            custom=custom,
            user=user,
        )

        return self.put("/api/v2/chat/polls", PollResponse, json=json)

    def query_polls(
        self,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[QueryPollsResponse]:
        query_params = build_query_param(user_id=user_id)
        json = build_body_dict(
            limit=limit, next=next, prev=prev, sort=sort, filter=filter
        )

        return self.post(
            "/api/v2/chat/polls/query",
            QueryPollsResponse,
            query_params=query_params,
            json=json,
        )

    def delete_poll(
        self, poll_id: str, user_id: Optional[str] = None
    ) -> StreamResponse[Response]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "poll_id": poll_id,
        }

        return self.delete(
            "/api/v2/chat/polls/{poll_id}",
            Response,
            query_params=query_params,
            path_params=path_params,
        )

    def get_poll(
        self, poll_id: str, user_id: Optional[str] = None
    ) -> StreamResponse[PollResponse]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "poll_id": poll_id,
        }

        return self.get(
            "/api/v2/chat/polls/{poll_id}",
            PollResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_poll_partial(
        self,
        poll_id: str,
        user_id: Optional[str] = None,
        unset: Optional[List[str]] = None,
        set: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[PollResponse]:
        path_params = {
            "poll_id": poll_id,
        }
        json = build_body_dict(user_id=user_id, unset=unset, set=set, user=user)

        return self.patch(
            "/api/v2/chat/polls/{poll_id}",
            PollResponse,
            path_params=path_params,
            json=json,
        )

    def create_poll_option(
        self,
        poll_id: str,
        text: str,
        position: Optional[int] = None,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[PollOptionResponse]:
        path_params = {
            "poll_id": poll_id,
        }
        json = build_body_dict(
            text=text, position=position, user_id=user_id, custom=custom, user=user
        )

        return self.post(
            "/api/v2/chat/polls/{poll_id}/options",
            PollOptionResponse,
            path_params=path_params,
            json=json,
        )

    def update_poll_option(
        self,
        poll_id: str,
        id: str,
        text: str,
        user_id: Optional[str] = None,
        custom: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[PollOptionResponse]:
        path_params = {
            "poll_id": poll_id,
        }
        json = build_body_dict(
            id=id, text=text, user_id=user_id, custom=custom, user=user
        )

        return self.put(
            "/api/v2/chat/polls/{poll_id}/options",
            PollOptionResponse,
            path_params=path_params,
            json=json,
        )

    def delete_poll_option(
        self, poll_id: str, option_id: str, user_id: Optional[str] = None
    ) -> StreamResponse[Response]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "poll_id": poll_id,
            "option_id": option_id,
        }

        return self.delete(
            "/api/v2/chat/polls/{poll_id}/options/{option_id}",
            Response,
            query_params=query_params,
            path_params=path_params,
        )

    def get_poll_option(
        self, poll_id: str, option_id: str, user_id: Optional[str] = None
    ) -> StreamResponse[PollOptionResponse]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "poll_id": poll_id,
            "option_id": option_id,
        }

        return self.get(
            "/api/v2/chat/polls/{poll_id}/options/{option_id}",
            PollOptionResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def query_poll_votes(
        self,
        poll_id: str,
        user_id: Optional[str] = None,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        prev: Optional[str] = None,
        sort: Optional[List[Optional[SortParam]]] = None,
        filter: Optional[Dict[str, object]] = None,
    ) -> StreamResponse[PollVotesResponse]:
        query_params = build_query_param(user_id=user_id)
        path_params = {
            "poll_id": poll_id,
        }
        json = build_body_dict(
            limit=limit, next=next, prev=prev, sort=sort, filter=filter
        )

        return self.post(
            "/api/v2/chat/polls/{poll_id}/votes",
            PollVotesResponse,
            query_params=query_params,
            path_params=path_params,
            json=json,
        )

    def query_banned_users(
        self, payload: Optional[QueryBannedUsersRequest] = None
    ) -> StreamResponse[QueryBannedUsersResponse]:
        query_params = build_query_param(payload=payload)

        return self.get(
            "/api/v2/chat/query_banned_users",
            QueryBannedUsersResponse,
            query_params=query_params,
        )

    def search(
        self, payload: Optional[SearchRequest] = None
    ) -> StreamResponse[SearchResponse]:
        query_params = build_query_param(payload=payload)

        return self.get(
            "/api/v2/chat/search", SearchResponse, query_params=query_params
        )

    def query_threads(
        self,
        limit: Optional[int] = None,
        next: Optional[str] = None,
        participant_limit: Optional[int] = None,
        prev: Optional[str] = None,
        reply_limit: Optional[int] = None,
        user_id: Optional[str] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[QueryThreadsResponse]:
        json = build_body_dict(
            limit=limit,
            next=next,
            participant_limit=participant_limit,
            prev=prev,
            reply_limit=reply_limit,
            user_id=user_id,
            user=user,
        )

        return self.post("/api/v2/chat/threads", QueryThreadsResponse, json=json)

    def get_thread(
        self,
        message_id: str,
        connection_id: Optional[str] = None,
        reply_limit: Optional[int] = None,
        participant_limit: Optional[int] = None,
    ) -> StreamResponse[GetThreadResponse]:
        query_params = build_query_param(
            connection_id=connection_id,
            reply_limit=reply_limit,
            participant_limit=participant_limit,
        )
        path_params = {
            "message_id": message_id,
        }

        return self.get(
            "/api/v2/chat/threads/{message_id}",
            GetThreadResponse,
            query_params=query_params,
            path_params=path_params,
        )

    def update_thread_partial(
        self,
        message_id: str,
        user_id: Optional[str] = None,
        unset: Optional[List[str]] = None,
        set: Optional[Dict[str, object]] = None,
        user: Optional[UserRequest] = None,
    ) -> StreamResponse[UpdateThreadPartialResponse]:
        path_params = {
            "message_id": message_id,
        }
        json = build_body_dict(user_id=user_id, unset=unset, set=set, user=user)

        return self.patch(
            "/api/v2/chat/threads/{message_id}",
            UpdateThreadPartialResponse,
            path_params=path_params,
            json=json,
        )

    def unread_counts(self) -> StreamResponse[WrappedUnreadCountsResponse]:
        return self.get("/api/v2/chat/unread", WrappedUnreadCountsResponse)

    def unread_counts_batch(
        self, user_ids: List[str]
    ) -> StreamResponse[UnreadCountsBatchResponse]:
        json = build_body_dict(user_ids=user_ids)

        return self.post(
            "/api/v2/chat/unread_batch", UnreadCountsBatchResponse, json=json
        )

    def send_user_custom_event(
        self, user_id: str, event: UserCustomEventRequest
    ) -> StreamResponse[Response]:
        path_params = {
            "user_id": user_id,
        }
        json = build_body_dict(event=event)

        return self.post(
            "/api/v2/chat/users/{user_id}/event",
            Response,
            path_params=path_params,
            json=json,
        )
