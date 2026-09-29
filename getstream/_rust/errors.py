class RustError(Exception):
    """Base class of the errors that ``getstream._rust`` raises."""


class RtcError(RustError):
    """An RTC operation of the Rust SDK failed."""
