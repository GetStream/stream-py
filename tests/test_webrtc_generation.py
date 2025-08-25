from getstream.video.rtc.pb.stream.video.sfu.models.models_pb2 import (
    TrackInfo,
    TrackType,
)
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_pb2 import (
    SetPublisherRequest,
    SetPublisherResponse,
)
from getstream.video.rtc.pb.stream.video.sfu.signal_rpc.signal_twirp import (
    SignalServerClient,
    SignalServerServer,
)


class MockSignalService:
    """Mock implementation of the SignalServer service for testing."""

    def SetPublisher(self, ctx, request):
        return SetPublisherResponse()

    def SendAnswer(self, ctx, request):
        return None

    def IceTrickle(self, ctx, request):
        return None

    def UpdateSubscriptions(self, ctx, request):
        return None

    def UpdateMuteStates(self, ctx, request):
        return None

    def IceRestart(self, ctx, request):
        return None

    def SendStats(self, ctx, request):
        return None

    def StartNoiseCancellation(self, ctx, request):
        return None

    def StopNoiseCancellation(self, ctx, request):
        return None


def test_webrtc_models_exist():
    """Test that the generated models exist and can be instantiated."""
    # Test basic model creation
    track_info = TrackInfo()
    assert track_info is not None

    # Test enum values
    assert TrackType.TRACK_TYPE_AUDIO == 1
    assert TrackType.TRACK_TYPE_VIDEO == 2


def test_webrtc_signal_service_exists():
    """Test that the generated Signal service exists and has the expected methods."""
    # Test that both server and client classes exist
    server = SignalServerServer(service=MockSignalService())
    client = SignalServerClient(address="http://localhost:8080")
    assert server is not None
    assert client is not None

    # Test that key methods exist on the client
    assert hasattr(client, "SetPublisher")
    assert hasattr(client, "SendAnswer")
    assert hasattr(client, "IceTrickle")
    assert hasattr(client, "UpdateSubscriptions")


def test_webrtc_message_types_exist():
    """Test that the generated message types exist and can be instantiated."""
    # Test request/response types
    set_publisher_req = SetPublisherRequest()
    set_publisher_resp = SetPublisherResponse()
    assert set_publisher_req is not None
    assert set_publisher_resp is not None

    # Test that fields can be set
    set_publisher_req.session_id = "test-session"
    set_publisher_req.sdp = "test-sdp"
    assert set_publisher_req.session_id == "test-session"
    assert set_publisher_req.sdp == "test-sdp"
