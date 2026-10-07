class RustError(Exception):
    """Base class of the errors that ``getstream_rtc`` raises."""


class ConfigError(RustError):
    """The client configuration is invalid."""


class RtcError(RustError):
    """An RTC operation of the Rust SDK failed."""


class ApiError(RtcError):
    """The Stream API returned an error response. ``message`` is the message
    of the API; ``str(error)`` also contains the code and the HTTP status."""

    def __init__(
        self,
        text: str,
        code: int,
        status_code: int,
        message: str,
        unrecoverable: bool,
    ):
        super().__init__(text)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.unrecoverable = unrecoverable


class CoordinatorError(RtcError):
    """A coordinator step of the join failed, for example the coordinator
    rejected the credentials."""


class IllegalStateError(RtcError):
    """The operation is not valid in the current state of the call or track."""


class MediaError(RtcError):
    """Encoding, decoding or packetizing media failed, or a frame is invalid."""


class PermissionDeniedError(RtcError):
    """The participant lacks ``capability`` (for example ``send-audio``), which
    the operation requires."""

    def __init__(self, message: str, capability: str):
        super().__init__(message)
        self.capability = capability


class PcmQueueOverflowError(RtcError):
    """A PCM write exceeded the queue capacity. The newest samples were kept
    and ``dropped_samples`` oldest samples were discarded."""

    def __init__(self, message: str, dropped_samples: int, capacity_samples: int):
        super().__init__(message)
        self.dropped_samples = dropped_samples
        self.capacity_samples = capacity_samples
