from abc import ABC

from getstream import Stream
from getstream.video.call import Call


class VideoTestClass(ABC):
    """
    Abstract base class for video tests that need to share the same call and client objects using pytest fixture
    """

    client: Stream
    call: Call
