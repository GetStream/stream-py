from getstream.models import ActivityMarksConfig, CreateFeedGroupRequest, RankingConfig


def test_create_feed_group_serializes_activity_marks_ranking_is_seen():
    request = CreateFeedGroupRequest(
        id="timeline",
        activity_marks=ActivityMarksConfig(track_seen=True, track_read=True),
        ranking=RankingConfig(type="expression", score="is_seen ? 0 : 100"),
    )

    payload = request.to_dict()

    assert payload["activity_marks"]["track_seen"] is True
    assert payload["activity_marks"]["track_read"] is True
    assert payload["ranking"]["type"] == "expression"
    assert payload["ranking"]["score"] == "is_seen ? 0 : 100"
