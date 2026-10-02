from getstream import _rust
from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


class TestEvents:
    def test_call_ended_made_in_python_has_no_reason(self):
        event = _rust.CallEnded()

        assert event.name == "call_ended"
        assert event.reason == models_pb2.CALL_ENDED_REASON_UNSPECIFIED
