import uuid

from getstream import Stream
from getstream.models import (
    ChannelInput,
    ChannelMemberRequest,
    MessageRequest,
    PollOptionInput,
    VoteData,
)


def test_create_get_update_delete_poll(client: Stream, random_user):
    """Create, get, update, and delete a poll."""
    poll_name = f"Favorite color {uuid.uuid4().hex[:8]}"
    response = client.create_poll(
        name=poll_name,
        description="Pick your favorite color",
        enforce_unique_vote=True,
        user_id=random_user.id,
        options=[
            PollOptionInput(text="Red"),
            PollOptionInput(text="Blue"),
            PollOptionInput(text="Green"),
        ],
    )
    poll_id = response.data.poll.id
    assert poll_id is not None
    assert response.data.poll.name == poll_name
    assert response.data.poll.enforce_unique_vote is True
    assert len(response.data.poll.options) == 3

    # get
    get_resp = client.get_poll(poll_id=poll_id)
    assert get_resp.data.poll.id == poll_id
    assert get_resp.data.poll.name == poll_name

    # update
    updated_name = f"Updated: {poll_name}"
    update_resp = client.update_poll(
        id=poll_id,
        name=updated_name,
        description="Updated description",
        user_id=random_user.id,
    )
    assert update_resp.data.poll.name == updated_name

    # delete
    client.delete_poll(poll_id=poll_id, user_id=random_user.id)


def test_query_polls(client: Stream, random_user):
    """Query polls."""
    poll_name = f"Query test poll {uuid.uuid4().hex[:8]}"
    response = client.create_poll(
        name=poll_name,
        user_id=random_user.id,
        options=[
            PollOptionInput(text="Option A"),
            PollOptionInput(text="Option B"),
        ],
    )
    poll_id = response.data.poll.id

    q_resp = client.query_polls(
        user_id=random_user.id,
        filter={"id": poll_id},
    )
    assert q_resp.data.polls is not None
    assert len(q_resp.data.polls) >= 1
    assert q_resp.data.polls[0].id == poll_id

    # cleanup
    client.delete_poll(poll_id=poll_id, user_id=random_user.id)


def test_cast_poll_vote(client: Stream, random_users):
    """Cast a poll vote."""
    creator = random_users[0]
    voter = random_users[1]

    response = client.create_poll(
        name=f"Vote test {uuid.uuid4().hex[:8]}",
        enforce_unique_vote=True,
        user_id=creator.id,
        options=[
            PollOptionInput(text="Yes"),
            PollOptionInput(text="No"),
        ],
    )
    poll_id = response.data.poll.id
    option_id = response.data.poll.options[0].id

    # create channel and send message with poll
    channel_id = str(uuid.uuid4())
    ch = client.chat.channel("messaging", channel_id)
    ch.get_or_create(
        data=ChannelInput(
            created_by_id=creator.id,
            members=[
                ChannelMemberRequest(user_id=creator.id),
                ChannelMemberRequest(user_id=voter.id),
            ],
        )
    )

    try:
        send_resp = ch.send_message(
            message=MessageRequest(
                text="Please vote!",
                user_id=creator.id,
                poll_id=poll_id,
            )
        )
    except Exception as e:
        if "polls not enabled" in str(e).lower():
            import pytest

            pytest.skip("Polls not enabled for this channel type")
        raise
    msg_id = send_resp.data.message.id

    # cast vote
    vote_resp = client.chat.cast_poll_vote(
        message_id=msg_id,
        poll_id=poll_id,
        user_id=voter.id,
        vote=VoteData(option_id=option_id),
    )
    assert vote_resp.data.vote is not None
    assert vote_resp.data.vote.option_id == option_id

    # verify vote count
    get_resp = client.get_poll(poll_id=poll_id)
    assert get_resp.data.poll.vote_count == 1

    # cleanup
    try:
        client.chat.delete_channels(cids=[f"messaging:{channel_id}"], hard_delete=True)
    except Exception:
        pass
    client.delete_poll(poll_id=poll_id, user_id=creator.id)
