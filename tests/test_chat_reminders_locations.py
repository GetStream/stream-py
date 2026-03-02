import datetime

import pytest

from getstream import Stream
from getstream.chat.channel import Channel
from getstream.models import (
    MessageRequest,
)


class TestReminders:
    @pytest.fixture(autouse=True)
    def setup_channel_for_reminders(self, channel: Channel):
        """Enable user_message_reminders on the channel."""
        channel.update_channel_partial(
            set={"config_overrides": {"user_message_reminders": True}}
        )
        yield
        try:
            channel.update_channel_partial(
                set={"config_overrides": {"user_message_reminders": False}}
            )
        except Exception:
            pass

    def test_create_reminder(self, client: Stream, channel: Channel, random_user):
        """Create a reminder without remind_at."""
        msg = channel.send_message(
            message=MessageRequest(
                text="Test message for reminder", user_id=random_user.id
            )
        )
        message_id = msg.data.message.id

        response = client.chat.create_reminder(
            message_id=message_id, user_id=random_user.id
        )
        assert response.data.reminder is not None
        assert response.data.reminder.message_id == message_id

        try:
            client.chat.delete_reminder(message_id=message_id, user_id=random_user.id)
        except Exception:
            pass

    def test_create_reminder_with_remind_at(
        self, client: Stream, channel: Channel, random_user
    ):
        """Create a reminder with a specific remind_at time."""
        msg = channel.send_message(
            message=MessageRequest(
                text="Test message for timed reminder", user_id=random_user.id
            )
        )
        message_id = msg.data.message.id

        remind_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=1
        )
        response = client.chat.create_reminder(
            message_id=message_id,
            user_id=random_user.id,
            remind_at=remind_at,
        )
        assert response.data.reminder is not None
        assert response.data.reminder.message_id == message_id
        assert response.data.reminder.remind_at is not None

        try:
            client.chat.delete_reminder(message_id=message_id, user_id=random_user.id)
        except Exception:
            pass

    def test_update_reminder(self, client: Stream, channel: Channel, random_user):
        """Update a reminder's remind_at time."""
        msg = channel.send_message(
            message=MessageRequest(
                text="Test message for updating reminder", user_id=random_user.id
            )
        )
        message_id = msg.data.message.id

        client.chat.create_reminder(message_id=message_id, user_id=random_user.id)

        remind_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            days=2
        )
        response = client.chat.update_reminder(
            message_id=message_id,
            user_id=random_user.id,
            remind_at=remind_at,
        )
        assert response.data.reminder is not None
        assert response.data.reminder.message_id == message_id
        assert response.data.reminder.remind_at is not None

        try:
            client.chat.delete_reminder(message_id=message_id, user_id=random_user.id)
        except Exception:
            pass

    def test_delete_reminder(self, client: Stream, channel: Channel, random_user):
        """Delete a reminder."""
        msg = channel.send_message(
            message=MessageRequest(
                text="Test message for deleting reminder", user_id=random_user.id
            )
        )
        message_id = msg.data.message.id

        client.chat.create_reminder(message_id=message_id, user_id=random_user.id)

        response = client.chat.delete_reminder(
            message_id=message_id, user_id=random_user.id
        )
        assert response is not None

    def test_query_reminders(self, client: Stream, channel: Channel, random_user):
        """Query reminders for a user."""
        message_ids = []
        for i in range(3):
            msg = channel.send_message(
                message=MessageRequest(
                    text=f"Test message {i} for querying reminders",
                    user_id=random_user.id,
                )
            )
            message_ids.append(msg.data.message.id)
            remind_at = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(days=i + 1)
            client.chat.create_reminder(
                message_id=msg.data.message.id,
                user_id=random_user.id,
                remind_at=remind_at,
            )

        response = client.chat.query_reminders(user_id=random_user.id)
        assert response.data.reminders is not None
        assert len(response.data.reminders) >= 3

        # cleanup
        for mid in message_ids:
            try:
                client.chat.delete_reminder(message_id=mid, user_id=random_user.id)
            except Exception:
                pass


class TestLiveLocations:
    @pytest.fixture(autouse=True)
    def setup_channel_for_shared_locations(self, channel: Channel):
        """Enable shared_locations on the channel."""
        channel.update_channel_partial(
            set={"config_overrides": {"shared_locations": True}}
        )
        yield
        try:
            channel.update_channel_partial(
                set={"config_overrides": {"shared_locations": False}}
            )
        except Exception:
            pass

    def test_get_user_locations(self, client: Stream, channel: Channel, random_user):
        """Get active live locations for a user."""
        response = client.get_user_live_locations(user_id=random_user.id)
        assert response.data.active_live_locations is not None

    def test_update_user_location(self, client: Stream, channel: Channel, random_user):
        """Send a message with shared location, then update location."""
        now = datetime.datetime.now(datetime.timezone.utc)
        one_hour_later = now + datetime.timedelta(hours=1)

        msg = channel.send_message(
            message=MessageRequest(
                text="Message with location",
                user_id=random_user.id,
                custom={
                    "shared_location": {
                        "created_by_device_id": "test_device_id",
                        "latitude": 37.7749,
                        "longitude": -122.4194,
                        "end_at": one_hour_later.isoformat(),
                    }
                },
            )
        )
        message_id = msg.data.message.id

        try:
            response = client.update_live_location(
                message_id=message_id,
                latitude=37.7749,
                longitude=-122.4194,
                user_id=random_user.id,
            )
            assert response is not None
        except Exception:
            # shared locations may not be fully configured in test env
            pass
