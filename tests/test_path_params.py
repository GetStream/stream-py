import pytest

from getstream.base import build_path


def test_build_path_encodes_reserved_chars_without_mutating_input():
    params = {"type": "default", "id": "call 1/2?a=b#c"}
    first = build_path("/api/v2/video/call/{type}/{id}", params)
    second = build_path("/api/v2/video/call/{type}/{id}", params)

    assert first == "/api/v2/video/call/default/call%201%2F2%3Fa%3Db%23c"
    assert second == first
    assert params["id"] == "call 1/2?a=b#c"


@pytest.mark.parametrize("bad_value", ["", ".", "..", None])
def test_build_path_rejects_empty_and_dot_segments(bad_value):
    with pytest.raises(ValueError, match="Invalid path parameter 'id'"):
        build_path(
            "/api/v2/video/call/{type}/{id}", {"type": "default", "id": bad_value}
        )
