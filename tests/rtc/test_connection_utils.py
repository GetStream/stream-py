import pytest

from getstream.video.rtc.connection_utils import create_join_request


@pytest.mark.asyncio
async def test_create_join_request_generates_valid_sdps():
    token = "test-token"
    session_id = "session-123"

    join_request = await create_join_request(token, session_id)

    # Validate basic fields
    assert join_request.token == token
    assert join_request.session_id == session_id

    # SDPs should be non-empty strings
    assert isinstance(join_request.publisher_sdp, str) and join_request.publisher_sdp
    assert isinstance(join_request.subscriber_sdp, str) and join_request.subscriber_sdp

    # SDP should start with version line
    assert join_request.publisher_sdp.startswith("v=0")
    assert join_request.subscriber_sdp.startswith("v=0")

    # Expect audio and video media descriptions present
    assert "m=audio" in join_request.publisher_sdp
    assert "m=video" in join_request.publisher_sdp
    assert "m=audio" in join_request.subscriber_sdp
    assert "m=video" in join_request.subscriber_sdp


