import datetime

import pytest

from getstream import Stream
from getstream.chat.channel import Channel
from getstream.exceptions import StreamApiException
from getstream.models import MessageRequest, ScheduledMessagesFilter


pytestmark = pytest.mark.integration

# Error code the API returns when scheduled messages are off for the app.
SCHEDULED_MESSAGES_DISABLED = 114


def in_one_hour() -> datetime.datetime:
    # Millisecond precision, so it survives the round trip through the API.
    now = datetime.datetime.now(datetime.timezone.utc)
    return (now + datetime.timedelta(hours=1)).replace(
        microsecond=now.microsecond // 1000 * 1000
    )


def channel_cid(channel: Channel) -> str:
    return f"{channel.channel_type}:{channel.channel_id}"


def schedule_message(channel: Channel, user_id: str, text: str) -> str:
    """Schedule a message an hour ahead and return its scheduled message ID.

    Skips the test when the app cannot schedule: the feature is opt-in per
    app, and backends without it ignore scheduled_at and send right away.
    """
    try:
        response = channel.send_message(
            message=MessageRequest(text=text, user_id=user_id),
            scheduled_at=in_one_hour(),
        )
    except StreamApiException as e:
        if e.code == SCHEDULED_MESSAGES_DISABLED:
            pytest.skip("Scheduled messages are not enabled for this app")
        raise
    if response.data.scheduled_message is None:
        pytest.skip("This backend does not support scheduled messages")
    return response.data.scheduled_message.id


class TestScheduledMessages:
    def test_schedule_and_query(self, client: Stream, channel: Channel, random_user):
        scheduled_id = schedule_message(channel, random_user.id, "scheduled hello")

        response = client.chat.query_scheduled_messages(
            user_id=random_user.id,
            filter=ScheduledMessagesFilter(cid=channel_cid(channel)),
        )

        assert [m.id for m in response.data.scheduled_messages] == [scheduled_id]
        scheduled = response.data.scheduled_messages[0]
        assert scheduled.status == "scheduled"
        assert scheduled.cid == channel_cid(channel)
        assert scheduled.message.text == "scheduled hello"
        assert isinstance(scheduled.scheduled_at, datetime.datetime)

    def test_update(self, client: Stream, channel: Channel, random_user):
        scheduled_id = schedule_message(channel, random_user.id, "scheduled hello")
        scheduled_at = in_one_hour()

        response = client.chat.update_scheduled_message(
            id=scheduled_id,
            scheduled_at=scheduled_at,
            message=MessageRequest(text="rescheduled hello"),
        )

        assert response.data.scheduled_message.message.text == "rescheduled hello"
        assert response.data.scheduled_message.scheduled_at == scheduled_at

    def test_send_now(self, client: Stream, channel: Channel, random_user):
        scheduled_id = schedule_message(channel, random_user.id, "scheduled hello")

        response = client.chat.send_scheduled_message_now(id=scheduled_id)

        assert response.data.scheduled_message.id == scheduled_id

    def test_delete(self, client: Stream, channel: Channel, random_user):
        scheduled_id = schedule_message(channel, random_user.id, "scheduled hello")

        response = client.chat.delete_scheduled_message(id=scheduled_id)

        assert response.data.scheduled_message.id == scheduled_id
        assert response.data.scheduled_message.status == "canceled"
        query = client.chat.query_scheduled_messages(
            user_id=random_user.id,
            filter=ScheduledMessagesFilter(cid=channel_cid(channel)),
        )
        assert scheduled_id not in [m.id for m in query.data.scheduled_messages]
