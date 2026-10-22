import getstream_rtc

from getstream.video.rtc.pb.stream.video.sfu.models import models_pb2


class TestEnums:
    def test_a_track_type_is_the_dict_key_of_its_int(self) -> None:
        names = {getstream_rtc.TrackType.AUDIO: "audio"}

        assert names[models_pb2.TRACK_TYPE_AUDIO] == "audio"

    def test_a_calling_state_is_the_dict_key_of_its_int(self) -> None:
        names = {getstream_rtc.CallingState.JOINED: "joined"}

        assert names[int(getstream_rtc.CallingState.JOINED)] == "joined"
