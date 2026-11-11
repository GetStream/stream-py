# Migration Guide: v7 → v8

v8 regenerates the client from the current Stream API. Most of the changes add new methods, models and optional parameters. This guide lists the changes that can break code written for stream-py 7.1.0.

```bash
pip install "getstream==8.*"
```

## Pass optional parameters by keyword

Generated method parameters are positional-or-keyword, and v8 adds new optional parameters in the middle of many signatures. A call that passes optional arguments by position can now send a value to the wrong parameter. Calls that pass them by keyword work unchanged.

```python
# v7: the fourth positional argument was `user_id`
client.feeds.get_activity(activity_id, "first", 10, "jane")

# v8: "jane" would go to the new `skip_own_followings`, so pass it by keyword
client.feeds.get_activity(activity_id, comment_sort="first", comment_limit=10, user_id="jane")
```

These methods have new parameters before existing ones. Each async client has the same changes.

| Method | New parameters | First moved parameter |
|---|---|---|
| `Channel.get_or_create`, `chat.get_or_create_channel`, `chat.get_or_create_distinct_channel` | `include_scheduled_messages` | `state` |
| `Channel.send_message`, `chat.send_message` | `scheduled_at` | `skip_enrich_url` |
| `chat.query_channels` | `include_active_member_count` | `limit` |
| `chat.grouped_query_channels` | `sort` | `groups` |
| `chat.channel_batch_update` | `synchronous` | `custom_unset` |
| `chat.create_channel_type` | `quotes`, `reminders`, `automod_thresholds` | `reactions` |
| `chat.create_reminder`, `chat.update_reminder` | `expires_at` | `remind_at` |
| `chat.cast_poll_vote`, `feeds.cast_poll_vote` | `config_key`, `config_team` | `user_id` |
| `create_poll` | `config_key`, `config_team`, `team` | `description` |
| `update_poll` | `config_key`, `config_team` | `description` |
| `update_poll_partial`, `create_poll_option`, `update_poll_option` | `config_key`, `config_team` | `user_id` |
| `update_app` | `two_way_block_effect_enabled` | `user_response_time_enabled` |
| `Feed.get_or_create`, `feeds.get_or_create_feed` | `discard_actors` | `data` |
| `Feed.query_pinned_activities`, `feeds.query_pinned_activities` | `include_expired_activities`, `include_moderated_activities`, `include_soft_deleted_activities`, `user_id` | `limit` |
| `feeds.add_activity` | `skip_existing` | `skip_push` |
| `feeds.get_activity` | `skip_own_followings` | `user_id` |
| `feeds.query_activities` | `include_moderated_activities` | `include_private_activities` |
| `feeds.query_comments` | `include_soft_deleted_comments` | `limit` |
| `feeds.query_follows` | `include_group_counts` | `limit` |
| `feeds.follow_batch`, `feeds.get_or_create_follows` | `_async` | `create_users` |
| `feeds.unfollow_batch`, `feeds.get_or_create_unfollows` | `_async` | `delete_notification_activity` |
| `moderation.analyze` | `country_code`, `country_codes` | `entity_creator_id` |
| `moderation.check` | `country_code`, `country_codes` | `test_mode` |
| `moderation.appeal` | `channel_cid` | `review_queue_item_id` |
| `moderation.ban` | `ban_from_future_channels`, `delete_reactions` | `banned_by_id` |
| `moderation.unban` | `remove_future_channels_ban` | `unbanned_by_id` |
| `moderation.submit_action` | `delete_poll`, `delete_poll_answer`, `delete_poll_option` | `delete_reaction` |
| `moderation.upsert_config` | `engine`, `intent_config` | `flood_config` |

## Parameters that are now optional

These parameters are now optional, so they moved behind the required ones. Pass them by keyword.

- `chat.update_channel_type`: `automod`, `automod_behavior` and `max_message_length`. `max_message_length` now comes after `mark_messages_pending`.
- `moderation.submit_moderation_feedback`: `message`, `published_at` and `reference`. They now come after the new `confidence`, `entity_creator_id`, `entity_id`, `entity_type`, `false_positive`, `feedback_type`, `review_queue_item_id` and `user_id` parameters.

The matching request models, `UpdateChannelTypeRequest` and `SubmitModerationFeedbackRequest`, give these fields a `None` default, so they also moved in the dataclass field order.

## Campaign responses

`update_campaign` returns `UpdateCampaignResponse` and `stop_campaign` returns `StopCampaignResponse`. v7 decoded both into `CampaignResponse`, whose fields came back as `None` because the API returns the campaign inside a `campaign` field. Read the campaign from that field.

```python
# v7
resp = client.chat.stop_campaign(id=campaign_id)
status = resp.data.status  # None

# v8
resp = client.chat.stop_campaign(id=campaign_id)
status = resp.data.campaign.status
```

## Removed models

These request models had no fields, because their endpoints take no request body. The methods that call those endpoints keep their signatures.

- `CancelImportV2TaskRequest`
- `CommitMessageRequest`
- `EndCallRequest`
- `ExportFeedUserDataRequest`
- `RestoreFeedGroupRequest`
- `StartHLSBroadcastingRequest`
- `StartPolicyTestRunRequest`
- `StopAllRTMPBroadcastsRequest`
- `StopCampaignRequest`
- `StopFrameRecordingRequest`
- `StopHLSBroadcastingRequest`
- `VideoEndCallRequestPayload`
- `VideoKickUserRequestPayload`

`Time` was also removed. `EnrichedReaction.created_at` and `EnrichedReaction.updated_at` are now `Optional[str]`.

## Removed field

`AIVideoConfig.provider` was removed. Drop it from `AIVideoConfig(...)` calls in your moderation config.

## Type annotation changes

These changes affect only type checkers. Runtime values are unchanged.

- `own_capabilities` on call, channel and feed responses is annotated as `List[str]`. The constants classes `OwnCapability`, `ChannelOwnCapability` and `FeedOwnCapability` still exist, and their values are strings.
- `ChannelMemberResponse.user_id` and `OwnUserResponse.blocked_user_ids` are no longer `Optional`.
- `CampaignResponse.sender_mode` and `CampaignResponse.sender_visibility` are now `Optional[str]`.

## Uploads

`upload_file`, `upload_image`, `upload_channel_file` and `upload_channel_image` keep their signatures and still send `multipart/form-data`. `file` is a keyword with a `None` default in the signature, but the upload raises `ValueError` without it.
